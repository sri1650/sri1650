# Recruiter / interview evidence — verified software claims only

## CV-ready phrasing

- Developed a cross-platform C++20/Python servo-axis software-in-the-loop testbed with a cascaded fixed-step position/velocity/current-control core, explicit motion profiles, anti-windup and software supervision.
- Modelled assumed motor winding dynamics, back-EMF, reflected load inertia and friction; generated reproducible fault, disturbance and parameter-variation tests with traceable outputs.
- Validated the compiled C++ and Python trajectories using a deterministic numerical comparison, CTest/Pytest and automated CI scripts; retained engineering results, fault logs and an offline interactive dashboard.

## What I must not say

- "Developed a production servo drive" — no actual drive hardware.
- "Safety-rated E-stop/STO" — the model illustrates software latches only.
- "Guaranteed 1 kHz real-time control" — 1 kHz refers to simulated fixed-step time, not measured operating-system scheduling.
- "100% reliable" — the 100/100 synthetic sweep is not a statistical reliability estimate.
- "CANopen/CiA 402" — both current protocols are internal virtual formats, not standards-compliant fieldbus stacks.
- "Physical motor tracking within 0.001 mm" — all numbers are assumed-software simulation results.

## Useful interview scenarios

1. Why nested current/velocity/position loops rather than only position PID?
2. How do anti-windup strategies avoid integral accumulation during DC-bus saturation?
3. How does inertial reflection through a gearbox change current sizing?
4. Why should a disabled drive not be equated with an immediate mechanical stop?
5. How were simulation and C++ runtime results independently compared?
6. Why was the original parameter sweep invalid when external disturbances pushed the axis into its hard home stop?
7. Why is an independent encoder/tachometer needed to diagnose encoder freezes reliably?
8. What tests and hardware would be needed to call this a real-time and safety-validated system?

## Additional recruiter-facing evidence: vendor-informed virtual STM32 motor bench

- Simulated a Pololu 24 V brushed encoder gearmotor based on published output speed, current, gearing and 3,200-count quadrature feedback; documented the source, inferred motor R/K_e and assumed L/J/friction.
- Implemented a portable C multirate position/velocity/current control core used in host-simulated closed loop, with Cortex-M4 cross-compile evidence. **Not a real STM32 firmware bring-up.**
- Implemented virtual rotary PLC register and Modbus PDU command sequencing, a 90°/return cycle and automated fault-latching tests.
- Generated repeatable scenario metrics, CSV/JSON, engineering plots and interactive offline dashboard; completed 200 hypothetical inertia/friction variation runs.
- Preserved original C++20/Python SIL project, C++/Python parity evidence and CI. **No physical motor, current-protection circuit, networked PLC or safety-certified stop has been tested.**

Suggested CV wording: **"Developed a vendor-specification-informed motor-control digital twin with a portable C control core cross-compiled for Cortex-M4, simulated rotary PLC/Modbus interfaces, deterministic fault injection and reproducible engineering verification; clearly separated manufacturer data, inferred parameters and synthetic assumptions."**
