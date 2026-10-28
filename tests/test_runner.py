import pytest
from servo_lab.parameters import load_config
from servo_lab.runner import run_simulation,Scenario,run_campaign


def test_nominal_trajectory_is_reproducible_and_accurate():
    a=run_simulation()
    b=run_simulation()
    assert a.summary()==b.summary()
    assert abs(a.final_error_m)<.0002
    assert a.peak_abs_tracking_error_m<.002
    assert a.final_mode=="ENABLED"
    assert a.peak_current_a<load_config().motor.peak_current_a
    assert a.hard_stop_contacts==0


def test_disturbance_step_has_bounded_tracking():
    out=run_simulation(scenario=Scenario("disturbance",disturbance_force_n=6.0))
    assert abs(out.final_error_m)<.001
    assert out.peak_abs_tracking_error_m<.003


@pytest.mark.parametrize("kind,mode",[("encoder_invalid","FAULT"),("undervoltage","FAULT"),
                                      ("overtemperature","FAULT"),("sensor_stale","FAULT"),
                                      ("emergency_stop","ESTOP")])
def test_faults_inhibit_drive_and_latch(kind,mode):
    out=run_simulation(scenario=Scenario(kind,inject_fault=kind,fault_at_s=.35))
    assert out.final_mode==mode
    assert out.first_fault_s==pytest.approx(.35)
    assert out.post_fault_travel_m is not None
    assert out.post_fault_travel_m>.005
    assert out.trajectory[-1]["command_voltage_v"]==0


def test_heartbeat_fails_but_after_defined_timeout():
    out=run_simulation(scenario=Scenario("heartbeat_loss",inject_fault="heartbeat_loss",fault_at_s=.35))
    assert out.final_mode=="FAULT"
    assert .5<=out.first_fault_s<=.55


def test_campaign_contains_nominal_and_fault_cases():
    out=run_campaign()
    assert len(out)==8
    assert out["nominal"]["first_fault_s"] is None
    assert out["sensor_stale"]["first_fault_s"] is not None


def test_reject_target_outside_travel():
    with pytest.raises(ValueError):run_simulation(scenario=Scenario(target_m=.7))
