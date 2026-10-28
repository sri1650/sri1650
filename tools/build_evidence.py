#!/usr/bin/env python3
"""Create traceable numerical reports and plots from the actual offline simulations."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import csv
import subprocess
import hashlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from servo_lab.parameters import load_config,motor_sizing
from servo_lab.runner import run_simulation,run_campaign,Scenario
from servo_lab.robustness import screen,write_rows
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def figure(title,xlabel,ylabel,curves,out):
    fig,ax=plt.subplots(figsize=(8.5,4.4),dpi=135)
    for x,y,label in curves:
        ax.plot(x,y,label=label)
    ax.set(title=title,xlabel=xlabel,ylabel=ylabel)
    ax.grid(True,alpha=.25)
    if len(curves)>1:ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--samples",type=int,default=100)
    parser.add_argument("--seed",type=int,default=2026)
    parser.add_argument("--out",type=Path,default=ROOT/"outputs")
    args=parser.parse_args()
    output=args.out
    output.mkdir(parents=True,exist_ok=True)
    plots=output/"plots";plots.mkdir(exist_ok=True)
    cfg=load_config()
    nominal=run_simulation(cfg)
    disturbance=run_simulation(cfg,Scenario("load_step",disturbance_force_n=6))
    nominal.to_csv(output/"nominal_axis_trace.csv")
    disturbance.to_csv(output/"disturbance_axis_trace.csv")
    faults=run_campaign(cfg)
    robustness=screen(n=args.samples,seed=args.seed,cfg=cfg)
    write_rows(robustness,output/"assumed_parameter_sweep.csv")
    t=[r["t_s"] for r in nominal.trajectory]
    figure("100 mm commanded move — reference versus simulation","Time (s)","Axis position (mm)",
           [(t,[r["reference_m"]*1000 for r in nominal.trajectory],"Quintic reference"),
            (t,[r["position_m"]*1000 for r in nominal.trajectory],"Simulated position")],plots/"tracking_position.png")
    figure("Position tracking error under assumed load","Time (s)","Tracking error (mm)",
           [(t,[r["tracking_error_m"]*1000 for r in nominal.trajectory],"Nominal"),
            (t,[r["tracking_error_m"]*1000 for r in disturbance.trajectory],"6 N disturbance")],plots/"tracking_error.png")
    figure("Motor current and commanded voltage","Time (s)","Value (A or V)",
           [(t,[r["current_a"] for r in nominal.trajectory],"Current (A)"),
            (t,[r["command_voltage_v"] for r in nominal.trajectory],"Command voltage (V)")],plots/"drive_command.png")
    faultnames=[x for x in faults if faults[x]["first_fault_s"] is not None]
    fig,ax=plt.subplots(figsize=(8.5,4),dpi=135)
    distances=[1000*faults[n]["post_fault_travel_m"] for n in faultnames]
    ax.barh(faultnames,distances)
    ax.set(xlabel="Additional travel after first detected software fault (mm)",title="Illustrative high-impedance coast; not a safety-rated stop")
    ax.grid(axis="x",alpha=.25)
    fig.tight_layout();fig.savefig(plots/"fault_stop_travel.png");plt.close(fig)
    trace_hash=hashlib.sha256((output/"nominal_axis_trace.csv").read_bytes()).hexdigest()
    summary={
        "validation":"software-in-the-loop analytical/ODE simulation; no physical motor testing, no timing guarantees",
        "input_assumptions":str(Path("config/assumed_axis.json")),
        "cad_reference":str(Path("assets/cad_axis_reference.json")),
        "nominal":nominal.summary(),
        "disturbance_6n":disturbance.summary(),
        "faults":faults,
        "assumed_parameter_sweep":{k:v for k,v in robustness.items() if k!="rows"},
        "preliminary_motor_sizing":motor_sizing(cfg),
        "nominal_csv_sha256":trace_hash
    }
    (output/"evidence_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    nom=summary["nominal"];sweep=summary["assumed_parameter_sweep"]
    lines=[
       "# Industrial Servo Motion Control — Engineering Evidence",
       "",
       "**Validation:** deterministic software-in-the-loop model only. Motor, transmission, load, friction, bus voltage, encoder and controller gains are assumptions.",
       "",
       "## Assumed motor sizing",
       "",
       "| Metric | Calculated value |",
       "|---|---:|",
    ]
    for k,v in summary["preliminary_motor_sizing"].items():lines.append(f"| {k} | {v:.6f} |")
    lines += [
       "","## 100 mm nominal trajectory",
       "",f"- Quintic commanded motion duration: **{nom['move_duration_s']:.3f} s**",
       f"- Final position error: **{nom['final_error_m']*1000:.4f} mm**",
       f"- Maximum tracking error during move: **{nom['peak_abs_tracking_error_m']*1000:.4f} mm**",
       f"- Peak simulated winding current: **{nom['peak_current_a']:.3f} A**",
       f"- Peak simulated axis speed: **{nom['peak_speed_m_s']:.3f} m/s**",
       f"- Final controller/supervisor mode: **{nom['final_mode']}**",
       "","## Parameter-variation campaign (assumed distributions)",
       "",f"- Samples: **{sweep['samples']}**, deterministic seed **{sweep['seed']}**",
       f"- Passes under deliberately chosen surrogate screen: **{sweep['assumed_screen_passes']}/{sweep['samples']} ({100*sweep['assumed_screen_pass_rate']:.1f}%)**",
       f"- p95 peak tracking error: **{sweep['peak_tracking_error_p95_mm']:.4f} mm**",
       f"- Highest simulated current: **{sweep['peak_current_max_a']:.3f} A**",
       "", "The percentage is **not** motor reliability, a real tolerance distribution, or a field-failure rate.",
       "","## Injected faults: software response and residual travel",
       "","| Fault | First detected at (s) | Additional travel after fault (mm) | Final supervisor mode |",
       "|---|---:|---:|---|",
    ]
    for name in faultnames:
        v=faults[name]
        lines.append(f"| {name} | {v['first_fault_s']:.3f} | {v['post_fault_travel_m']*1000:.3f} | {v['final_mode']} |")
    lines += [
       "","The coast model treats disabling the drive as ideal high impedance, instantaneously zero current and simplified Coulomb/viscous friction. It is **not** a validated stopping-distance estimate. Independent hardwired emergency stop / STO, limit switches, brake and risk assessment would be required for hardware.",
       "", "## Deliberately excluded from verification",
       "", "- Real motor identification, thermal limits, torque ripple, switching losses, real drive current limits, electromagnetic compatibility or encoder accuracy.",
       "- Real CAN/CANopen, fieldbus latency, RTOS timing, physical homing or certified functional safety.",
       "- Physical inertia, belt compliance, backlash, mechanical resonance, hard-stop contact response or real drivetrain coupling.",
       "", "## Outputs",
       "", "- `nominal_axis_trace.csv` and `disturbance_axis_trace.csv`",
       "- `assumed_parameter_sweep.csv`",
       "- `plots/tracking_position.png`, `plots/tracking_error.png`, `plots/drive_command.png`, `plots/fault_stop_travel.png`",
       "- `evidence_summary.json`",
    ]
    (output/"ENGINEERING_EVIDENCE.md").write_text("\n".join(lines)+"\n")
    print(f"Built {len(robustness['rows'])} deterministic variants, {len(faults)} fault/nominal scenarios")
    print(f"Final error={nom['final_error_m']*1000:.4f} mm, max tracking={nom['peak_abs_tracking_error_m']*1000:.3f} mm")
    print(f"Output: {output}")
    return 0

if __name__=="__main__":raise SystemExit(main())
