# Servo motion platform — engineering assumptions and risk register

The following are **unresolved engineering questions**, not evidence that hardware is safe. Severity is descriptive only; no invented risk priority numbers or certification claims.

| ID | Risk / uncertainty | Consequence | Evidence available | Required closure |
|---|---|---|---|---|
| H-01 | No selected motor/driver or validated torque constant | incorrect current/torque sizing and overheating | assumed 24 V DC equivalent motor model | manufacturer data, measured current/torque/temperature and thermal protection |
| H-02 | No independent torque-off / stop circuit designed | hazardous uncontrolled motion | software inhibit only | qualified safety architecture and demonstrated independent de-energisation |
| H-03 | Loss of supply or command while moving | residual coast travel into end-stop | synthetic coast travel up to ~28 mm in one campaign | real friction/inertia/load tests, physical guarding and stops |
| H-04 | Encoder polarity, dropouts, timestamp errors | feedback runaway or position loss | host fault guards and independent timestamps | sensor electrical integration, calibration, fault injection and data logging |
| H-05 | No real motor-axis friction or inertia measurements | unstable or mistuned controller | synthetic identification only | measured plant identification under controlled conditions |
| H-06 | No actual ISR jitter/deadline evidence | unstable timing or missed control updates | virtual fixed-priority response-time estimates and host call microbenchmark | target MCU timing measurement with all peripherals/network running |
| H-07 | Unverified CAD bracket and fastener interfaces | unexpected deflection/fatigue/bolted-joint slip | external Gmsh/CCX idealised preliminary model | supplier geometry, service loads, fatigue/joint models and physical tests |
| H-08 | Fieldbus not implemented or qualified | stale commands, bus-off or missed stop | local virtual register/drive-state tests | protocol stack, network fault tests, hardware watchdog and physical safety channel |
| H-09 | No loss-of-load or gravity model for vertical axis | uncontrolled drop after power loss | assumed horizontal axis only | use horizontal controlled bench; any vertical axis requires independent brake design |
| H-10 | No EMC/environmental validation | faults in real manufacturing environment | no hardware evidence | wiring, shielding, grounding, electrical inspection, EMC and environment tests |

## Hardware-entry checklist

- [ ] Actual movement, mass, load cases, velocity/acceleration and duty cycle signed off
- [ ] Selected motor, drive, power supply, encoder and current sensors verified by part number and revision
- [ ] Measured friction, inertia, resistance, inductance, temperature rise and torque/current conversions
- [ ] Mechanical alignment and stop arrangement inspected, including verified mounting and guarding
- [ ] Independent emergency stop/STO concept reviewed by a competent engineer
- [ ] Fuse/protection, ground, shielding, thermal, wiring and enclosure decisions reviewed
- [ ] Hardware watchdog, timer/ISR load, bus-off and feedback timing verified
- [ ] Controlled low-energy supervised commissioning plan and stop criteria approved

No physical testing is claimed anywhere in this project.
