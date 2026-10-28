# Industrial Servo Motion Control — Engineering Evidence

**Validation:** deterministic software-in-the-loop model only. Motor, transmission, load, friction, bus voltage, encoder and controller gains are assumptions.

## Assumed motor sizing

| Metric | Calculated value |
|---|---:|
| assumed_accelerating_force_n | 8.000000 |
| assumed_friction_force_n | 9.417600 |
| assumed_total_axis_force_n | 17.417600 |
| shaft_torque_nm | 0.136609 |
| current_for_force_a | 0.853804 |
| motor_speed_rad_s_at_max_axis_speed | 52.500000 |
| approx_voltage_needed_v | 9.680706 |
| reflected_mass_inertia_kg_m2 | 0.000418 |
| total_reflected_inertia_kg_m2 | 0.000568 |
| current_headroom_a | 6.646196 |
| voltage_headroom_v | 14.319294 |

## 100 mm nominal trajectory

- Quintic commanded motion duration: **0.909 s**
- Final position error: **0.0011 mm**
- Maximum tracking error during move: **0.3117 mm**
- Peak simulated winding current: **0.917 A**
- Peak simulated axis speed: **0.208 m/s**
- Final controller/supervisor mode: **ENABLED**

## Parameter-variation campaign (assumed distributions)

- Samples: **100**, deterministic seed **2026**
- Passes under deliberately chosen surrogate screen: **100/100 (100.0%)**
- p95 peak tracking error: **0.3192 mm**
- Highest simulated current: **1.324 A**

The percentage is **not** motor reliability, a real tolerance distribution, or a field-failure rate.

## Injected faults: software response and residual travel

| Fault | First detected at (s) | Additional travel after fault (mm) | Final supervisor mode |
|---|---:|---:|---|
| encoder_invalid | 0.350 | 19.139 | FAULT |
| undervoltage | 0.350 | 19.139 | FAULT |
| overtemperature | 0.350 | 19.139 | FAULT |
| sensor_stale | 0.350 | 19.139 | FAULT |
| emergency_stop | 0.350 | 19.139 | ESTOP |
| heartbeat_loss | 0.501 | 22.722 | FAULT |

The coast model treats disabling the drive as ideal high impedance, instantaneously zero current and simplified Coulomb/viscous friction. It is **not** a validated stopping-distance estimate. Independent hardwired emergency stop / STO, limit switches, brake and risk assessment would be required for hardware.

## Deliberately excluded from verification

- Real motor identification, thermal limits, torque ripple, switching losses, real drive current limits, electromagnetic compatibility or encoder accuracy.
- Real CAN/CANopen, fieldbus latency, RTOS timing, physical homing or certified functional safety.
- Physical inertia, belt compliance, backlash, mechanical resonance, hard-stop contact response or real drivetrain coupling.

## Outputs

- `nominal_axis_trace.csv` and `disturbance_axis_trace.csv`
- `assumed_parameter_sweep.csv`
- `plots/tracking_position.png`, `plots/tracking_error.png`, `plots/drive_command.png`, `plots/fault_stop_travel.png`
- `evidence_summary.json`
