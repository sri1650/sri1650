"""Virtual CAN-like command envelope (not actual CANopen or safety-rated comms)."""
from __future__ import annotations
from dataclasses import dataclass
import json
import zlib


@dataclass(frozen=True)
class VirtualCommand:
    sequence:int
    name:str
    position_m:float|None=None


def encode_command(cmd:VirtualCommand)->bytes:
    if cmd.sequence<0 or cmd.name not in {"MOVE","STOP","HEARTBEAT","HOME","RESET"}:
        raise ValueError("invalid command")
    packet=json.dumps({"seq":cmd.sequence,"op":cmd.name,"position_m":cmd.position_m},sort_keys=True,separators=(",",":")).encode("utf-8")
    checksum=zlib.crc32(packet)
    return len(packet).to_bytes(2,"big")+packet+checksum.to_bytes(4,"big")


def decode_command(frame:bytes)->VirtualCommand:
    if len(frame)<6:
        raise ValueError("short frame")
    length=int.from_bytes(frame[:2],"big")
    if length>256 or len(frame)!=length+6:
        raise ValueError("invalid length")
    data=frame[2:2+length]
    crc=int.from_bytes(frame[-4:],"big")
    if zlib.crc32(data)!=crc:
        raise ValueError("CRC mismatch")
    p=json.loads(data)
    cmd=VirtualCommand(p["seq"],p["op"],p["position_m"])
    if cmd.sequence<0 or cmd.name not in {"MOVE","STOP","HEARTBEAT","HOME","RESET"}:
        raise ValueError("invalid decoded command")
    return cmd


class CommandReceiver:
    def __init__(self):
        self.highest_sequence=-1
        self.last_frame:bytes|None=None

    def accept(self,frame:bytes)->tuple[bool,VirtualCommand]:
        cmd=decode_command(frame)
        if cmd.sequence==self.highest_sequence:
            if frame != self.last_frame:
                raise ValueError("sequence reuse with different content")
            return False,cmd
        if cmd.sequence<self.highest_sequence:
            raise ValueError("replayed older command")
        self.highest_sequence=cmd.sequence
        self.last_frame=frame
        return True,cmd
