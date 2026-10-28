# START HERE — Project 4

1. Read `README.md` and `docs/PLANT_AND_CONTROL_ASSUMPTIONS.md`.
2. Run `python tools/quality_gate.py` to reproduce 10 software verification steps.
3. Open `outputs/servo_control_dashboard.html` to explore the simulated run interactively.
4. Read `outputs/ENGINEERING_EVIDENCE.md` for actual numerical results and caveats.
5. If continuing in Work/Codex, provide `WORK_HANDOFF.md`, `docs/CURRENT_STATE.md`, `AGENTS.md` and the verified archive. Do **not** restart or rewrite the control core.
6. No hardware has been selected. Do not energise a motor or infer safe stopping distances from this simulation.


## Extended pre-Codex status

1. Run `PYTHONPATH=src python tools/quality_gate.py` for the new 12-stage gate.
2. Open `outputs/extended_prework/REPORT.md` and `outputs/extended_prework/identification_fit.png`.
3. Read `docs/EMBEDDED_INTERFACE_SPEC.md` for the HAL, virtual PLC and timing contracts.
4. Read `docs/ENGINEERING_RISK_REGISTER.md` for unresolved physical risks.
5. Read `docs/NEXT_WORK_BOUNDARY.md` before starting Work/Codex.

No new software installations or user accounts are needed to review the portable C++/Python evidence. Physical-motor work requires a selected drive, MCU and an independently reviewed safe test setup.
