#!/usr/bin/env python3
"""Generate honest, deterministic pre-Codex interfaces and identification evidence."""
from __future__ import annotations
from pathlib import Path
import argparse
import csv
import json
import math
import subprocess
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from servo_lab.identification import (
    synthetic_locked_rotor_data,fit_locked_rotor_rl,save_electrical_observations,
    synthetic_mechanical_data,fit_equivalent_mechanics,electrical_step_response,
)
from servo_lab.parameters import load_config,motor_sizing
from servo_lab.schedulability import nominal_task_set,response_time_analysis
from servo_lab.plc_contract import VirtualRegisterImage,StatusCode,Register
from servo_lab.runner import Scenario,run_simulation


def run_fault_campaign(out:Path,seed=2026,count=64)->dict:
    rng=np.random.default_rng(seed)
    cfg=load_config()
    faults=['encoder_invalid','sensor_stale','undervoltage','overtemperature',
            'emergency_stop','heartbeat_loss']
    records=[]
    violations=0
    for n in range(count):
        fault=faults[n%len(faults)]
        initial=.07
        target=float(rng.uniform(.10,.19))
        instant=float(rng.uniform(.2,.5))
        res=run_simulation(cfg,Scenario(name=f'seed{n:03d}_{fault}',duration_s=1.8,
            initial_position_m=initial,target_m=target,inject_fault=fault,
            fault_at_s=instant,fault_duration_s=.5))
        faulted=[p for p in res.trajectory if p['mode'] in ('FAULT','ESTOP')]
        valid=(res.first_fault_s is not None and len(faulted)>0 and all(
            abs(row['command_voltage_v']) < 1e-12 for row in faulted))
        if not valid:violations+=1
        records.append({
            'case':res.scenario,'fault':fault,'target_m':target,'first_fault_s':res.first_fault_s,
            'post_fault_travel_m':res.post_fault_travel_m,'final_mode':res.final_mode,
            'hard_stop_contacts':res.hard_stop_contacts,'voltage_inhibit_verified':valid})
    with (out/'fault_campaign_expanded.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    return {
        'scenarios':count,'seed':seed,'faults':faults,
        'software_voltage_inhibit_violations':violations,
        'max_abs_post_fault_travel_m':max(abs(float(r['post_fault_travel_m'])) for r in records),
        'hard_stop_contacts':sum(int(r['hard_stop_contacts']) for r in records),
        'scope':'SIL assumed plant and software command inhibit; not hardware emergency-stop distance',
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,default=ROOT/'outputs'/'extended_prework')
    ap.add_argument('--host-benchmark',type=Path,default=None)
    args=ap.parse_args()
    out=args.output
    out.mkdir(parents=True,exist_ok=True)
    cfg=load_config()
    e=cfg.motor
    t,i=synthetic_locked_rotor_data(resistance_ohm=e.winding_resistance_ohm,
        inductance_h=e.winding_inductance_h,seed=17)
    save_electrical_observations(out/'synthetic_locked_rotor.csv',t,i,8)
    rl=fit_locked_rotor_rl(t,i,8)
    inertia=motor_sizing(cfg)['total_reflected_inertia_kg_m2']
    w,a,measured_i=synthetic_mechanical_data(inertia_kg_m2=inertia,
        friction_nm_s_rad=e.viscous_friction_nm_per_rad_s,
        coulomb_nm=.012,torque_constant_nm_a=e.torque_constant_nm_per_a)
    mechanical=fit_equivalent_mechanics(w,a,measured_i,e.torque_constant_nm_per_a)
    taskset=response_time_analysis(nominal_task_set())
    r=VirtualRegisterImage()
    r.set_telemetry(status=StatusCode.READY,fault=0,position_m=.10,speed_m_s=0)
    map_snapshot=r.snapshot_inputs()
    faults=run_fault_campaign(out)
    summary={
      'validation_status':'software/synthetic only; no physical motor, no RTOS WCET evidence',
      'assumed_motor_electrical':{'R_ohm':e.winding_resistance_ohm,'L_h':e.winding_inductance_h},
      'synthetic_electrical_fit':vars(rl),
      'synthetic_mechanical_fit':vars(mechanical),
      'assumed_fixed_priority_schedulability':taskset,
      'example_plc_register_snapshot':list(map_snapshot),
      'fault_campaign':faults,
    }
    if args.host_benchmark:
        b=subprocess.run([str(args.host_benchmark)],cwd=ROOT,capture_output=True,text=True,timeout=35,check=True)
        summary['native_host_loop_benchmark']=json.loads(b.stdout)
    (out/'results.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    md=['# Extended pre-Codex servo verification','',
       '**Status:** synthetic software evidence only. Assumed loads and motor constants have not been identified on hardware.','',
       '## Synthetic parameter identification','',
       f'- Locked-rotor RL resistance: **{rl.resistance_ohm:.5f} Ω** (assumed {e.winding_resistance_ohm:.5f} Ω)',
       f'- Locked-rotor inductance: **{rl.inductance_h*1000:.5f} mH** (assumed {e.winding_inductance_h*1000:.5f} mH)',
       f'- Electrical holdout RMSE: **{rl.holdout_rmse_a:.5f} A**',
       f'- Fitted equivalent inertia: **{mechanical.equivalent_inertia_kg_m2:.7f} kg·m²** (assumed {inertia:.7f})',
       f'- Mechanical fit torque RMSE: **{mechanical.residual_rmse_nm:.6f} Nm**',
       '', 'Parameter confidence intervals assume independent Gaussian residual noise; they are not datasheet tolerances.','',
       '## Fixed-priority response-time analysis (assumed task costs)','',
       f'- Task utilisation: **{taskset["assumed_utilisation"]*100:.2f}%**',
       f'- All declared deadlines schedulable under model: **{taskset["all_schedulable"]}**',
       '', '| Task | Period (µs) | Assumed WCET (µs) | Response bound (µs) | Deadline (µs) |',
       '|---|---:|---:|---:|---:|']
    lookup={t.name:t for t in nominal_task_set()}
    for item in taskset['tasks']:
        spec=lookup[item['name']]
        md.append(f'| {item["name"]} | {spec.period_us} | {spec.wcet_us} | {item["response_time_us"]} | {item["deadline_us"]} |')
    md += ['', '**Not** a measurement of actual interrupt latency, WCET or real-time jitter.','',
       '## Deterministic software fault campaign','',
       f'- Cases: **{faults["scenarios"]}**, seed **{faults["seed"]}**',
       f'- Post-fault command voltage inhibit violations: **{faults["software_voltage_inhibit_violations"]}**',
       f'- Maximum absolute simulated post-fault travel: **{faults["max_abs_post_fault_travel_m"]*1000:.2f} mm**',
       f'- Contact-count occurrences in these simulated runs: **{faults["hard_stop_contacts"]}**',
       '', 'These are not safety-rated stopping tests. Drive disable may allow coasting and gravity/load-induced motion.',
       '', '## Communication/embedded boundaries','',
       '- C++ native loop defaults to disabled and latches excessive tick gaps, stale samples or non-finite inputs.',
       '- Virtual CiA402-style state machine prohibits motion until successive controlword transitions.',
       '- Virtual register map and localhost-only Modbus/TCP test server provide register reads/writes; no industrial fieldbus, remote exposure or actuator link.',
       '- Native host benchmark samples **function compute-time**, not end-to-end jitter or an embedded WCET.',
       ]
    if 'native_host_loop_benchmark' in summary:
        bm=summary['native_host_loop_benchmark']
        md+=['',f'- Host benchmark {bm["samples"]} cycles: p50 **{bm["p50_us"]:.3f} µs**, p95 **{bm["p95_us"]:.3f} µs**, p99 **{bm["p99_us"]:.3f} µs**, maximum **{bm["max_us"]:.3f} µs**.']
    (out/'REPORT.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    # Graphical evidence (no external user hardware required).
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8.2,4))
    ax.plot(t*1000,i,'.',markersize=2,alpha=.5,label='Synthetic observed current')
    ax.plot(t*1000,electrical_step_response(t,8,rl.resistance_ohm,rl.inductance_h),label='Fitted RL response')
    ax.set_xlabel('Time (ms)'); ax.set_ylabel('Current (A)');ax.legend();ax.set_title('Synthetic Locked-Rotor Parameter Identification')
    fig.tight_layout();fig.savefig(out/'identification_fit.png',dpi=160);plt.close(fig)
    with (out/'fault_campaign_expanded.csv').open(encoding='utf-8',newline='') as fh:
        fault_rows=list(csv.DictReader(fh))
    categories=sorted(set(row['fault'] for row in fault_rows))
    coast=[max(abs(float(row['post_fault_travel_m'])) for row in fault_rows if row['fault']==category)*1000
           for category in categories]
    fig,ax=plt.subplots(figsize=(9.2,4.4))
    ax.bar(categories,coast)
    ax.set_ylabel('Maximum absolute simulated post-fault travel (mm)')
    ax.set_title('Software-in-Loop Fault Coast Travel (not a safe-stop validation)')
    ax.tick_params(axis='x',rotation=25)
    fig.tight_layout();fig.savefig(out/'fault_coast_comparison.png',dpi=160);plt.close(fig)
    print(json.dumps({'status':'PASS' if faults['software_voltage_inhibit_violations']==0 else 'FAIL',
       'fault_cases':faults['scenarios'],'resistance_ohm':rl.resistance_ohm,
       'inductance_h':rl.inductance_h,'holdout_rmse_a':rl.holdout_rmse_a,
       'target':str(out)},indent=2))
    return 0 if faults['software_voltage_inhibit_violations']==0 else 2

if __name__=='__main__':raise SystemExit(main())
