"""Reference cascaded controller, mirrored by C++20 control core for SIL verification."""
from __future__ import annotations
from dataclasses import dataclass
from .parameters import AxisConfig
from .plant import Feedback
from .trajectory import TrajectoryPoint
import math


def clamp(x:float,limit:float)->float:
    return max(-limit,min(limit,x))


@dataclass(frozen=True)
class ControlOutput:
    voltage_v:float
    target_current_a:float
    target_velocity_m_s:float
    valid:bool


class CascadedController:
    """Fixed-rate position P (100 Hz), speed PI (250 Hz), current PI (1 kHz)."""
    def __init__(self, cfg:AxisConfig):
        self.cfg=cfg
        self.tick=0
        self.target_velocity_m_s=0.0
        self.target_current_a=0.0
        self.integrated_speed_error=0.0
        self.integrated_current_error=0.0
        self.maximum_integrator_current_v=cfg.motor.dc_bus_v
        self.maximum_integrator_speed_a=cfg.control.current_limit_a

    def reset(self):
        self.__init__(self.cfg)

    @staticmethod
    def integrate_conditionally(current:float, err:float, dt:float,ki:float,kp:float,ff:float,limit:float,imax:float):
        trial=clamp(current+err*dt,imax)
        u=ff+kp*err+ki*trial
        if (u>limit and err>0) or (u < -limit and err < 0):
            return current
        return trial

    def step(self,reference:TrajectoryPoint,fb:Feedback)->ControlOutput:
        cfg,m,mo,c=self.cfg,self.cfg.mechanics,self.cfg.motor,self.cfg.control
        if not fb.encoder_valid or not fb.drive_ready or fb.emergency_stop:
            self.reset()
            return ControlOutput(0,0,0,False)
        if not all(math.isfinite(v) for v in (reference.position_m,reference.velocity_m_s,reference.acceleration_m_s2,fb.position_m,fb.speed_rad_s,fb.current_a)):
            self.reset(); return ControlOutput(0,0,0,False)
        if self.tick%c.position_loop_divisor==0:
            self.target_velocity_m_s=clamp(reference.velocity_m_s+c.position_kp_per_s*(reference.position_m-fb.position_m),c.max_speed_m_s)
            if fb.position_m < m.travel_min_m + cfg.soft_limit_margin_m:
                self.target_velocity_m_s=max(0,self.target_velocity_m_s)
            if fb.position_m > m.travel_max_m - cfg.soft_limit_margin_m:
                self.target_velocity_m_s=min(0,self.target_velocity_m_s)
        if self.tick%c.velocity_loop_divisor==0:
            omega_ref=self.target_velocity_m_s*m.gear_ratio_motor_to_output/m.pulley_radius_m
            err=omega_ref-fb.speed_rad_s
            # Mechanical force feedforward is nominal; actual friction and external loads vary.
            force_ff=(m.moving_mass_kg*reference.acceleration_m_s2+
                      m.coulomb_friction_coefficient*m.moving_mass_kg*m.gravity_m_s2*math.tanh(self.target_velocity_m_s/m.friction_smoothing_velocity_m_s))
            torque_ff=force_ff*m.pulley_radius_m/(m.gear_ratio_motor_to_output*m.transmission_efficiency)
            i_ff=torque_ff/mo.torque_constant_nm_per_a
            dtv=c.tick_s*c.velocity_loop_divisor
            self.integrated_speed_error=self.integrate_conditionally(self.integrated_speed_error,err,dtv,c.velocity_ki_a_per_rad,c.velocity_kp_a_per_rad_s,i_ff,c.current_limit_a,c.current_limit_a/max(c.velocity_ki_a_per_rad,1e-9))
            self.target_current_a=clamp(i_ff+c.velocity_kp_a_per_rad_s*err+c.velocity_ki_a_per_rad*self.integrated_speed_error,c.current_limit_a)
        err_i=self.target_current_a-fb.current_a
        feedforward=mo.winding_resistance_ohm*self.target_current_a+mo.back_emf_constant_v_per_rad_s*fb.speed_rad_s
        self.integrated_current_error=self.integrate_conditionally(self.integrated_current_error,err_i,c.tick_s,c.current_ki_v_per_a_s,c.current_kp_v_per_a,feedforward,mo.dc_bus_v,self.maximum_integrator_current_v/max(c.current_ki_v_per_a_s,1e-9))
        voltage=clamp(feedforward+c.current_kp_v_per_a*err_i+c.current_ki_v_per_a_s*self.integrated_current_error,mo.dc_bus_v)
        self.tick+=1
        return ControlOutput(voltage,self.target_current_a,self.target_velocity_m_s,True)
