# Hardware-first work reserved for Work/Codex

## Verified pre-Work deliverables

1. Single-source assumed axis configuration with Mechanical CAD provenance.
2. Python electromechanical ODE model and quintic trajectory generation.
3. C++20 fixed-rate cascaded P/PI/PI controller, conditional antiwindup and soft limits.
4. Virtual position encoder and bounded software fault supervisor.
5. Python and C++ illustrative command protocols with replay/CRC checks.
6. Native C++ compile/CTest; Python tests; full trace and cross-language comparison.
7. Nominal, disturbance, fault and deterministic parameter variation evidence.
8. Offline interactive dashboard, plots, CSV, JSON and engineering documentation.

## Next stage A — real embedded toolchain, if required by target roles

- Decide MCU target (e.g. STM32 G4, RP2040 or comparable), RTOS vs bare-metal, and toolchain support.
- Port C++ control core behind a hardware abstraction boundary (ADC, PWM, encoder, timer, GPIO, temperature and supply voltage interfaces).
- Establish real timing with recorded ISR execution and deadline/jitter metrics.
- If relevant, integrate a *real* BLDC FOC/current-control power stage; current project uses only averaged DC-equivalent motor dynamics.
- Use hardware-independent test fakes, unit tests and host-compiled firmware before attempting to energise actuators.

## Next stage B — transport / industrial communications

- Choose CANopen CiA 402 or EtherCAT stack based on hardware; do not label the current virtual formats as CANopen.
- Generate an interface specification, cyclic process-data mapping, latching sequence semantics and fault codes.
- Verify timeouts, duplicate commands, bus-off and identity using a loopback or HIL test rig.
- Implement firmware or PLC supervisory mode transitions with logged causal evidence.

## Next stage C — real hardware, explicitly not achievable in a cloud-only work session

- Obtain actual motor datasheet, drive, shaft, encoder, bracket and risk assessment.
- Measure winding/torque constants, friction, effective inertia and electrical/thermal response.
- Independent STO/e-stop, fuses, mechanical guards, limit switches, safe low-voltage bench and electrical inspection.
- Tune controllers against measured plant. Validate settling, overshoot, fault stop, current/temperature and repeatability.
- Preserve actual scope: 'hardware-in-loop' and 'physical validation' only after tests on physical devices.

## Next stage D — PLC and automation-cell integration

- After motor firmware and hardware interface are stable, implement IEC 61131-3 Structured Text machine sequencing, PLC/HMI and fieldbus diagnostics as the next separate career-facing project.

**Do not spend Work/Codex credits rebuilding the already verified host-side simulations or reports.**


## Latest cost-saving checkpoint

Before spending Codex credits, the project now includes an actual host-compiled C++ HAL interface, loop supervisor, virtual drive-state machine, local Modbus/TCP test server, synthetic motor identification, scheduling feasibility analysis, stress/fault campaign and sanitiser checks. **Do not implement these again.** See `docs/NEXT_WORK_BOUNDARY.md` and `outputs/extended_prework/REPORT.md`.

The next real step requires exact motor/driver/MCU hardware selection and a supervised low-energy physical test bench. An entirely cloud-based workflow cannot validate those tasks. For the PLC track, continue from the tested register contract; only a qualified implementation with an actual PLC runtime and network/drive should be described as PLC integration.
