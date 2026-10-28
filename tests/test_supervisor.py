import pytest
from servo_lab.supervisor import AxisSupervisor,AxisMode
from servo_lab.parameters import load_config
from servo_lab.plant import Feedback


def fb(**changes):
    d=dict(position_m=.05,speed_rad_s=0,current_a=0,timestamp_s=.10)
    d.update(changes)
    return Feedback(**d)


def test_supervisor_enabled_in_sil():
    s=AxisSupervisor(load_config());s.enable_after_homing(0)
    s.heartbeat(.10)
    r=s.update(.10,fb())
    assert r.mode is AxisMode.ENABLED and r.enable_voltage


@pytest.mark.parametrize("changes,reason",[
    ({"encoder_valid":False},"encoder_invalid"),
    ({"drive_ready":False},"drive_not_ready"),
    ({"winding_temperature_c":100},"winding_overtemperature"),
    ({"bus_voltage_v":16},"dc_bus_undervoltage"),
    ({"timestamp_s":0},"stale_sensor"),
    ({"position_m":.5},"position_out_of_range"),
])
def test_supervision_faults(changes,reason):
    s=AxisSupervisor(load_config());s.enable_after_homing(0);s.heartbeat(.10)
    r=s.update(.10,fb(**changes))
    assert not r.enable_voltage and r.mode is AxisMode.FAULT
    assert r.reason==reason
    assert not s.update(.15,fb(timestamp_s=.15)).enable_voltage
    s.reset_fault()
    assert s.mode is AxisMode.DISABLED


def test_watchdog_timeout():
    s=AxisSupervisor(load_config());s.enable_after_homing(0)
    assert s.update(.201,fb(timestamp_s=.201)).reason=="command_heartbeat_timeout"


def test_estop_latched():
    s=AxisSupervisor(load_config());s.enable_after_homing(0)
    r=s.update(.01,fb(emergency_stop=True,timestamp_s=.01))
    assert r.mode is AxisMode.ESTOP
    assert not s.update(.02,fb(timestamp_s=.02)).enable_voltage


def test_homing_supervision_state_transitions_with_synthetic_switch():
    s=AxisSupervisor(load_config());s.start_homing(0)
    s.heartbeat(.01)
    r=s.update(.01,fb(position_m=.04,timestamp_s=.01))
    assert r.mode is AxisMode.HOMING_SEEK
    r=s.update(.02,fb(position_m=0,timestamp_s=.02))
    assert r.mode is AxisMode.HOMING_BACKOFF
    r=s.update(.03,fb(position_m=.015,timestamp_s=.03))
    assert r.mode is AxisMode.ENABLED
