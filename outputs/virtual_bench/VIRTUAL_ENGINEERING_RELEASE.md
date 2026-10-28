# Project 4 — Virtual Engineering Release (28 October 2026)

**Software digital twin: PASS. No physical motor, MCU, PLC or safety-related equipment was used.**

## Real manufacturer facts versus inferred and assumed inputs

- ST STM32G474RE, Cortex-M4 170 MHz with 512 KiB Flash and 128 KiB SRAM (manufacturer specification). ARM cross-compilation demonstrates code generation only; the ELF has **no functional vendor HAL or MCU GPIO/PWM/ADC/encoder configuration**, and is **not a flash-ready commissioned firmware image**.
- Pololu #4693, 24 V, 200 rpm unloaded output, 0.1 A no-load current, 3.0 A **extrapolated** stall current, 23 kg-cm extrapolated output torque, 50:1 gearing, 3,200 counts per output revolution (quadrature x4). Stall is not a continuous operating point.
- Pololu #2992, 6.5–40 V *absolute-max supply range* and 13 A published continuous-driver rating, default ~30 A chopping threshold. That default is **not suitable as a 3 A motor overcurrent protection**. CS ~40 mV/A + 50 mV offset is not available in all switching/braking states, so the simulated signed-current sensor is an **idealised replacement**.
- From vendor numbers, motor R≈8.00 Ω and K_e≈0.02215 V/(rad/s), *inferred and approximate*. L=5.0 mH, gearbox η=0.70, equivalent inertia J=0.00550 kg·m², friction/temperature model and 0.75 A operating limit are **assumptions**.

Sources: https://www.st.com/en/microcontrollers-microprocessors/stm32g474re.html · https://www.pololu.com/product/4693 · https://www.pololu.com/product/2992

## Actual virtual test results

| Metric | Software evidence |
|---|---:|
| C firmware in host simulation | Compiled, executed |
| Cortex-M4 freestanding binary | ARM ELF generated (compile-only) |
| Nominal PLC command | 90° move, dwell, return to 0° |
| Nominal final angle | -0.169° |
| Peak output speed | 24.368 rpm |
| Peak simulated winding current | 0.181 A |
| Nominal firmware state | DONE |
| Faults latched (defined scenarios) | 12 |
| Software voltage-enable violations after latch | 0 |
| Assumption-screen passes | 200/200 |
| Seeded screen p95 final absolute angle | 0.312° |
| Seeded screen p95 peak motor current | 0.222 A |

The seeded inertia/friction ranges are arbitrary ±30% mathematical scenarios—not measured manufacturing variation, statistical reliability or product qualification.

## What the virtual machine contains

1. **Published component targets** and assumption-provenance config.
2. **One C control/supervisor core** used by the host simulation and a Cortex-M4 cross-compiled artifact.
3. **A software motor/gearbox/load model** with idealised PWM H-bridge, ADC/encoder feedback, supply, winding heating and inertia.
4. **Rotary PLC register image and Modbus PDU coverage**, with signed millidegree telemetry, command sequences and two-move machine sequencing. Loopback-only simulation; not a real PLC.
5. **Fault injection and recovery interfaces**: no automatic re-enable after a latched fault, software command inhibit verified.
6. **Offline interactive dashboard** generated from actual simulation traces rather than mock charts.
7. **Regression tests, original C++/Python SIL, CI**, and reproducible study outputs.

## Limitations that cannot be solved by more assumptions

- No actual ADC calibration, PWM/gate-drive behavior, encoder polarity or switching-braking measurement.
- No reliable real current measurement under all H-bridge commutation/braking states; software current limit is **not hardware protection**.
- No physical independent protective interlock, emergency stop, safe torque-off, guarding or measured stopping distance.
- No STM32 hardware-specific HAL, oscillator/clock, peripherals, timer interrupts, jitter or WCET measurement.
- No motor bearing/gearbox wear, real thermal limits, actual torque constant or shaft-load test.
- No CANopen/EtherCAT certification, networked PLC, validated physical homing or commissioning.

**Completion statement:** PROJECT 4 IS COMPLETE **FOR THE DEFINED SOFTWARE-ONLY / VIRTUAL BENCH SCOPE**. It is intentionally not labelled a hardware-tested, certified servo drive or deployed automation cell.

## Reproduction

```bash
python -m pip install -e '.[test]'
python tools/build_virtual_firmware.py
PYTHONPATH=src python tools/build_virtual_bench_evidence.py --samples 200 --seed 2026
PYTHONPATH=src python -m pytest -q
python tools/quality_gate.py
```

Open `outputs/virtual_bench/virtual_commissioning_dashboard.html` in any browser (offline).
