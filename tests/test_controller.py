import math
import pytest
from servo_lab.parameters import load_config
from servo_lab.controller import CascadedController
from servo_lab.plant import Feedback
from servo_lab.trajectory import TrajectoryPoint


def test_current_and_voltage_are_bounded():
    c=load_config();ctrl=CascadedController(c)
    ref=TrajectoryPoint(.29,.35,1,0)
    for _ in range(500):
        o=ctrl.step(ref,Feedback(.01,0,0,0))
        assert o.valid
        assert abs(o.voltage_v)<=c.motor.dc_bus_v
        assert abs(o.target_current_a)<=c.control.current_limit_a


def test_soft_limit_blocks_positive_motion_near_max():
    c=load_config(); ctrl=CascadedController(c)
    o=ctrl.step(TrajectoryPoint(.35,.1,0,0),Feedback(.299,0,0,0))
    assert o.target_velocity_m_s<=0


def test_invalid_feedback_disables_and_clears_integral():
    c=load_config(); ctrl=CascadedController(c)
    ref=TrajectoryPoint(.1,0,0,0)
    for _ in range(50):ctrl.step(ref,Feedback(0,0,0,0))
    assert ctrl.tick==50
    o=ctrl.step(ref,Feedback(0,0,0,0,encoder_valid=False))
    assert not o.valid and o.voltage_v==0
    assert ctrl.tick==0


def test_nonfinite_feedback_is_rejected():
    c=load_config();ctrl=CascadedController(c)
    o=ctrl.step(TrajectoryPoint(.1,0,0,0),Feedback(0,math.nan,0,0))
    assert not o.valid


def test_reset_restores_baseline():
    c=load_config();a=CascadedController(c)
    b=CascadedController(c)
    ref=TrajectoryPoint(.08,.1,.2,0)
    fb=Feedback(.01,0,0,0)
    for _ in range(10):a.step(ref,fb)
    a.reset()
    assert a.step(ref,fb)==b.step(ref,fb)
