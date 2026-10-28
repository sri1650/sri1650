import copy
import json
import pytest
from servo_lab.parameters import load_config,motor_sizing,Mechanics,Motor
from pathlib import Path


def test_load_and_sizing():
    c=load_config()
    r=motor_sizing(c)
    assert r["shaft_torque_nm"]==pytest.approx((8+0.12*8*9.81)*.02/(3*.85))
    assert r["current_for_force_a"]<c.motor.continuous_current_a
    assert r["approx_voltage_needed_v"]<c.motor.dc_bus_v
    assert r["total_reflected_inertia_kg_m2"]>c.motor.rotor_inertia_kg_m2


def test_cad_reference_physical_axis_values():
    root=Path(__file__).resolve().parents[1]
    d=json.loads((root/"assets/cad_axis_reference.json").read_text())["motion_axis"]
    c=load_config()
    assert d["moving_mass_kg"]==c.mechanics.moving_mass_kg
    assert d["pulley_radius_mm"]==1000*c.mechanics.pulley_radius_m
    assert d["friction_coefficient"]==c.mechanics.coulomb_friction_coefficient
    assert d["transmission_efficiency"]==c.mechanics.transmission_efficiency
    assert d["target_speed_m_s"]==c.control.max_speed_m_s
    assert d["candidate_motor_continuous_torque_nm"]==c.motor.continuous_torque_nm


def test_reject_nonphysical_inertia_or_voltage():
    cfg=load_config()
    d=dict(vars(cfg.motor))
    d["winding_inductance_h"]=0
    with pytest.raises(ValueError): Motor(**d)
    d=dict(vars(cfg.mechanics));d["transmission_efficiency"]=1.3
    with pytest.raises(ValueError): Mechanics(**d)


def test_config_contains_assumptions_warning():
    assert "ASSUMED" in load_config().status


def test_bad_current_limit_from_config(tmp_path):
    root=Path(__file__).resolve().parents[1]
    d=json.loads((root/"config/assumed_axis.json").read_text())
    d["control"]["current_limit_a"]=100
    p=tmp_path/"bad.json";p.write_text(json.dumps(d))
    with pytest.raises(ValueError):load_config(p)
