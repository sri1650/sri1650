# START HERE — Project 4

1. Read `README.md` and `docs/PLANT_AND_CONTROL_ASSUMPTIONS.md`.
2. Run `python tools/quality_gate.py` to reproduce the expanded 16-stage software verification gate.
3. Open `outputs/servo_control_dashboard.html` to explore the simulated run interactively.
4. Read `outputs/ENGINEERING_EVIDENCE.md` for actual numerical results and caveats.
5. If continuing in Work/Codex, provide `WORK_HANDOFF.md`, `docs/CURRENT_STATE.md`, `AGENTS.md` and the verified archive. Do **not** restart or rewrite the control core.
6. Reference hardware was selected in `docs/SELECTED_BENCH_HARDWARE.md`, but **no hardware was bought, wired or tested**. Do not energise a motor or infer safe stopping distances from this simulation.


## Extended pre-Codex status

1. Run `PYTHONPATH=src python tools/quality_gate.py` for the new 12-stage gate.
2. Open `outputs/extended_prework/REPORT.md` and `outputs/extended_prework/identification_fit.png`.
3. Read `docs/EMBEDDED_INTERFACE_SPEC.md` for the HAL, virtual PLC and timing contracts.
4. Read `docs/ENGINEERING_RISK_REGISTER.md` for unresolved physical risks.
5. Read `docs/NEXT_WORK_BOUNDARY.md` before starting Work/Codex.

No new software installations or user accounts are needed to review the portable C++/Python evidence. Physical-motor work requires a selected drive, MCU and an independently reviewed safe test setup.

## FINAL SOFTWARE-ONLY VIRTUAL RELEASE (28 October 2026)

1. The full bench is now closed for **software-only validation**. It combines the original 8 kg illustrative linear SIL with a separate, manufacturer-informed Pololu brushed gearmotor rotary digital twin.
2. Run `python tools/quality_gate.py` (16 checks, includes original tests, ARM cross-build where possible, C host sanitizer tests and full virtual HMI/evidence generation).
3. Open `outputs/virtual_bench/virtual_commissioning_dashboard.html` in a browser. The controls replay a stored simulation, not physical hardware.
4. Read `outputs/virtual_bench/VIRTUAL_ENGINEERING_RELEASE.md`, `docs/VIRTUAL_RELEASE_SCOPE.md` and `docs/VIRTUAL_INTERFACE_AND_WIRING_REVIEW.md`.
5. The ARM ELF is **code-generation evidence only**; firmware peripheral drivers, current sense in all switching states, real-time target jitter, a real PLC and physical safety/commissioning remain unverified. This is not a flashable production package.
6. No purchase, account or additional Work/Codex session is required to run the virtual simulation.
