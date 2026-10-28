# Project 4 — Definition of done without hardware

This scope is **complete only as a software-defined digital twin**. A Pololu part-number model and an STM32-target compile do not demonstrate manufacturer accuracy, real controller timing, a hardware safety function, a connected PLC or true device commissioning.

## Evidence tiers

| Tier | What exists | What it does not establish |
|---|---|---|
| Published specification | Manufacturer motor speed/current/gear ratio/encoder counts, driver pin/defaults, MCU family | Actual sample variation or motor identification |
| Inferred values | Approximately 8 Ω motor resistance, 0.02215 V/(rad/s) back-EMF from no-load specification | Verified winding-temperature resistance or measured torque constant |
| Explicit assumptions | L, J, friction, gearbox efficiency, ideal signed current feedback, heat model, 0.75 A software reference limit | Physical power-electronics/current/thermal protection |
| Host-in-the-loop | Same C control core compiled to a host library, executed against a Python plant | Hardware-in-the-loop (HIL) or physical actuator operation |
| ARM code generation | Freestanding Cortex-M4 ELF with core code and a compile-only inert startup | STM32 board clocks, GPIO, timers, ADC, interrupts, linker/flash qualification |
| Virtual PLC | Register image, Modbus function-code packet tests, sequenced 90° and return cycle | An IEC 61131-3 PLC, industrial SCADA network or real Modbus equipment |
| Synthetic fault campaign | Watchdog, encoder, driver, overtemperature, overcurrent, estop signal and interlock signal simulated | Certified emergency stop, independent safety circuit or known physical coast distance |
| Reproducible outputs | Deterministic tests, CSV, JSON, charts, offline HMI replay | Live HMI connected to machinery |

## Why this is not a universal servo drive

This bench targets a *brushed DC gearmotor* with encoder and PWM H-bridge. It is not a three-phase BLDC/PMSM field-oriented controller. Actual Pololu #2992 `CS` output is invalid in some PWM/braking conditions, so a true 1 kHz bidirectional current loop cannot simply assume the virtual signed-sensor model. Its default 30 A chop is also incompatible with protecting a small motor whose published extrapolated stall current is 3 A. Real implementation would require independently engineered lower current-limit electronics, isolation/stop design, safe signal levels and detailed electrical inspection.

The original Project 3 8 kg belt-drive plant and its motor torque/current values are a *different historical SIL model*. This new gearmotor bench does not validate that load, mount or motor selection.

## Definition of software-only completion

- [x] Manufacturer facts and model assumptions individually traceable
- [x] Host-executed C controller, with Arm Cortex-M4 code generation where toolchain supports it
- [x] Virtual quadrature encoder, current feedback, PWM/driver gate, motor dynamics, thermal model
- [x] PLC command register semantics and virtual two-move machine cycle
- [x] Deterministic fault/latching tests and manually triggered stop/rearm test
- [x] 200 fixed-seed assumed-variation scenarios and machine-readable results
- [x] Offline interactive dashboard and comparison charts
- [x] CI, original project tests, simulation evidence and source published to GitHub

**The last list is not a physical-commissioning acceptance checklist.** No such checklist can pass without measurements. All virtual protection and mechanical outcomes are model assumptions, not guaranteed physical behaviour.

## Future option, not a blocker for this scope

If hardware becomes available, select the safe bench architecture and a different current-sense/limit strategy, integrate actual STM32CubeG4 drivers, measure real motor constants, test ADC and encoder polarity, PWM output, interrupt jitter, drive fault input, external independent stop, coasting and thermal behaviour, then repeat the verification with actual measured traces.
