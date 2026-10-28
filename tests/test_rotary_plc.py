"""Rotary register semantics and existing Modbus PDU transport replay."""
import struct
import pytest
from servo_lab.rotary_plc import RotaryRegisterImage,RotaryCommand,VirtualPLC
from servo_lab.modbus_tcp import respond_pdu

def test_rotary_counts_from_millidegree_registers():
    p=VirtualPLC();p.tick(100,1,0,0.0,0.0)
    cmd,target,seq=p.output_to_firmware()
    assert (cmd,target,seq)==(1,800,1)
    assert p.output_to_firmware()[0]==0 # no duplicated actuation

def test_return_dwell_machine_sequence():
    p=VirtualPLC();p.tick(100,1,0,0,0)
    assert p.output_to_firmware()[1]==800
    p.tick(1800,3,0,90.0,0.0)
    assert p.step=='DWELL'
    p.tick(2700,3,0,90.0,0.0)
    assert p.output_to_firmware()==(1,0,2)
    p.tick(4100,3,0,0,0)
    assert p.step=='COMPLETE'

def test_fault_blocks_plc_cycle():
    p=VirtualPLC();p.tick(100,1,0,0,0);p.output_to_firmware();p.tick(900,4,3,30,2)
    assert p.step=='FAULT'

def test_consecutive_command_sequence_and_replay_protection():
    x=RotaryRegisterImage()
    x.write_operator_command(RotaryCommand.MOVE,sequence=9,target_deg=45)
    assert x.fetch_command()[0] is True
    assert x.fetch_command()[0] is False
    x.write_operator_command(RotaryCommand.MOVE,sequence=9,target_deg=50)
    with pytest.raises(ValueError,match='modified'):x.fetch_command()
    x.write_operator_command(RotaryCommand.MOVE,sequence=8,target_deg=50)
    with pytest.raises(ValueError,match='stale'):x.fetch_command()

def test_mdeg_telemetry_and_rpm_sign():
    x=RotaryRegisterImage()
    x.update_telemetry(state=2,fault=0,angle_deg=-42.125,rpm=-6.2)
    assert x.angle_mdeg()==-42125
    assert x.speed_rpm()==-6.2
    assert x.read_input(100)==2

def test_actual_modbus_pdu_operates_rotary_register_image():
    x=RotaryRegisterImage()
    # FC16 atomic multiregister simulated write of controlword/seq/target in mdeg.
    header=bytes([16])+struct.pack('>HHB',0,4,8)
    values=struct.pack('>HHHH',1,5,1,24464) # 90000mdeg=0x00015f90
    response=respond_pdu(x,header+values)
    assert response==bytes([16])+struct.pack('>HH',0,4)
    assert x.fetch_command()[1].target_mdeg==90000
    read=respond_pdu(x,bytes([3])+struct.pack('>HH',0,4))
    assert read[0:2]==bytes([3,8])

def test_bad_target_rejected():
    x=RotaryRegisterImage()
    with pytest.raises(ValueError):x.write_operator_command(RotaryCommand.MOVE,sequence=1,target_deg=250)
