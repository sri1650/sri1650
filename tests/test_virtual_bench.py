"""Portable C firmware in host-in-the-loop gearmotor simulation (not physical HIL)."""
import ctypes as C
import math
from pathlib import Path
import pytest
from servo_lab.virtual_bench import (PublishedBench,Firmware,Input,run_bench,SCENARIOS,VirtualMotor)

@pytest.fixture(scope='module')
def bench_firmware():
    from tools.build_virtual_firmware import build,ROOT
    return build(ROOT/'build/virtual_firmware',arm=True)

def test_published_spec_is_internally_consistent():
    s=PublishedBench.load()
    assert s.voltage==24 and s.enc_counts==3200 and s.gear_ratio==50
    assert abs(s.Ke-0.02215)<0.00005
    assert s.R==8.0 and s.stall_a==3.0
    motor_rad_s=s.no_load_output_rpm*s.gear_ratio*2*math.pi/60
    assert (s.voltage-s.i0*s.R)/motor_rad_s==pytest.approx(s.Ke,rel=1e-9)


def test_no_load_operating_point_is_calibrated_not_measured():
    s=PublishedBench.load()
    omega_out=s.no_load_output_rpm*2*math.pi/60
    armature_a=(s.voltage-s.Ke*s.gear_ratio*omega_out)/s.R
    torque_out=s.Kt*armature_a*s.gear_ratio*s.eta
    drag=s.friction*math.tanh(omega_out/0.14)+s.viscous*omega_out
    assert armature_a==pytest.approx(s.i0,rel=1e-9)
    assert torque_out==pytest.approx(drag,rel=1e-4)


def test_host_firmware_build_and_arm_codegen(bench_firmware):
    root=Path(__file__).resolve().parents[1]
    assert (root/bench_firmware['host_shared_library']).is_file()
    if bench_firmware['arm_compile_only']:
        blob=(root/bench_firmware['arm_elf']).read_bytes()
        assert blob[:4]==b'\x7fELF'
        assert blob[18]==40 # ARM machine ID
    else:
        assert bench_firmware.get('arm_unavailable_reason') # unsupported cross-toolchain is explicit

def test_nominal_complete_motion(bench_firmware):
    result=run_bench()
    assert result.fault=='NONE'
    assert result.final_state=='DONE'
    assert result.reached_target
    assert abs(result.final_angle_deg)<2.0
    assert result.max_abs_current_a<0.5
    assert result.peak_abs_output_speed_rpm<50
    out=max((x['position_deg'] for x in result.trace if x['t_s']<2.6),default=0)
    assert abs(out-90)<2.0
    assert all(x['enabled']==0 for x in result.trace if x['t_s']<0.1)

def test_driver_coast_when_command_disabled():
    s=PublishedBench.load();plant=VirtualMotor(s)
    plant.omega=5.0;plant.step(0.0,False)
    assert plant.omega>0
    assert plant.current==0 # modelled open-circuit assumption

def test_adc_quantisation_and_encoder_counts():
    s=PublishedBench.load();plant=VirtualMotor(s)
    plant.angle=math.pi/2
    assert plant.encoder_count()==800
    plant.current=0.4
    assert abs(plant.sampled_current()-0.4)<0.015

@pytest.mark.parametrize('name,fault',[('encoder_loss','ENCODER'),('driver_fault','DRIVER'),
    ('heartbeat_loss','HEARTBEAT'),('estop','ESTOP'),('interlock_open','INTERLOCK'),
    ('undervoltage','BUS'),('overtemperature','TEMPERATURE'),('overcurrent','OVERCURRENT'),
    ('stale_feedback','STALE'),('timing_gap','TIMING'),('jam','TRACK_TIMEOUT'),
    ('bad_target','BAD_TARGET')])
def test_fault_latched_no_output(name,fault):
    r=run_bench(name)
    assert r.fault==fault and r.final_state=='FAULT'
    assert r.post_fault_enabled_violations==0
    assert 0<=r.max_abs_pwm<=1
    assert all(x['enabled']==0 for x in r.trace if x['state']=='FAULT')

def test_command_stop_never_reports_safe_stop_distance():
    r=run_bench('command_stop')
    assert r.final_state=='READY' and r.fault=='NONE'
    assert r.final_angle_deg>0


def _safe_input(time_ms:int,command=0,sequence=0,target=800):
    return Input(encoder_count=0,target_count=target,time_ms=time_ms,sample_ms=time_ms,
        command_sequence=sequence,command=command,encoder_good=1,driver_good=1,
        interlock_good=1,estop=0,heartbeat_good=1,winding_current_a=0,
        bus_voltage_v=24,temperature_c=25)

def test_boot_disabled_and_explicit_reset_required(bench_firmware):
    fw=Firmware()
    assert fw.cycle(_safe_input(0)).drive_enable==0
    assert fw.cycle(_safe_input(1,command=1,sequence=1)).drive_enable==1
    fault=_safe_input(2);fault.estop=1
    assert fw.cycle(fault).drive_enable==0
    assert fw.cycle(_safe_input(3)).fault==1
    assert fw.cycle(_safe_input(4,command=1,sequence=2)).drive_enable==0
    assert fw.cycle(_safe_input(5,command=3,sequence=3)).state==1
    assert fw.cycle(_safe_input(6)).drive_enable==0
    assert fw.cycle(_safe_input(7,command=1,sequence=4)).drive_enable==1

def test_reset_disallowed_while_fault_input_asserted(bench_firmware):
    fw=Firmware();fw.cycle(_safe_input(0));x=_safe_input(1);x.estop=1
    assert fw.cycle(x).fault==1
    x=_safe_input(2,command=3,sequence=1);x.estop=1
    assert fw.cycle(x).fault==1

def test_nonfinite_current_latches_fault(bench_firmware):
    fw=Firmware();fw.cycle(_safe_input(0));x=_safe_input(1);x.winding_current_a=float('nan')
    assert fw.cycle(x).fault==11
