# Current State — 28 October 2026

Verified checkpoint: **52 Python tests and 2 CTest executables pass**; the 10-check automated quality gate is PASS. Python software-only modelling, C++20 control, SIL verification and fault evidence are implemented. Run `python tools/quality_gate.py` for the authoritative recorded test and analysis results. No physical motor hardware or real-time system has been used. Current motor, drive, gearbox and load parameters are deliberately assumed.

Key deliverables: `outputs/ENGINEERING_EVIDENCE.md`, `outputs/evidence_summary.json`, `outputs/cpp_sil_trace.csv`, `outputs/cross_language_check.json`, `outputs/servo_control_dashboard.html`, `cpp/include/servo/`, `docs/VERIFICATION_MATRIX.md`, and `config/assumed_axis.json`.

Stop at this verified pre-Work boundary. Next meaningful work: selected MCU/driver firmware, genuine real-time timing, CANopen/EtherCAT, physical motor identification, and PLC/HMI integration.


## Extended hardware-neutral pre-Codex checkpoint — 28 October 2026

- New portable C++ `EmbeddedLoop` and fake `HostPortableAxis`: default disabled, latched timing/reference/estop faults, independent sample timestamps, no automatic re-arm.
- Virtual CiA402-inspired drive-state semantics: no actual CANopen/EtherCAT.
- Python PLC register contract, local-only Modbus/TCP function 03/04/06/16 and socket roundtrip tests: not a production fieldbus.
- Electrical (R/L) and mechanical (J/viscous/Coulomb) synthetic identification with holdout data and excitation checks. No actual measurements.
- Assumed fixed-priority schedulability and native development-host loop compute-time observations: no actual target-WCET or ISR jitter claims.
- Expanded seeded fault-injection campaign and additional automated tests.
- Results: `outputs/extended_prework/results.json`, `REPORT.md`, `synthetic_locked_rotor.csv`, `fault_campaign_expanded.csv`, `identification_fit.png`, plus `outputs/host_loop_benchmark.json`.
- Remaining tasks now require actual motor/drive/MCU selection, MCU peripherals and actual hardware verification. See `docs/NEXT_WORK_BOUNDARY.md`.

### Final extended-prework verification (2026-10-28)

- **71 Python tests passed**; **4/4 C++ CTest executables passed**; host C++ AddressSanitizer/UndefinedBehaviorSanitizer tests passed.
- **12/12 deterministic quality-gate steps passed** with BLAS/OMP numerical threading pinned to one thread for reproducibility.
- 64 seeded synthetic fault runs: 0 software-voltage-inhibit violations after latching, 0 simulated hard-stop contacts, 27.56 mm maximum absolute residual travel; **not physical stopping-distance evidence**.
- Synthetic RL identification: R approximately 1.4992 Ω, L approximately 3.0128 mH, held-out current RMSE approximately 0.0211 A; not observed motor parameters.
- Hypothetical fixed-priority scheduling: 7.05% utilisation under **assumed WCET inputs**; no actual MCU deadline proof.
- Native host benchmark 60,000 cycles recorded compute-time percentiles; development-host timing is not an embedded WCET guarantee.
- Read `docs/NEXT_WORK_BOUNDARY.md` before spending Work/Codex credits. Physical motor/driver/MCU integration and commissioning remain unresolved.

## Final vendor-informed virtual commissioning release — 28 October 2026

The earlier sections document the original linear-axis SIL checkpoint; this section supersedes their project status. A **new independent rotary reference bench** now uses published ST NUCLEO-G474RE / Pololu #4693 / Pololu #2992 specifications plus separately labelled assumed/inferred parameters. No real parts were bought, energised or measured.

- Portable C firmware core compiled for host execution and ARM Cortex-M4 compile-only target. No board HAL peripherals, ADC/PWM/GPIO interrupts, or physical code execution is implied.
- 3,200-count virtual output encoder, averaged virtual motor/gearbox/load, simulated H-bridge, synthetic voltage/current/temperature/drive fault and independent-interlock *logic input*.
- A virtual rotary PLC register image and Modbus PDU packet tests; nominal sequence requests 90°, dwells, then returns to 0°. No real PLC, industrial network or certified safety protocol.
- Fault latch and output inhibition tested on host. Additional travel after disabling in the virtual model does not represent a safe physical stop.
- Fixed-seed ±30% *invented* inertia/friction sensitivity campaign, not equipment reliability statistics.
- Offline replay dashboard, 3 generated plots and machine-readable release results.
- Full project verification includes the original 71 Python tests and 4 C++ suites plus new firmware/PLC regression tests, native C sanitizer build and the virtual release gate.
- Evidence: `outputs/virtual_bench/VIRTUAL_ENGINEERING_RELEASE.md`; acceptance contract: `docs/VIRTUAL_RELEASE_SCOPE.md`.

**Done for virtual-only portfolio scope; not physically validated, not production/servo safety certified.**
