"""Simulated zero-based 16-bit register image, intended for future Modbus/HMI adapter.

NOT Modbus TCP/RTU or a fieldbus implementation. Caller owns transport,
concurrency, validation and watchdog independently of this contract.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
import math

class Register(IntEnum):
    COMMAND=0             # Holding register, 0=none 1=move 2=stop 3=home 4=reset
    SEQUENCE=1            # 16-bit sequence identity
    TARGET_HIGH=2         # signed 32-bit position in micrometres, high word
    TARGET_LOW=3
    STATUS=100            # Input registers (read-only snapshot)
    FAULT=101
    ACTUAL_HIGH=102
    ACTUAL_LOW=103
    SPEED_MM_S=104        # signed i16, mm/s; saturation flagged in report
    LAST_ACK_SEQUENCE=105

class StatusCode(IntEnum):
    DISABLED=0; READY=1; MOVING=2; HOMING=3; FAULT=4

class CommandCode(IntEnum):
    NONE=0; MOVE=1; STOP=2; HOME=3; RESET=4

@dataclass(frozen=True)
class CommandSnapshot:
    seq: int
    operation: CommandCode
    position_um: int


def split_signed_32(value: int) -> tuple[int,int]:
    if not -(1<<31) <= value < (1<<31): raise ValueError("signed position overflow")
    bits=value & 0xffffffff
    return (bits>>16)&0xffff,bits&0xffff


def join_signed_32(high: int,low: int) -> int:
    if any(not isinstance(v,int) or not 0<=v<=65535 for v in (high,low)):
        raise ValueError("register word out of range")
    u=(high<<16)|low
    return u-(1<<32) if u & (1<<31) else u


class VirtualRegisterImage:
    def __init__(self):
        self._holding={int(a):0 for a in (Register.COMMAND,Register.SEQUENCE,Register.TARGET_HIGH,Register.TARGET_LOW)}
        self._input={int(a):0 for a in range(100,106)}
        self._last_seq: int|None=None
        self._last_command: CommandSnapshot|None=None

    def write_holding(self, address:int, value:int)->None:
        if address not in self._holding or not isinstance(value,int) or not 0<=value<=65535:
            raise ValueError("invalid or read-only holding register")
        self._holding[address]=value

    def read_holding(self,address:int)->int:
        return self._holding[address]

    def read_input(self,address:int)->int:
        return self._input[address]

    def fetch_command(self)->tuple[bool,CommandSnapshot]|None:
        try: code=CommandCode(self._holding[int(Register.COMMAND)])
        except ValueError as exc:raise ValueError("unknown command code") from exc
        if code is CommandCode.NONE:return None
        seq=self._holding[int(Register.SEQUENCE)]
        position=join_signed_32(self._holding[int(Register.TARGET_HIGH)],self._holding[int(Register.TARGET_LOW)])
        cmd=CommandSnapshot(seq,code,position)
        if self._last_seq is not None:
            if seq==self._last_seq:
                if cmd!=self._last_command:raise ValueError("sequence reused for different command")
                return False,cmd
            # 16-bit sequence wrap is not silently accepted; resync is explicit.
            if seq < self._last_seq:raise ValueError("stale sequence or unhandled 16-bit rollover")
        self._last_seq=seq
        self._last_command=cmd
        self._input[int(Register.LAST_ACK_SEQUENCE)]=seq
        return True,cmd

    def set_telemetry(self, *, status:StatusCode, fault:int,position_m:float,speed_m_s:float)->None:
        if not all(math.isfinite(v) for v in (position_m,speed_m_s)) or not 0<=fault<=65535:
            raise ValueError("invalid telemetry")
        pos_um=int(round(position_m*1e6))
        hi,lo=split_signed_32(pos_um)
        speed_mm_s=max(-32768,min(32767,int(round(speed_m_s*1000))))
        self._input.update({int(Register.STATUS):int(status),int(Register.FAULT):fault,
           int(Register.ACTUAL_HIGH):hi,int(Register.ACTUAL_LOW):lo,
           int(Register.SPEED_MM_S):speed_mm_s & 0xffff})

    def snapshot_inputs(self)->tuple[int,...]:
        """One consistent image; caller must provide cross-thread/transport locking."""
        return tuple(self._input[i] for i in range(100,106))
