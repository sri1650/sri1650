import math
import pytest
from servo_lab.parameters import load_config
from servo_lab.plant import MotorPlant,PlantState,VirtualEncoder


def test_zero_state_stays_at_rest_without_power():
    plant=MotorPlant(load_config(),position_m=.10)
    for i in range(100):plant.step(0,.001)
    assert plant.position_m==pytest.approx(.10,abs=1e-7)
    assert abs(plant.speed_m_s)<1e-6


def test_electrical_derivative_uses_rl_and_back_emf():
    plant=MotorPlant(load_config())
    d=plant.derivatives(PlantState(0,10.,1.),12.)
    mo=plant.config.motor
    assert d.winding_current_a==pytest.approx((12-mo.winding_resistance_ohm-10*mo.back_emf_constant_v_per_rad_s)/mo.winding_inductance_h)
    assert d.motor_angle_rad==10.


def test_encoder_quantization_bounded_by_half_count():
    cfg=load_config()
    enc=VirtualEncoder(cfg)
    angle=1.2378
    p=enc.sample(angle)
    truth=angle*cfg.mechanics.pulley_radius_m/cfg.mechanics.gear_ratio_motor_to_output
    maxerr=math.pi*cfg.mechanics.pulley_radius_m/(cfg.mechanics.gear_ratio_motor_to_output*cfg.encoder_counts_per_rev)
    assert abs(p-truth)<=maxerr+1e-12


def test_encoder_freeze_and_release():
    cfg=load_config()
    enc=VirtualEncoder(cfg)
    p1=enc.sample(.2,freeze=True)
    p2=enc.sample(.8,freeze=True)
    p3=enc.sample(.8,freeze=False)
    assert p1==p2
    assert p3!=p1


def test_drive_open_circuit_zeroes_current_and_avoids_active_short():
    cfg=load_config()
    plant=MotorPlant(cfg,position_m=.05)
    plant.state=PlantState(7.5,25,2)
    nxt=plant.step(0,.001,drive_enabled=False)
    assert nxt.winding_current_a==0
    assert nxt.motor_speed_rad_s<25
    assert nxt.motor_speed_rad_s>0


def test_limit_clamp_and_contact_record():
    cfg=load_config()
    plant=MotorPlant(cfg,position_m=.299)
    plant.state=PlantState(.299*cfg.mechanics.gear_ratio_motor_to_output/cfg.mechanics.pulley_radius_m,100,0)
    plant.step(24,.01)
    assert plant.position_m<=cfg.mechanics.travel_max_m
    assert plant.hard_stop_contacts>=1


def test_invalid_initial_position():
    with pytest.raises(ValueError):MotorPlant(load_config(),position_m=.4)
