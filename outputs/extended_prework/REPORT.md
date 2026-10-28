# Extended pre-Codex servo verification

**Status:** synthetic software evidence only. Assumed loads and motor constants have not been identified on hardware.

## Synthetic parameter identification

- Locked-rotor RL resistance: **1.49922 Ω** (assumed 1.50000 Ω)
- Locked-rotor inductance: **3.01283 mH** (assumed 3.00000 mH)
- Electrical holdout RMSE: **0.02109 A**
- Fitted equivalent inertia: **0.0005682 kg·m²** (assumed 0.0005683)
- Mechanical fit torque RMSE: **0.000157 Nm**

Parameter confidence intervals assume independent Gaussian residual noise; they are not datasheet tolerances.

## Fixed-priority response-time analysis (assumed task costs)

- Task utilisation: **7.05%**
- All declared deadlines schedulable under model: **True**

| Task | Period (µs) | Assumed WCET (µs) | Response bound (µs) | Deadline (µs) |
|---|---:|---:|---:|---:|
| current_control | 1000 | 35 | 35 | 1000 |
| velocity_control | 4000 | 60 | 95 | 4000 |
| communication_housekeeping | 10000 | 120 | 215 | 10000 |
| position_control | 10000 | 85 | 300 | 10000 |

**Not** a measurement of actual interrupt latency, WCET or real-time jitter.

## Deterministic software fault campaign

- Cases: **64**, seed **2026**
- Post-fault command voltage inhibit violations: **0**
- Maximum absolute simulated post-fault travel: **27.56 mm**
- Contact-count occurrences in these simulated runs: **0**

These are not safety-rated stopping tests. Drive disable may allow coasting and gravity/load-induced motion.

## Communication/embedded boundaries

- C++ native loop defaults to disabled and latches excessive tick gaps, stale samples or non-finite inputs.
- Virtual CiA402-style state machine prohibits motion until successive controlword transitions.
- Virtual register map and localhost-only Modbus/TCP test server provide register reads/writes; no industrial fieldbus, remote exposure or actuator link.
- Native host benchmark samples **function compute-time**, not end-to-end jitter or an embedded WCET.

- Host benchmark 60000 cycles: p50 **0.051 µs**, p95 **0.078 µs**, p99 **0.088 µs**, maximum **1173.628 µs**.
