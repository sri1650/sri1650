# Virtual bench I/O contract and electrical review

**No physical wiring schematic has been issued.** The following are logical channels for the simulator only. STM32 alternate functions, pin voltage tolerances and rail power must be determined and reviewed before actual hardware wiring.

| Function | Virtual signal / meaning | Physical evidence still needed |
|---|---|---|
| 1 kHz control timebase | integer `time_ms`, monotonic | STM32 timer ISR and jitter/deadline measurements |
| Quadrature encoder A/B | 3,200 x4 counts/output rev, simulated signed encoder | STM32 timer encoder mode, 5 V encoder output level shifting, noise/rollover |
| Driver PWM/DIR | signed normalized duty -1…+1, average voltage motor model | reviewed timer AF, polarity, switching, dead-time and safe startup |
| Driver SLP/enable | software enable gated by virtual interlock | physical independent disable path; actual board may be **enabled by default** |
| Driver FLT | software driver-good/fault injection | real open-drain pull-up and logic-level verification |
| Driver CS | idealized signed and quantised measurement | real CS only valid during active driving; external shunt/sensor likely required |
| Supply voltage and temperature | synthetic float sensor channels | actual ADC/thermistor calibration, limits, wiring and accuracy |
| Independent interlock input | boolean only in software | physical independent power isolation and competent safety review |
| PLC command | loopback rotary register image, FC03/04/06/16 test | production PLC runtime, cybersecurity, real bus wiring and fieldbus conformance |

The motor's blue encoder supply lead requires **3.5–20 V**. The yellow/white encoder A/B outputs are approximately the encoder supply voltage and should never be assumed compatible with any STM32 pin without verifying its input tolerance. Use proper level shifting and ground strategy if constructing a future bench.

This simulation uses **one open-circuit voltage-disable model** rather than all possible H-bridge switching/braking/freewheel states. Simulated software fault latency and angle travel cannot be taken as real emergency-stop measurements.
