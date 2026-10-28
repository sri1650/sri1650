# Remaining Work/Codex mission — narrow and hardware dependent

## Work already completed without Work/Codex

- Explicit assumptions and CAD-axis provenance; averaged electromechanical SIL plant.
- Multirate P/PI/PI C++ and Python controllers, trajectory generation and virtual sensors.
- Software supervisor, watchdog, fault latch and drive-disable residual-travel measurements.
- Cross-language SIL trace comparison, expanded software fault campaign, CLI reports and dashboards.
- Portable C++ `EmbeddedLoop` and `HostPortableAxis` with safe boot defaults, timestamps and host fake.
- Virtual CiA-402-style drive states, fake PLC register image and **localhost-only** Modbus/TCP exercise.
- Synthetic RL and equivalent inertia/friction parameter identification with held-out error and insufficient-excitation checks.
- Assumed fixed-priority task response-time analysis and development-host C++ cycle microbenchmark.
- Automated code verification with one quality-gate command.

## First action in Work

1. Recover the latest project ZIP/Git bundle and read `AGENTS.md`, `docs/CURRENT_STATE.md`, `docs/EMBEDDED_INTERFACE_SPEC.md` and this document.
2. Run `python tools/quality_gate.py`; establish the baseline.
3. Do **not** regenerate passing Python/C++ modules, dashboards, plots or synthetic data without a relevant failing test.
4. Reference bench hardware has now been selected in `docs/SELECTED_BENCH_HARDWARE.md` (STM32 NUCLEO-G474RE + Pololu #4693 motor/encoder + Pololu #2992 driver). It has NOT been obtained or tested. Before vendor-specific code or energisation, verify pin mapping, interlock, signal levels, current limiting, motor/gearbox limitations and actual axis coupling; do not assume the existing SIL motor parameters match.

## High-value tasks reserved for Work/Codex

1. Vendor specific MCU/RTOS build and compile-only target once hardware is chosen.
2. Actual peripheral HAL (timer/ADC/PWM/encoder/GPIO, calibration and sensor timestamps).
3. Real CANopen/CiA402 or EtherCAT/PLC stack with physical-drive integration.
4. Measured target scheduling, worst-case timing, noise, thermal and watchdog behaviour.
5. HIL rig and actual measured motor-ID/closed-loop controller tests, after independent safety review.
6. PLC/HMI integration for the complete indexing/inspection cell after servo hardware is verified.

A cloud-only Work run cannot establish real motor performance or hardware safety. Keep tasks labelled **blocked by selected hardware**, not `complete`, until genuine test evidence exists.

## Credit discipline

One bounded task at a time; smallest relevant file set; tool-driven verification; at most two identical repair attempts before a blocker report; use higher reasoning only for numerical/control/RTOS or real fieldbus failures; checkpoint each verified change; no repeated redesign of completed software.
