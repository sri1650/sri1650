import pytest
from servo_lab.robustness import screen,vary_assumed_system
from servo_lab.parameters import load_config
import random


def test_fixed_seed_robustness_is_reproducible():
    a=screen(n=8,seed=12)
    b=screen(n=8,seed=12)
    assert a==b
    assert a["samples"]==8
    assert 0<=a["assumed_screen_pass_rate"]<=1


def test_parameter_samples_stay_physical():
    c=load_config()
    rng=random.Random(0)
    for _ in range(40):
        x=vary_assumed_system(c,rng)
        assert x.motor.dc_bus_v>0
        assert 0<x.mechanics.transmission_efficiency<=1
        assert x.motor.torque_constant_nm_per_a>0
        assert x.motor.back_emf_constant_v_per_rad_s==pytest.approx(x.motor.torque_constant_nm_per_a)


def test_invalid_sample_count():
    with pytest.raises(ValueError): screen(n=0)
