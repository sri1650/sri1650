"""Reproducible hypothetical parameter-variation study, not real-world reliability evidence."""
from __future__ import annotations
from dataclasses import dataclass,replace
from pathlib import Path
import csv
import math
import random
import statistics
from .parameters import AxisConfig,load_config
from .runner import run_simulation,Scenario


@dataclass(frozen=True)
class ScreeningLimits:
    max_final_abs_error_m:float=0.002
    max_tracking_abs_error_m:float=0.004
    max_peak_current_a:float=7.5
    require_no_stop_contact:bool=True


def vary_assumed_system(cfg:AxisConfig,rng:random.Random)->AxisConfig:
    """Toy independent uniform tolerances; intentionally not calibrated distributions."""
    m,mo=cfg.mechanics,cfg.motor
    m=replace(m,
        moving_mass_kg=m.moving_mass_kg*rng.uniform(.80,1.20),
        coulomb_friction_coefficient=m.coulomb_friction_coefficient*rng.uniform(.65,1.40),
        transmission_efficiency=max(.60,min(.95,m.transmission_efficiency*rng.uniform(.91,1.04))),
        external_disturbance_force_n=rng.uniform(-4,4))
    scale=rng.uniform(.90,1.10)
    mo=replace(mo,
        winding_resistance_ohm=mo.winding_resistance_ohm*rng.uniform(.85,1.15),
        winding_inductance_h=mo.winding_inductance_h*rng.uniform(.8,1.2),
        rotor_inertia_kg_m2=mo.rotor_inertia_kg_m2*rng.uniform(.8,1.2),
        torque_constant_nm_per_a=mo.torque_constant_nm_per_a*scale,
        back_emf_constant_v_per_rad_s=mo.back_emf_constant_v_per_rad_s*scale,
        dc_bus_v=mo.dc_bus_v*rng.uniform(.88,1.06))
    return replace(cfg,mechanics=m,motor=mo)


def screen(n:int=100,seed:int=2026,cfg:AxisConfig|None=None,limits:ScreeningLimits=ScreeningLimits())->dict:
    if n<=0: raise ValueError("n must be positive")
    cfg=load_config() if cfg is None else cfg
    rng=random.Random(seed)
    rows=[]
    for i in range(n):
        sample_cfg=vary_assumed_system(cfg,rng)
        res=run_simulation(sample_cfg,Scenario(name=f"sample_{i:03d}",initial_position_m=0.05,target_m=0.15))
        passed=(abs(res.final_error_m)<=limits.max_final_abs_error_m and
                res.peak_abs_tracking_error_m<=limits.max_tracking_abs_error_m and
                res.peak_current_a<=limits.max_peak_current_a and
                (not limits.require_no_stop_contact or res.hard_stop_contacts==0))
        rows.append({
            "seed":seed,"case_index":i,"moving_mass_kg":sample_cfg.mechanics.moving_mass_kg,
            "friction_coefficient":sample_cfg.mechanics.coulomb_friction_coefficient,
            "motor_resistance_ohm":sample_cfg.motor.winding_resistance_ohm,
            "motor_inductance_h":sample_cfg.motor.winding_inductance_h,
            "motor_torque_constant_nm_per_a":sample_cfg.motor.torque_constant_nm_per_a,
            "bus_voltage_v":sample_cfg.motor.dc_bus_v,
            "final_abs_error_mm":abs(res.final_error_m)*1000,
            "peak_tracking_abs_error_mm":res.peak_abs_tracking_error_m*1000,
            "peak_current_a":res.peak_current_a,
            "hard_stop_contacts":res.hard_stop_contacts,
            "passes_assumed_screen":passed
        })
    def quantile(values,q):
        vals=sorted(values)
        i=q*(len(vals)-1)
        low=math.floor(i)
        high=math.ceil(i)
        return vals[low]*(high-i)+vals[high]*(i-low) if high!=low else vals[low]
    p=sum(r["passes_assumed_screen"] for r in rows)
    return {"samples":n,"seed":seed,"assumed_screen_passes":p,"assumed_screen_pass_rate":p/n,
            "final_abs_error_p95_mm":quantile([r["final_abs_error_mm"] for r in rows],.95),
            "peak_tracking_error_p95_mm":quantile([r["peak_tracking_abs_error_mm"] for r in rows],.95),
            "peak_current_max_a":max(r["peak_current_a"] for r in rows),
            "rows":rows,
            "caution":"Synthetic independent uniform variations; not a measured probability of success or safety reliability."}


def write_rows(report:dict,path:str|Path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",newline="",encoding="utf-8") as f:
        rows=report["rows"]
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
