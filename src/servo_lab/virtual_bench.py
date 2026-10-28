"""Vendor-grounded, assumption-labelled rotary bench simulation driving the SAME C firmware core.

No STM32 hardware, motor, driver or safety-rated circuit exists in this study.
The firmware controller is compiled as host shared library and also cross-compiled to ARM.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import csv
import ctypes as C
import json
import math
import subprocess
import sys
import sys
from typing import Literal
from .rotary_plc import VirtualPLC

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'config/published_reference_bench.json'

class Input(C.Structure):
    _fields_=[('encoder_count',C.c_int32),('target_count',C.c_int32),('time_ms',C.c_uint32),
      ('sample_ms',C.c_uint32),('command_sequence',C.c_uint16),('command',C.c_uint8),
      ('encoder_good',C.c_uint8),('driver_good',C.c_uint8),('interlock_good',C.c_uint8),
      ('estop',C.c_uint8),('heartbeat_good',C.c_uint8),('winding_current_a',C.c_float),
      ('bus_voltage_v',C.c_float),('temperature_c',C.c_float)]
class Output(C.Structure):
    _fields_=[('normalized_pwm',C.c_float),('target_current_a',C.c_float),
      ('filtered_velocity_rad_s',C.c_float),('drive_enable',C.c_uint8),
      ('state',C.c_uint8),('fault',C.c_uint16),('position_error_counts',C.c_int32)]
class Core(C.Structure):
    _fields_=[('ticks',C.c_uint32),('last_time_ms',C.c_uint32),('start_ms',C.c_uint32),
      ('last_command_sequence',C.c_uint16),('state',C.c_uint8),('started',C.c_uint8),
      ('sequence_seen',C.c_uint8),('fault',C.c_uint16),('last_encoder_count',C.c_int32),
      ('start_encoder_count',C.c_int32),('target_encoder_count',C.c_int32),
      ('filtered_velocity',C.c_float),('velocity_reference',C.c_float),('current_reference',C.c_float),
      ('velocity_integral',C.c_float),('current_integral',C.c_float)]

STATE={0:'BOOT',1:'READY',2:'MOVING',3:'DONE',4:'FAULT'}
FAULT={0:'NONE',1:'ESTOP',2:'INTERLOCK',3:'ENCODER',4:'DRIVER',5:'HEARTBEAT',6:'BUS',
       7:'TEMPERATURE',8:'OVERCURRENT',9:'TIMING',10:'STALE',11:'NUMERIC',12:'TRACK_TIMEOUT',13:'BAD_TARGET'}

@dataclass(frozen=True)
class PublishedBench:
    voltage:float
    i0:float
    stall_a:float
    no_load_output_rpm:float
    gear_ratio:float
    enc_counts:int
    R:float
    L:float
    Ke:float
    Kt:float
    eta:float
    J:float
    friction:float
    viscous:float
    ambient:float
    heat:float
    cool:float
    dt:float

    @classmethod
    def load(cls,path:Path=CONFIG)->'PublishedBench':
        cfg=json.loads(Path(path).read_text());v=cfg['vendor_data'];d=cfg['derived_not_independently_measured'];a=cfg['assumptions_not_vendor_specifications']
        assert a['simulation_only'] is True
        assert abs(v['extrapolated_stall_current_a_at_24v']*d['winding_resistance_ohm_from_24v_over_extrapolated_3a']-v['motor_voltage_v'])<1e-9
        shaft_rad_s=v['no_load_output_speed_rpm_at_24v']*v['gear_ratio']*2*math.pi/60
        ke=(v['motor_voltage_v']-v['no_load_current_a_at_24v']*d['winding_resistance_ohm_from_24v_over_extrapolated_3a'])/shaft_rad_s
        assert abs(ke-d['electromagnetic_back_emf_v_per_rad_s_from_no_load'])<2e-5
        assert v['quadrature_counts_per_motor_rev_x4']*v['gear_ratio']==v['quadrature_counts_per_output_rev_x4']
        return cls(v['motor_voltage_v'],v['no_load_current_a_at_24v'],v['extrapolated_stall_current_a_at_24v'],
          v['no_load_output_speed_rpm_at_24v'],v['gear_ratio'],v['quadrature_counts_per_output_rev_x4'],
          d['winding_resistance_ohm_from_24v_over_extrapolated_3a'],a['winding_inductance_h'],ke,ke,
          a['gearbox_efficiency'],a['rotor_inertia_kg_m2']*v['gear_ratio']**2+a['bench_load_inertia_at_output_kg_m2'],
          a['coulomb_friction_at_output_nm'],a['viscous_friction_at_output_nm_per_rad_s'],
          a['ambient_temperature_c'],a['thermal_heating_c_per_a2_s'],a['thermal_cooling_per_s'],a['firmware_tick_s'])

class VirtualMotor:
    def __init__(self,s:PublishedBench):
        self.s=s;self.angle=0.0;self.omega=0.0;self.current=0.0;self.temperature=s.ambient
    def step(self,duty:float,enabled:bool, *,jam:bool=False,load_nm:float=0.0):
        s=self.s
        duty=max(-1.0,min(1.0,duty)) if enabled else 0.0
        if enabled:
            equilibrium=(s.voltage*duty-s.Ke*s.gear_ratio*self.omega)/s.R
            self.current=equilibrium+(self.current-equilibrium)*math.exp(-s.R*s.dt/s.L)
        else:
            # High-impedance simplified decay; not physical current recirculation/braking modelling.
            self.current=0.0
        t=s.Kt*s.gear_ratio*s.eta*self.current
        drag=s.friction*math.tanh(self.omega/0.14)+s.viscous*self.omega
        if jam:
            # Simulated fixture immobilises output; controller may fault on tracking timeout/current.
            self.omega=0.0
        else:
            accel=(t-drag-load_nm)/s.J
            self.omega+=accel*s.dt
            self.angle+=self.omega*s.dt
        self.temperature+=s.dt*(s.heat*self.current*self.current-s.cool*(self.temperature-s.ambient))
    def encoder_count(self)->int:
        return int(round(self.angle*self.s.enc_counts/(2*math.pi)))
    def sampled_current(self)->float:
        # Ideal signed 12-bit quantisation, NOT the actual H-bridge CS signal in all switch states.
        sign=1.0 if self.current>=0 else -1.0
        voltage=0.050+0.040*abs(self.current)
        adc=max(0,min(4095,int(round(voltage/3.3*4095))))
        return sign*max(0.0,(adc*3.3/4095-0.050)/0.040)

class Firmware:
    def __init__(self,libpath:Path|None=None):
        libpath=libpath or ROOT/'build/virtual_firmware'/('libbench_core.dylib' if sys.platform=='darwin' else 'libbench_core.so')
        if not libpath.exists():
            subprocess.run([sys.executable,str(ROOT/'tools/build_virtual_firmware.py'),'--no-arm'],check=True)
        self.lib=C.CDLL(str(libpath))
        self.lib.bench_init.argtypes=[C.POINTER(Core)]
        self.lib.bench_cycle.argtypes=[C.POINTER(Core),C.POINTER(Input),C.POINTER(Output)]
        self.core=Core();self.lib.bench_init(C.byref(self.core))
    def cycle(self,ins:Input)->Output:
        out=Output();self.lib.bench_cycle(C.byref(self.core),C.byref(ins),C.byref(out));return out

SCENARIOS=('nominal','encoder_loss','driver_fault','heartbeat_loss','estop','interlock_open',
           'undervoltage','overtemperature','overcurrent','stale_feedback','timing_gap','jam','command_stop',
           'bad_target')

@dataclass
class BenchResult:
    scenario:str
    trace:list[dict]
    final_state:str
    fault:str
    max_abs_current_a:float
    peak_abs_output_speed_rpm:float
    max_abs_pwm:float
    post_fault_enabled_violations:int
    final_angle_deg:float
    coast_deg_after_fault:float|None
    reached_target:bool
    firm_core_source:str='firmware/src/bench_core.c'

    def summary(self):
        return {k:v for k,v in vars(self).items() if k!='trace'}


def run_bench(scenario:str='nominal',*,duration_s:float=4.3,load_scale:float=1.0,
              friction_scale:float=1.0,seed:int=2026,libpath:Path|None=None)->BenchResult:
    if scenario not in SCENARIOS:raise ValueError('unsupported scenario')
    if not (0.25<=load_scale<=3 and 0.3<=friction_scale<=3):raise ValueError('invalid hypothetical variation')
    s=PublishedBench.load()
    # immutable reference spec, varied only explicitly as mathematical scenario assumptions.
    if load_scale!=1 or friction_scale!=1:
        from dataclasses import replace
        s=replace(s,J=s.J*load_scale,friction=s.friction*friction_scale,viscous=s.viscous*friction_scale)
    plant=VirtualMotor(s);fw=Firmware(libpath)
    target=round(0.5*math.pi/(2*math.pi)*s.enc_counts)
    trace=[];latched_time=None;angle_at_fault=None;inhibit_violations=0;reached=False
    fault_start_ms=850
    plc=VirtualPLC() if scenario=='nominal' else None
    dtms=int(round(s.dt*1000))
    if dtms!=1:raise ValueError('firmware compiled for 1ms loop')
    for ms in range(int(duration_s/s.dt)):
        adverse=(ms>=fault_start_ms)
        count=plant.encoder_count()
        cmd=1 if ms==100 else 0
        seq=1
        goal=target
        # A software PLC scan owns the full nominal cycle; status/ack use the real virtual register contract.
        if plc:
            plc.tick(ms,fw.core.state,fw.core.fault,plant.angle*180/math.pi,plant.omega*60/(2*math.pi))
            cmd,goal,seq=plc.output_to_firmware()
        if scenario=='command_stop' and ms==fault_start_ms:cmd=2;seq=2
        if scenario=='bad_target' and ms==100:goal=5000
        if scenario=='encoder_loss' and adverse:count=round(plant.angle*160) # does not matter; encoder_valid=0
        tm=ms+(5 if scenario=='timing_gap' and ms==fault_start_ms else 0)
        sample=ms-30 if scenario=='stale_feedback' and ms>=fault_start_ms and ms>=30 else ms
        ins=Input(
          encoder_count=count,target_count=goal,time_ms=tm,sample_ms=sample,
          command_sequence=seq,command=cmd,
          encoder_good=0 if scenario=='encoder_loss' and adverse else 1,
          driver_good=0 if scenario=='driver_fault' and adverse else 1,
          interlock_good=0 if scenario=='interlock_open' and adverse else 1,
          estop=1 if scenario=='estop' and adverse else 0,
          heartbeat_good=0 if scenario=='heartbeat_loss' and adverse else 1,
          winding_current_a=1.5 if scenario=='overcurrent' and adverse else plant.sampled_current(),
          bus_voltage_v=14.0 if scenario=='undervoltage' and adverse else s.voltage,
          temperature_c=100.0 if scenario=='overtemperature' and adverse else plant.temperature,
        )
        o=fw.cycle(ins)
        if o.state==3:reached=True
        if o.state==4 and latched_time is None:latched_time=ms;angle_at_fault=plant.angle
        if latched_time is not None and o.drive_enable:inhibit_violations+=1
        plant.step(o.normalized_pwm,bool(o.drive_enable),jam=scenario=='jam' and adverse)
        if ms%10==0 or o.fault and (ms==latched_time):
            trace.append({'t_s':round(ms/1000,3),'position_deg':plant.angle*180/math.pi,
              'velocity_rpm':plant.omega*60/(2*math.pi),
              'encoder_counts':count,'winding_current_a':plant.current,
              'temperature_c':plant.temperature,'duty':float(o.normalized_pwm),
              'enabled':int(o.drive_enable),'state':STATE[o.state],
              'fault':FAULT[o.fault],'target_deg':90.0 if ms<2700 or scenario!='nominal' else 0.0})
    coast=(plant.angle-angle_at_fault)*180/math.pi if angle_at_fault is not None else None
    return BenchResult(scenario,trace,STATE[fw.core.state],FAULT[fw.core.fault],
       max(abs(x['winding_current_a']) for x in trace),max(abs(x['velocity_rpm']) for x in trace),
       max(abs(x['duty']) for x in trace),inhibit_violations,
       plant.angle*180/math.pi,coast,reached)


def save_trace(trace:list[dict],path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(trace[0]));w.writeheader();w.writerows(trace)

if __name__=='__main__':
    for scenario in SCENARIOS:
        result=run_bench(scenario)
        print(json.dumps(result.summary()))
