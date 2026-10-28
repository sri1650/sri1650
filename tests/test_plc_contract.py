import pytest
from servo_lab.plc_contract import (
    Register,StatusCode,CommandCode,VirtualRegisterImage,split_signed_32,join_signed_32
)

def test_signed_32_round_trip():
    for x in (-2147483648,-50000,-1,0,1,300000,2147483647):
        assert join_signed_32(*split_signed_32(x))==x

def test_virtual_register_command_and_duplicate():
    x=VirtualRegisterImage()
    x.write_holding(Register.SEQUENCE,1)
    x.write_holding(Register.COMMAND,CommandCode.MOVE)
    hi,lo=split_signed_32(100000)
    x.write_holding(Register.TARGET_HIGH,hi)
    x.write_holding(Register.TARGET_LOW,lo)
    accepted,cmd=x.fetch_command()
    assert accepted and cmd.position_um==100000
    assert not x.fetch_command()[0]
    assert x.read_input(Register.LAST_ACK_SEQUENCE)==1
    x.write_holding(Register.TARGET_LOW,lo-1)
    with pytest.raises(ValueError):x.fetch_command()

def test_stale_seq_readonly_guard():
    x=VirtualRegisterImage()
    with pytest.raises(ValueError):x.write_holding(Register.FAULT,1)
    x.write_holding(Register.SEQUENCE,2)
    x.write_holding(Register.COMMAND,CommandCode.STOP)
    assert x.fetch_command()[0]
    x.write_holding(Register.SEQUENCE,1)
    with pytest.raises(ValueError):x.fetch_command()

def test_telemetry_snapshot_atomic_image():
    x=VirtualRegisterImage()
    x.set_telemetry(status=StatusCode.MOVING,fault=0,position_m=-0.024,speed_m_s=-.2)
    snap=x.snapshot_inputs()
    assert len(snap)==6
    assert snap[0]==StatusCode.MOVING
    assert join_signed_32(snap[2],snap[3])==-24000
    assert snap[4]==(65536-200)

def test_reject_nan_and_overflow():
    with pytest.raises(ValueError):split_signed_32(2**31)
    with pytest.raises(ValueError):VirtualRegisterImage().set_telemetry(
        status=StatusCode.READY,fault=0,position_m=float('nan'),speed_m_s=0)
