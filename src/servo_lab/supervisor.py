"""Non-certified software supervision; never substitute for independent physical STO/e-stop."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .parameters import AxisConfig
from .plant import Feedback


class AxisMode(str,Enum):
    DISABLED="DISABLED"
    HOMING_SEEK="HOMING_SEEK"
    HOMING_BACKOFF="HOMING_BACKOFF"
    ENABLED="ENABLED"
    FAULT="FAULT"
    ESTOP="ESTOP"


@dataclass(frozen=True)
class Supervision:
    mode:AxisMode
    enable_voltage:bool
    reason:str
    position_command_m:float|None=None


class AxisSupervisor:
    def __init__(self,cfg:AxisConfig):
        self.cfg=cfg
        self.mode=AxisMode.DISABLED
        self.last_command_s=0.0
        self.latch_reason=""
        self._homing_started_s:float|None=None

    def heartbeat(self,now_s:float):
        if now_s<self.last_command_s: raise ValueError("clock moved backwards")
        self.last_command_s=now_s

    def start_homing(self,now_s:float):
        if self.mode not in (AxisMode.DISABLED, AxisMode.ENABLED):
            raise ValueError("cannot start homing from current mode")
        self.mode=AxisMode.HOMING_SEEK
        self._homing_started_s=now_s
        self.heartbeat(now_s)

    def enable_after_homing(self,now_s:float):
        """For SIL scenarios only; a real machine needs an independent homing reference."""
        if self.mode is not AxisMode.DISABLED:
            raise ValueError("enable only from disabled")
        self.mode=AxisMode.ENABLED
        self.heartbeat(now_s)

    def stop(self):
        if self.mode not in (AxisMode.FAULT,AxisMode.ESTOP): self.mode=AxisMode.DISABLED

    def reset_fault(self):
        if self.mode not in (AxisMode.FAULT,AxisMode.ESTOP):
            raise ValueError("not faulted")
        self.mode=AxisMode.DISABLED
        self.latch_reason=""

    def update(self,now_s:float,fb:Feedback)->Supervision:
        if fb.emergency_stop:
            self.mode=AxisMode.ESTOP;self.latch_reason="emergency_stop_input"
        elif self.mode in (AxisMode.ENABLED,AxisMode.HOMING_SEEK,AxisMode.HOMING_BACKOFF):
            if now_s-self.last_command_s>self.cfg.command_timeout_s:
                self.mode=AxisMode.FAULT;self.latch_reason="command_heartbeat_timeout"
            elif now_s-fb.timestamp_s>self.cfg.sensor_stale_limit_s:
                self.mode=AxisMode.FAULT;self.latch_reason="stale_sensor"
            elif not fb.encoder_valid:
                self.mode=AxisMode.FAULT;self.latch_reason="encoder_invalid"
            elif not fb.drive_ready:
                self.mode=AxisMode.FAULT;self.latch_reason="drive_not_ready"
            elif fb.bus_voltage_v<self.cfg.min_bus_v:
                self.mode=AxisMode.FAULT;self.latch_reason="dc_bus_undervoltage"
            elif fb.winding_temperature_c>=self.cfg.overtemperature_c:
                self.mode=AxisMode.FAULT;self.latch_reason="winding_overtemperature"
            elif fb.position_m<self.cfg.mechanics.travel_min_m-1e-6 or fb.position_m>self.cfg.mechanics.travel_max_m+1e-6:
                self.mode=AxisMode.FAULT;self.latch_reason="position_out_of_range"

        if self.mode is AxisMode.HOMING_SEEK and fb.position_m<=self.cfg.mechanics.travel_min_m+1e-5:
            self.mode=AxisMode.HOMING_BACKOFF
        if self.mode is AxisMode.HOMING_BACKOFF and fb.position_m>=self.cfg.mechanics.travel_min_m+0.01:
            self.mode=AxisMode.ENABLED

        enabled=self.mode in (AxisMode.HOMING_SEEK,AxisMode.HOMING_BACKOFF,AxisMode.ENABLED)
        command=None
        if self.mode is AxisMode.HOMING_SEEK:
            command=self.cfg.mechanics.travel_min_m
        if self.mode is AxisMode.HOMING_BACKOFF:
            command=self.cfg.mechanics.travel_min_m+0.015
        return Supervision(self.mode,enabled,self.latch_reason,command)
