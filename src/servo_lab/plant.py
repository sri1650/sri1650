"""Small-signal DC/BLDC-equivalent servo plant, explicitly not switching-level FOC."""
from __future__ import annotations
from dataclasses import dataclass
import math
import random
from .parameters import AxisConfig


@dataclass(frozen=True)
class PlantState:
    motor_angle_rad: float = 0.0
    motor_speed_rad_s: float = 0.0
    winding_current_a: float = 0.0


class MotorPlant:
    def __init__(self, config: AxisConfig, position_m: float = 0.0):
        self.config = config
        m=config.mechanics
        if not (m.travel_min_m <= position_m <= m.travel_max_m):
            raise ValueError("initial position outside travel")
        self.state = PlantState(motor_angle_rad=position_m*m.gear_ratio_motor_to_output/m.pulley_radius_m)
        self.hard_stop_contacts=0

    @property
    def position_m(self)->float:
        m=self.config.mechanics
        return self.state.motor_angle_rad*m.pulley_radius_m/m.gear_ratio_motor_to_output

    @property
    def speed_m_s(self)->float:
        m=self.config.mechanics
        return self.state.motor_speed_rad_s*m.pulley_radius_m/m.gear_ratio_motor_to_output

    def derivatives(self, s: PlantState, voltage_v: float, disturbance_force_n:float=0.0) -> PlantState:
        m, mo = self.config.mechanics, self.config.motor
        angular_speed=s.motor_speed_rad_s
        linear_speed=angular_speed*m.pulley_radius_m/m.gear_ratio_motor_to_output
        friction_force=m.coulomb_friction_coefficient*m.moving_mass_kg*m.gravity_m_s2 * math.tanh(linear_speed/m.friction_smoothing_velocity_m_s)
        reflected_tau=(friction_force+m.external_disturbance_force_n+disturbance_force_n)*m.pulley_radius_m/(m.gear_ratio_motor_to_output*m.transmission_efficiency)
        j_eq=mo.rotor_inertia_kg_m2+m.moving_mass_kg*m.pulley_radius_m**2/(m.gear_ratio_motor_to_output**2*m.transmission_efficiency)
        d_angle=angular_speed
        d_speed=(mo.torque_constant_nm_per_a*s.winding_current_a - mo.viscous_friction_nm_per_rad_s*angular_speed - reflected_tau)/j_eq
        d_current=(voltage_v - mo.winding_resistance_ohm*s.winding_current_a - mo.back_emf_constant_v_per_rad_s*angular_speed)/mo.winding_inductance_h
        return PlantState(d_angle,d_speed,d_current)

    def step(self, voltage_v:float, dt:float, *, disturbance_force_n:float=0.0,bus_voltage_v:float|None=None, drive_enabled:bool=True)->PlantState:
        if dt <= 0 or not math.isfinite(dt):
            raise ValueError("positive finite timestep required")
        m,mo=self.config.mechanics,self.config.motor
        bus=mo.dc_bus_v if bus_voltage_v is None else bus_voltage_v
        if bus<0 or not math.isfinite(bus):
            raise ValueError("invalid bus voltage")
        u=max(-bus,min(bus,voltage_v)) if drive_enabled else 0.0
        if not drive_enabled:
            # High-impedance idealisation: no intentional braking torque and current instantaneously falls to zero.
            # Neither STO nor mechanical stopping is modelled.
            self.state=PlantState(self.state.motor_angle_rad,self.state.motor_speed_rad_s,0.0)
        s=self.state
        def add(a:PlantState,b:PlantState,f:float):
            return PlantState(a.motor_angle_rad+f*b.motor_angle_rad,a.motor_speed_rad_s+f*b.motor_speed_rad_s,a.winding_current_a+f*b.winding_current_a)
        k1=self.derivatives(s,u,disturbance_force_n)
        k2=self.derivatives(add(s,k1,dt/2),u,disturbance_force_n)
        k3=self.derivatives(add(s,k2,dt/2),u,disturbance_force_n)
        k4=self.derivatives(add(s,k3,dt),u,disturbance_force_n)
        nxt=PlantState(*(
            getattr(s,k)+dt/6*(getattr(k1,k)+2*getattr(k2,k)+2*getattr(k3,k)+getattr(k4,k))
            for k in ("motor_angle_rad","motor_speed_rad_s","winding_current_a")
        ))
        if not drive_enabled:
            # Apply only inertia/friction to speed; electrical coupling is open.
            # Explicit RK4 mechanical step with i=0, removing regenerative short-circuit braking.
            b=mo.viscous_friction_nm_per_rad_s
            j=mo.rotor_inertia_kg_m2+m.moving_mass_kg*m.pulley_radius_m**2/(m.gear_ratio_motor_to_output**2*m.transmission_efficiency)
            omega=s.motor_speed_rad_s
            def f(w):
                v=w*m.pulley_radius_m/m.gear_ratio_motor_to_output
                F=m.coulomb_friction_coefficient*m.moving_mass_kg*m.gravity_m_s2*math.tanh(v/m.friction_smoothing_velocity_m_s)
                tau=(F+m.external_disturbance_force_n+disturbance_force_n)*m.pulley_radius_m/(m.gear_ratio_motor_to_output*m.transmission_efficiency)
                return (-b*w-tau)/j
            a1=f(omega);a2=f(omega+0.5*dt*a1);a3=f(omega+0.5*dt*a2);a4=f(omega+dt*a3)
            omega_new=omega+dt*(a1+2*a2+2*a3+a4)/6
            nxt=PlantState(s.motor_angle_rad+dt*0.5*(omega+omega_new),omega_new,0.0)
        x=nxt.motor_angle_rad*m.pulley_radius_m/m.gear_ratio_motor_to_output
        if x < m.travel_min_m or x > m.travel_max_m:
            self.hard_stop_contacts+=1
            x=max(m.travel_min_m,min(m.travel_max_m,x))
            nxt=PlantState(x*m.gear_ratio_motor_to_output/m.pulley_radius_m,0.0,nxt.winding_current_a)
        if not all(math.isfinite(v) for v in (nxt.motor_angle_rad,nxt.motor_speed_rad_s,nxt.winding_current_a)):
            raise FloatingPointError("non-finite plant state")
        self.state=nxt
        return nxt


@dataclass(frozen=True)
class Feedback:
    position_m:float
    speed_rad_s:float
    current_a:float
    timestamp_s:float
    encoder_valid:bool=True
    drive_ready:bool=True
    bus_voltage_v:float=24.0
    winding_temperature_c:float=35.0
    emergency_stop:bool=False


class VirtualEncoder:
    def __init__(self,config:AxisConfig):
        self._cfg=config
        self._rng=random.Random(config.encoder_seed)
        self._freeze_count:int|None=None

    def sample(self,theta_rad:float, *,freeze:bool=False)->float:
        count=round(theta_rad*self._cfg.encoder_counts_per_rev/(2*math.pi))
        if freeze:
            if self._freeze_count is None:
                self._freeze_count=count
            count=self._freeze_count
        else:
            self._freeze_count=None
        x=count*(2*math.pi/self._cfg.encoder_counts_per_rev)*self._cfg.mechanics.pulley_radius_m/self._cfg.mechanics.gear_ratio_motor_to_output
        return x+self._rng.gauss(0,self._cfg.feedback_noise_position_std_m)
