"""Loopback rotary motion PLC register interface, compatible with the existing Modbus PDU server.

Units are explicitly DIFFERENT from the original linear-axis register image:
  int32 target/actual = millidegrees; signed 16-bit rpm*10 speed.
No external network or industrial device is involved.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
import math
from .plc_contract import split_signed_32,join_signed_32

class RotaryReg(IntEnum):
    COMMAND=0; SEQUENCE=1; TARGET_HIGH=2; TARGET_LOW=3
    STATUS=100; FAULT=101; ACTUAL_HIGH=102; ACTUAL_LOW=103
    RPM_X10=104; LAST_ACK_SEQ=105

class RotaryCommand(IntEnum):
    NONE=0; MOVE=1; STOP=2; HOME=3; RESET=4

@dataclass(frozen=True)
class RotarySnapshot:
    sequence:int
    operation:RotaryCommand
    target_mdeg:int

class RotaryRegisterImage:
    def __init__(self):
        self.holding={i:0 for i in range(4)}
        self.inputs={i:0 for i in range(100,106)}
        self.last_sequence:int|None=None
        self.last_snapshot:RotarySnapshot|None=None
    def read_holding(self,address:int)->int:
        if address not in self.holding:raise KeyError(address)
        return self.holding[address]
    def write_holding(self,address:int,value:int)->None:
        if address not in self.holding or not isinstance(value,int) or not 0<=value<=65535:
            raise ValueError('bad rotary holding register/value')
        self.holding[address]=value
    def read_input(self,address:int)->int:
        if address not in self.inputs:raise KeyError(address)
        return self.inputs[address]
    def fetch_command(self)->tuple[bool,RotarySnapshot]|None:
        try:operation=RotaryCommand(self.holding[0])
        except ValueError as exc:raise ValueError('invalid operation') from exc
        if operation==RotaryCommand.NONE:return None
        snap=RotarySnapshot(self.holding[1],operation,join_signed_32(self.holding[2],self.holding[3]))
        if self.last_sequence is not None:
            if snap.sequence<self.last_sequence:raise ValueError('stale sequence; rollover requires resync')
            if snap.sequence==self.last_sequence:
                if snap!=self.last_snapshot:raise ValueError('same sequence with modified command')
                return False,snap
        self.last_snapshot=snap;self.last_sequence=snap.sequence;self.inputs[105]=snap.sequence
        return True,snap
    def write_operator_command(self,operation:RotaryCommand,*,sequence:int,target_deg:float=0.0):
        if not math.isfinite(target_deg) or abs(target_deg)>180.0:raise ValueError('target out of virtual bench limits')
        hi,lo=split_signed_32(round(target_deg*1000))
        # Represents a coherent single simulated PLC scan transaction, not four atomic real Modbus writes.
        for idx,value in enumerate((int(operation),sequence,hi,lo)):
            self.write_holding(idx,value)
    def update_telemetry(self,*,state:int,fault:int,angle_deg:float,rpm:float):
        if not math.isfinite(angle_deg) or not math.isfinite(rpm):raise ValueError('invalid encoder signals')
        hi,lo=split_signed_32(round(angle_deg*1000))
        sp=max(-32768,min(32767,round(rpm*10)))&0xffff
        self.inputs.update({100:state,101:fault,102:hi,103:lo,104:sp})
    def angle_mdeg(self)->int:return join_signed_32(self.inputs[102],self.inputs[103])
    def speed_rpm(self)->float:
        n=self.inputs[104]
        return (n-65536 if n&32768 else n)/10.0

class VirtualPLC:
    """One complete, deterministic rotary 90deg→dwell→0deg machine cycle."""
    def __init__(self):
        self.image=RotaryRegisterImage()
        self.sequence=0
        self.step='BOOT'
        self.ready_to_issue_return=False
    def tick(self,ms:int, firmware_state:int, fault:int, angle_deg:float, rpm:float):
        self.image.update_telemetry(state=firmware_state,fault=fault,angle_deg=angle_deg,rpm=rpm)
        if fault:
            self.step='FAULT'
            return
        if ms==100 and self.step=='BOOT':
            self.sequence+=1;self.image.write_operator_command(RotaryCommand.MOVE,sequence=self.sequence,target_deg=90)
            self.step='OUTBOUND'
        if self.step=='OUTBOUND' and firmware_state==3 and ms>=1400:
            self.step='DWELL'
        if self.step=='DWELL' and ms>=2700:
            self.sequence+=1;self.image.write_operator_command(RotaryCommand.MOVE,sequence=self.sequence,target_deg=0)
            self.step='RETURN'
        if self.step=='RETURN' and firmware_state==3 and ms>=3950:
            self.step='COMPLETE'
    def output_to_firmware(self)->tuple[int,int,int]:
        snap=self.image.fetch_command()
        if not snap or not snap[0]:return 0,0,self.image.read_holding(1)
        cmd=snap[1]
        firmware_command={RotaryCommand.MOVE:1,RotaryCommand.STOP:2,RotaryCommand.HOME:1,RotaryCommand.RESET:3}.get(cmd.operation,0)
        target_count=round(cmd.target_mdeg/1000/360*3200) if cmd.operation==RotaryCommand.MOVE else 0
        return firmware_command,target_count,cmd.sequence
