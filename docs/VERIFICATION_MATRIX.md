# Verification matrix

| Requirement | Test / evidence | Scope | Remaining |
|---|---|---|---|
| CAD assumptions preserved | `test_cad_reference_physical_axis_values` | unit-tested source provenance | Motor and drive are not selected |
| Physical parameter validation | config dataclass tests | software input checks | Measure all parameters |
| Winding electrical model | `test_electrical_derivative_uses_rl_and_back_emf` | numerical formula | Bench RL/current validation |
| Transmission inertia | motor sizing calculation tests | analytical consistency | Actual inertia measurement |
| Smooth trajectory and bounds | quintic tests over 5001 samples | mathematical | Physical motion profile commissioning |
| C++20 control compilation | CMake + CTest | compile/unit tested | Embedded target, RTOS, FOC |
| Cascade saturation | Python and C++ controller tests | software | Physical drive limit verification |
| Encoder quantisation | virtual sensor tests | synthetic | Real encoder timing/noise/faults |
| Nominal and 6 N disturbance | traced 2.5 s SIL runs | ODE simulator only | Measured load-response validation |
| Software fault latch | software supervisor tests | deterministic only | Hardware STO/estop design |
| Watchdog timeout | Python + C++ tests | simulated logical time | Clock/deadline and bus fault measurement |
| Virtual protocol | CRC and replay tests | internal test protocol | Real CANopen/CiA 402 or EtherCAT |
| Numerical consistency | C++/Python reference trace comparison | two simplified digital models | Independent external reference or actual rig |
| Assumed robustness screen | fixed 100-seed sweep | synthetic distributions | Distribution identification and statistical verification |
| Stopping distance | position after simulated drive-disable | simplified open-circuit model | Mechanical brake/stop validation |

## Acceptance and stop rules

- All automated tests and C++ checks pass.
- Nominal final position error <0.2 mm and peak tracking error <2 mm in this assumed model.
- No output exceeds the assumed DC-bus voltage or controller current-command limit.
- 100-seed nominal variation campaign is deterministic; no hard-stop contact for the *mid-stroke* sampling setup.
- Fault input disables the software controller and latches a reason. The remaining coast travel is explicitly reported, not hidden.
- Never use this software to energise a physical motor without a separate safety review, independent interlocks and appropriate commissioning procedures.

**Caution:** a positive SIL test is not proof of a safe real-time motor controller, compliance with ISO 13849, IEC 61508, IEC 61800-5-2 or other safety standards.


## Extended pre-Codex checks (28 October 2026)

| Requirement | Verification | Status | Validation boundary |
|---|---|---|---|
| Portable loop defaults to disabled | C++ `servo_embedded_contract_test`, `servo_hal_test` | PASS | host fake, not MCU |
| Deadline-gap, NaN and time-backward faults latch | C++ runtime tests | PASS | logical time only |
| Independent sensor acquisition timestamp | C++ HAL stale-sensor test | PASS | test fake, not ADC/encoder hardware |
| Observed external interlock inhibits output | C++ HAL test | PASS | not a safety-rated interlock implementation |
| Virtual drive enable/fault/quick-stop semantics | C++ `VirtualDrive402` test | PASS | no CANopen/EtherCAT network |
| Virtual PLC registers + 16-bit/32-bit conversion | Python `test_plc_contract.py` | PASS | interface model only |
| Localhost-only Modbus/TCP register exchange | Python socket test, write validation and 1,200 malformed packets | PASS | no production network security |
| Synthetic RL identification and holdout | `test_identification.py`, retained CSV | PASS | assumed electrical parameters |
| Synthetic equivalent inertia/friction fit | `test_identification.py` | PASS | assumed Kt and idealised mechanics |
| Fixed-priority response-time analysis | `test_schedulability.py` | PASS | WCET inputs are hypothetical |
| Native host compute-time microbenchmark | `servo_host_cycle_benchmark` | PASS | not interrupt jitter or certified WCET |
| Expanded software-in-loop fault cases | 64 seeded cases in `tools/extended_prework.py` | PASS | assumed plant; no physical stop measurement |
| ASan / UBSan C++ testing | `tools/verify_sanitizers.sh` | PASS locally | does not guarantee absence of all defects |

See `outputs/extended_prework/REPORT.md`, `docs/EMBEDDED_INTERFACE_SPEC.md` and `docs/ENGINEERING_RISK_REGISTER.md`.
