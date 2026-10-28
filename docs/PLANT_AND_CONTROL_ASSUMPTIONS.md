# Plant and controller equations (educational, assumed)

## Source and provenance

`assets/cad_axis_reference.json` is copied byte-for-byte from Project 3's `config/design.json` in `Mechatronics_CAE_Extreme_PreWork_2026-10-28.zip`. Relevant values: moving mass 8 kg; 20 mm pulley radius; friction coefficient 0.12; transmission efficiency 0.85; design speed 0.35 m/s; candidate continuous shaft torque 1.2 N·m. The original bracket load cases are unrelated to a selected drive and are not proof of motor capability.

The selected 3:1 gearbox, 24 V DC motor-equivalent constants, R, L, Kt, Ke, rotor inertia, encoder resolution and controller gains are **new model assumptions**. They are not extracted from a real motor or drive datasheet.

## Mechanical/electrical model

For motor angular speed ω, rotor angle θ and winding current i:

- Axis position: x = θ r / G; speed v = ω r / G
- Reflected moving inertia: J_load = m r²/(G² η)
- Effective inertia: J_eff = J_motor + J_load
- Resistive load: F = μmg tanh(v/v_smoothing) + F_external
- Shaft load torque: τ_load = F r /(G η)
- Motor torque: τ_m = Kt i
- Mechanical dynamics: J_eff dω/dt = τ_m − Bω − τ_load
- Winding dynamics: L di/dt = u − Ri − Keω

The friction model is a smooth Coulomb approximation, **not a validated static friction or LuGre model**. The efficiency factor is applied consistently as a simple worst-direction approximation but is not a fully bidirectional regenerative gearbox model. No belt compliance, backlash, structural modes or switching-level FOC are represented.

The Python plant uses RK4 with an assumed 1 ms fixed simulation step. The C++ demonstrator uses an independent simplified fixed-step Euler plant, allowing an approximate cross-language trajectory check.

When the supervisor removes drive enable, the Python plant models ideal instantaneous loss of winding torque and a high-impedance coast; that is *not* a guarantee for a physical drive. Actual safe stopping must consider braking circuits, backdrivability, motor characteristics, braking resistors, inertia and safety functions.

## Controller

The software uses a nested loop hierarchy:

- Position loop (100 Hz): v_ref + Kp_position (x_ref−x), clamped to v_max
- Velocity loop (250 Hz): I_ff + Kp_velocity (ω_ref−ω) + Ki_velocity ∫error dt, clamped to I_max
- Current loop (1 kHz): R I_ref + Keω + Kp_current (I_ref−i) + Ki_current∫error dt, clamped to ±V_bus

Integrators are conditionally updated when output saturation and error signs would otherwise increase windup. Gains are preliminary and tuned for this numerical model only.

The quintic rest-to-rest trajectory uses:

x(t)=x0+Δx(10s³−15s⁴+6s⁵), s=t/T.

T is computed from maximum analytic velocity (1.875 Δ/T), acceleration (~5.7735 Δ/T²), and jerk (60 Δ/T³). We verify bounds numerically in regression tests.

## What needs real hardware data

Motor: torque/speed curve, current and thermal ratings, winding resistance/inductance, Kt/Ke, rotor inertia, encoder type, driver protocol, supply, load cycle, EMC and motor mounting drawings.

Mechanics: mass/inertia, actual friction and transmission ratio, belt/gear efficiency and compliance, lead/ball screw or pulley drive, stroke, guide friction, gravity axis orientation, brake and limit stop.

Control: measured sample jitter, sensing noise, ADC quantisation, current waveform, saturation, power-stage nonlinearity and thermal/voltage variations.
