# Contributor/Work instructions

- This is an existing, tested engineering simulation repository. Continue; do not regenerate.
- Source of truth is `config/assumed_axis.json`; regenerate C++ values with `python tools/generate_cpp_config.py` when changed.
- Use the current simulation requirements and design assumptions; do not imply that the numerical values came from an actual motor.
- First run `python tools/quality_gate.py`, then inspect only the files relevant to the next task.
- Keep source modules independent of proprietary automation SDKs; adapters go in separate packages.
- Tests before documentation; use deterministic compilers/numerical tools to validate.
- Maximum two focused repair attempts before recording a concrete blocker with commands and errors.
- Critical stop: no physical energisation, safety functions, commissioning or production assertions without reviewed hardware and risk assessments.
- Use separate classes of evidence: analytical / software-in-loop / HIL / actual hardware. HIL and physical are currently **not** present.
- Do not add GUI frameworks, ROS or PLC scaffolding solely to make the project larger.


## Extended pre-Codex boundaries

- Do not recreate `cpp/include/servo/{runtime,hal,drive402}.hpp` or `src/servo_lab/{identification,plc_contract,modbus_tcp,schedulability}.py`: all are exercised in the gate.
- Core C++ portable host fake requires explicit SIL-only rearm; do not port `authorize_simulation_only` as a hardware-enable command.
- The Modbus/TCP server is bound to loopback and is **not** a production PLC bridge. The drive402 abstraction only models certain CiA402 state transitions, not CANopen conformance.
- Run `python tools/quality_gate.py` (12-stage baseline) before touching passing code, and `tools/verify_sanitizers.sh` when modifying C++.
- Keep results separated: synthetic motor parameter identification, assumed timing WCET, native host compute-time microbenchmark, software fault-inhibit tests versus real hardware measurements.
