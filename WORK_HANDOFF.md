# Low-credit continuation prompt — Industrial Servo Motion Control

Continue the existing `industrial-servo-motion-control` source project; **do not start over**.

## Baseline to check

1. Read `README.md`, `AGENTS.md`, `docs/CURRENT_STATE.md`, `docs/WORK_ROADMAP.md`, and `config/assumed_axis.json`.
2. Run `python tools/quality_gate.py`. It checks Python tests, compileall, C++ build/CTest, SIL simulation, numerical parity, parameter-variation data and offline dashboard.
3. Preserve the verified C++/Python core, test vectors, data and simulation methods.

## Limit Work/Codex strictly to

- Real embedded target toolchain and low-level MCU hardware abstraction.
- Correctly identified power electronics and PWM/FOC **only if an actual compatible drive is selected**.
- Measured real-time timing/deadline performance on a target (or clearly labelled emulation where hardware absent).
- A specific, selected CANopen CiA 402 or EtherCAT stack and industrial drive interface.
- Hardware-in-the-loop test adapters, with actual physical tests deferred until physical motor/driver available.
- PLC/HMI interface only once motor controller data model and transport protocol are stable.

These later stages require real hardware and/or external software. Do not fabricate 'successful HIL', 'CANopen certified', safety-rated functions, or commissioning evidence.

## Credit policy

- Work one dependency-ready, bounded task at a time.
- Read task + current state + only 3–8 relevant files.
- Use standard economical model and low reasoning for ordinary C++, build scripts, tests and documentation.
- Switch to medium only for numerical control issues, RTOS timing, fieldbus state-model integration or harder cross-tool failures.
- Run targeted compile/tests before full suite; do not rerun massive datasets without changes.
- Maximum two repair attempts for one failure; then put exact command, stderr and relevant context in `BLOCKED.md` and escalate only that blocker.
- Commit only verified changes and update `docs/CURRENT_STATE.md` concisely.
- No unsolicited redesign, rewrites, bulk refactors or unrelated frameworks.

## Required final report

Repo link/commit; C++ and Python test counts; actual target/emulator identified; runtime timing evidence; real vs simulated bus behavior; fault/stop evidence; physical tests not executed; remaining limitations.


## IMPORTANT — updated pre-Codex handoff (28 October 2026)

The low-credit work scope has been reduced again: a native C++ hardware-neutral loop and HAL, virtual CiA402 drive states, local Modbus/TCP test transport, synthetic parameter identification, fixed-priority scheduling analysis and expanded SIL fault campaigns are now implemented. **Read `docs/NEXT_WORK_BOUNDARY.md` first.**

Run `python tools/quality_gate.py` to verify the new baseline. Do not recreate anything listed as completed there. With no selected MCU/motor/driver and no physical bench, the correct next step is to request only required datasheets and hardware access before attempting a real embedded driver; never claim target real-time timing or motor safety from software-only tests.

## Virtual-only release complete; avoid unnecessary Codex continuation (28 October 2026)

The user explicitly chose **not to buy hardware** and requested completion entirely through official component data and assumptions. This scope is now implemented and tested. There is no need to start another Codex session to rewrite the simulator or create a hypothetical hardware commissioning claim. Only if the user later opts for real hardware should firmware-specific STM32 clock/peripheral/HAL support, actual fieldbus and electrical protection be undertaken, under a competent review and with measured device data. See `docs/VIRTUAL_RELEASE_SCOPE.md` and `outputs/virtual_bench/VIRTUAL_ENGINEERING_RELEASE.md`.
