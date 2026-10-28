"""1 kHz software-in-the-loop simulation, not embedded or hardware-in-loop evidence."""
from __future__ import annotations
from dataclasses import dataclass
import csv
import json
from pathlib import Path
import math
from .parameters import AxisConfig, load_config
from .plant import MotorPlant, Feedback, VirtualEncoder
from .controller import CascadedController
from .trajectory import QuinticMove
from .supervisor import AxisSupervisor, AxisMode


@dataclass(frozen=True)
class Scenario:
    name:str="nominal"
    duration_s:float=2.5
    target_m:float|None=None
    initial_position_m:float|None=None
    inject_fault:str|None=None
    fault_at_s:float=0.35
    fault_duration_s:float=0.20
    disturbance_force_n:float=0.0
    disturbance_start_s:float=0.3
    disturbance_end_s:float=0.8


@dataclass(frozen=True)
class RunResult:
    scenario:str
    final_position_m:float
    final_velocity_m_s:float
    final_error_m:float
    peak_abs_tracking_error_m:float
    peak_speed_m_s:float
    peak_current_a:float
    peak_voltage_v:float
    final_mode:str
    first_fault_s:float|None
    samples:int
    move_duration_s:float
    max_position_m:float
    hard_stop_contacts:int
    fault_position_m:float|None
    post_fault_travel_m:float|None
    trajectory:tuple[dict, ...]

    def summary(self)->dict:
        return {k:v for k,v in vars(self).items() if k!="trajectory"}

    def to_csv(self,path:str|Path)->None:
        p=Path(path)
        p.parent.mkdir(parents=True,exist_ok=True)
        with p.open("w",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=list(self.trajectory[0].keys()))
            writer.writeheader()
            writer.writerows(self.trajectory)


def run_simulation(cfg:AxisConfig|None=None, scenario:Scenario=Scenario())->RunResult:
    cfg=load_config() if cfg is None else cfg
    c,m,mo=cfg.control,cfg.mechanics,cfg.motor
    target=c.target_position_m if scenario.target_m is None else scenario.target_m
    start=m.travel_min_m if scenario.initial_position_m is None else scenario.initial_position_m
    if scenario.duration_s<=0 or not(m.travel_min_m<=target<=m.travel_max_m) or not(m.travel_min_m<=start<=m.travel_max_m):
        raise ValueError("invalid run duration/target")
    plant=MotorPlant(cfg,position_m=start)
    encoder=VirtualEncoder(cfg)
    ctrl=CascadedController(cfg)
    supervisor=AxisSupervisor(cfg)
    supervisor.enable_after_homing(0.0)  # Explicit SIL bypass; not valid on hardware.
    move=QuinticMove.for_limits(start,target,v_max=c.max_speed_m_s,a_max=c.max_acceleration_m_s2,j_max=c.max_jerk_m_s3)
    rows=[]
    fault_time=None
    fault_pos=None
    n=round(scenario.duration_s/c.tick_s)
    peak_error=peak_speed=peak_current=peak_voltage=peak_pos=0.0
    for k in range(n+1):
        t=k*c.tick_s
        fault_on=(scenario.inject_fault is not None and scenario.fault_at_s<=t<scenario.fault_at_s+scenario.fault_duration_s)
        if k % 50 == 0 and not (scenario.inject_fault=="heartbeat_loss" and t>=scenario.fault_at_s):
            supervisor.heartbeat(t)
        feedback_time=t-0.05 if fault_on and scenario.inject_fault=="sensor_stale" else t
        bus=14.0 if fault_on and scenario.inject_fault=="undervoltage" else mo.dc_bus_v
        temp=100.0 if fault_on and scenario.inject_fault=="overtemperature" else 35.0
        enc_valid=not (fault_on and scenario.inject_fault=="encoder_invalid")
        estop=fault_on and scenario.inject_fault=="emergency_stop"
        pos=encoder.sample(plant.state.motor_angle_rad,freeze=fault_on and scenario.inject_fault=="encoder_freeze")
        fb=Feedback(pos,plant.state.motor_speed_rad_s,plant.state.winding_current_a,
                    feedback_time,enc_valid,True,bus,temp,estop)
        status=supervisor.update(t,fb)
        if status.mode in (AxisMode.FAULT,AxisMode.ESTOP) and fault_time is None:
            fault_time=t
            fault_pos=plant.position_m
        ref=move.sample(t)
        if status.enable_voltage:
            out=ctrl.step(ref,fb)
            voltage=out.voltage_v
        else:
            ctrl.reset()
            voltage=0.0
        load=scenario.disturbance_force_n if scenario.disturbance_start_s<=t<scenario.disturbance_end_s else 0.0
        if k<n:
            plant.step(voltage,c.tick_s,disturbance_force_n=load,bus_voltage_v=bus,drive_enabled=status.enable_voltage)
        err=ref.position_m-plant.position_m
        peak_error=max(peak_error,abs(err))
        peak_speed=max(peak_speed,abs(plant.speed_m_s))
        peak_current=max(peak_current,abs(plant.state.winding_current_a))
        peak_voltage=max(peak_voltage,abs(voltage))
        peak_pos=max(peak_pos,plant.position_m)
        rows.append({"t_s":round(t,6),"reference_m":ref.position_m,"position_m":plant.position_m,
                     "reference_speed_m_s":ref.velocity_m_s,"speed_m_s":plant.speed_m_s,
                     "current_a":plant.state.winding_current_a,"command_voltage_v":voltage,
                     "tracking_error_m":err,"mode":status.mode.value,"load_disturbance_n":load})
    final_error=target-plant.position_m
    return RunResult(scenario.name,plant.position_m,plant.speed_m_s,final_error,peak_error,
                     peak_speed,peak_current,peak_voltage,supervisor.mode.value,fault_time,len(rows),
                     move.duration_s,peak_pos,plant.hard_stop_contacts,fault_pos,
                     None if fault_pos is None else plant.position_m-fault_pos,tuple(rows))


def run_campaign(cfg:AxisConfig|None=None)->dict[str,dict]:
    cfg=load_config() if cfg is None else cfg
    scenarios=[Scenario(),Scenario("load_step",disturbance_force_n=6.0),
               Scenario("encoder_invalid",inject_fault="encoder_invalid"),
               Scenario("undervoltage",inject_fault="undervoltage"),
               Scenario("overtemperature",inject_fault="overtemperature"),
               Scenario("sensor_stale",inject_fault="sensor_stale"),
               Scenario("emergency_stop",inject_fault="emergency_stop"),
               Scenario("heartbeat_loss",inject_fault="heartbeat_loss",fault_duration_s=1.5)]
    return {s.name:run_simulation(cfg,s).summary() for s in scenarios}
