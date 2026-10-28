"""Explicit assumed parameters, units and preliminary motor sizing."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import math

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "assumed_axis.json"


@dataclass(frozen=True)
class Mechanics:
    moving_mass_kg: float
    horizontal_acceleration_m_s2: float
    coulomb_friction_coefficient: float
    pulley_radius_m: float
    gear_ratio_motor_to_output: float
    transmission_efficiency: float
    travel_min_m: float
    travel_max_m: float
    gravity_m_s2: float = 9.81
    external_disturbance_force_n: float = 0.0
    friction_smoothing_velocity_m_s: float = 0.001

    def __post_init__(self):
        if min(self.moving_mass_kg, self.pulley_radius_m, self.gear_ratio_motor_to_output, self.gravity_m_s2, self.friction_smoothing_velocity_m_s) <= 0:
            raise ValueError("positive mass, pulley radius, gearing, gravity and smoothing required")
        if not 0 < self.transmission_efficiency <= 1:
            raise ValueError("transmission efficiency must be in (0,1]")
        if self.travel_min_m >= self.travel_max_m or self.coulomb_friction_coefficient < 0:
            raise ValueError("invalid travel range/friction")


@dataclass(frozen=True)
class Motor:
    dc_bus_v: float
    winding_resistance_ohm: float
    winding_inductance_h: float
    torque_constant_nm_per_a: float
    back_emf_constant_v_per_rad_s: float
    rotor_inertia_kg_m2: float
    viscous_friction_nm_per_rad_s: float
    continuous_torque_nm: float
    continuous_current_a: float
    peak_current_a: float

    def __post_init__(self):
        vals = (self.dc_bus_v,self.winding_resistance_ohm,self.winding_inductance_h,
                self.torque_constant_nm_per_a,self.back_emf_constant_v_per_rad_s,
                self.rotor_inertia_kg_m2,self.continuous_torque_nm,
                self.continuous_current_a,self.peak_current_a)
        if min(vals) <= 0 or self.viscous_friction_nm_per_rad_s < 0:
            raise ValueError("invalid motor parameters")
        if self.continuous_current_a > self.peak_current_a:
            raise ValueError("continuous current exceeds peak current")


@dataclass(frozen=True)
class Control:
    tick_s: float
    position_loop_divisor: int
    velocity_loop_divisor: int
    position_kp_per_s: float
    velocity_kp_a_per_rad_s: float
    velocity_ki_a_per_rad: float
    current_kp_v_per_a: float
    current_ki_v_per_a_s: float
    current_limit_a: float
    max_speed_m_s: float
    max_acceleration_m_s2: float
    max_jerk_m_s3: float
    target_position_m: float
    target_settle_error_m: float
    target_settle_velocity_m_s: float
    hold_duration_s: float

    def __post_init__(self):
        positive = (self.tick_s,self.position_loop_divisor,self.velocity_loop_divisor,
                    self.current_limit_a,self.max_speed_m_s,self.max_acceleration_m_s2,
                    self.max_jerk_m_s3,self.target_settle_error_m,
                    self.target_settle_velocity_m_s,self.hold_duration_s)
        if min(positive) <= 0:
            raise ValueError("invalid positive control values")
        if any(x < 0 for x in (self.position_kp_per_s,self.velocity_kp_a_per_rad_s,
                              self.velocity_ki_a_per_rad,self.current_kp_v_per_a,
                              self.current_ki_v_per_a_s)):
            raise ValueError("controller gains cannot be negative")
        if int(self.position_loop_divisor) != self.position_loop_divisor or int(self.velocity_loop_divisor) != self.velocity_loop_divisor:
            raise ValueError("divisors must be integers")


@dataclass(frozen=True)
class AxisConfig:
    mechanics: Mechanics
    motor: Motor
    control: Control
    encoder_counts_per_rev: int
    encoder_seed: int
    feedback_noise_position_std_m: float
    feedback_noise_current_std_a: float
    command_timeout_s: float
    soft_limit_margin_m: float
    overtemperature_c: float
    min_bus_v: float
    sensor_stale_limit_s: float
    status: str


def load_config(path: str | Path = DEFAULT_CONFIG) -> AxisConfig:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    m=Mechanics(**data["mechanics"])
    motor=Motor(**data["motor"])
    c=Control(**data["control"])
    e=data["encoder"]
    sup=data["supervision"]
    if e["counts_per_motor_rev"]<=0 or e["feedback_noise_position_std_m"]<0 or e["feedback_noise_current_std_a"]<0:
        raise ValueError("invalid encoder")
    if sup["command_timeout_s"]<=0 or sup["sensor_stale_limit_s"]<=0 or sup["soft_limit_margin_m"]<0:
        raise ValueError("invalid supervision")
    if c.current_limit_a > motor.peak_current_a:
        raise ValueError("control current limit > motor peak")
    return AxisConfig(m,motor,c,e["counts_per_motor_rev"],e["seed"],
                      e["feedback_noise_position_std_m"],e["feedback_noise_current_std_a"],
                      sup["command_timeout_s"],sup["soft_limit_margin_m"],
                      sup["overtemperature_c"],sup["min_bus_v"],sup["sensor_stale_limit_s"],data["status"])


def motor_sizing(config: AxisConfig) -> dict[str, float]:
    m, mo, c = config.mechanics, config.motor, config.control
    force_acc = m.moving_mass_kg * m.horizontal_acceleration_m_s2
    force_friction = m.coulomb_friction_coefficient * m.moving_mass_kg * m.gravity_m_s2
    force_total = force_acc+force_friction
    torque_shaft = force_total * m.pulley_radius_m/(m.gear_ratio_motor_to_output * m.transmission_efficiency)
    omega_at_speed = c.max_speed_m_s*m.gear_ratio_motor_to_output/m.pulley_radius_m
    current_demand = torque_shaft/mo.torque_constant_nm_per_a
    voltage_at_speed = mo.winding_resistance_ohm * current_demand + mo.back_emf_constant_v_per_rad_s * omega_at_speed
    j_reflected = m.moving_mass_kg*m.pulley_radius_m**2/(m.gear_ratio_motor_to_output**2*m.transmission_efficiency)
    return {
        "assumed_accelerating_force_n":force_acc,
        "assumed_friction_force_n":force_friction,
        "assumed_total_axis_force_n":force_total,
        "shaft_torque_nm":torque_shaft,
        "current_for_force_a":current_demand,
        "motor_speed_rad_s_at_max_axis_speed":omega_at_speed,
        "approx_voltage_needed_v":voltage_at_speed,
        "reflected_mass_inertia_kg_m2":j_reflected,
        "total_reflected_inertia_kg_m2":j_reflected+mo.rotor_inertia_kg_m2,
        "current_headroom_a":mo.continuous_current_a-current_demand,
        "voltage_headroom_v":mo.dc_bus_v-voltage_at_speed
    }
