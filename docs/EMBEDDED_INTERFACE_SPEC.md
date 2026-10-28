# Hardware-neutral embedded porting and interface specification

**Revision:** 28 October 2026. **Status:** developer interface contract; not a commissioned motor controller, safety function or manufacturer specification.

## Control topology and ownership

| Component | Interface | Responsibility | Verification now | Required in hardware |
|---|---|---|---|---|
| Current feedback | ADC/DMA calibrated samples | Current regulator feedback | simulated `Feedback.current_a` | calibrated shunt/isolated sensor, scaling, filtering, saturation |
| Encoder | hardware quadrature or digital absolute | position and velocity | virtual quantization | resolution, polarity, index, rollover, stale timestamp, noise |
| PWM/drive | motor driver command | apply current/voltage control demand | host fake records normalised duty | real switching driver, deadtime, overcurrent and electrical protections |
| Temperature | ADC or drive status | warning/fault | simulated high temperature | physical temperature sensor and verified thermal model |
| DC link | ADC | voltage brownout / overvoltage reporting | simulated low voltage | calibrated supply reading and overvoltage protection |
| Limit switches | redundant/dedicated input | travel reference and protective limits | simulated only | independently wired hardware safety and limit validation |
| Independent stop chain | physical drive STO / contactor | prevent hazardous movement | **observational** `independent_interlock_ok` fake | independent verified hardware, safety review and risk assessment |
| Command fieldbus | CANopen/EtherCAT/PLC | coordination and command lifecycle | virtual state and Modbus/TCP localhost subset | qualified stack, device EDS, PDO mapping, bus fault recovery |

The C++ `servo/hal.hpp` fake demonstrates a **software output inhibit**. It cannot guarantee torque-off, protective stopping, or prevention of gravity-induced motion. No unsafe startup: the portable loop begins disabled and the only available re-arm is explicitly named `authorize_simulation_only`.

## Periodic task proposal (assumed, not measured WCET)

| Loop | Period | Hypothetical WCET |
|---|---:|---:|
| Current regulation | 1 ms | 35 µs |
| Velocity regulation | 4 ms | 60 µs |
| Position loop | 10 ms | 85 µs |
| Communication/health | 10 ms | 120 µs |

`src/servo_lab/schedulability.py` calculates fixed-priority response-time bounds for these *invented* costs. It does not verify ARM/STM32 interrupt latency, peripheral synchronisation, RTOS scheduling or thermal-frequency scaling.

**Host benchmark:** `servo_host_cycle_benchmark` measures standalone function call cost under the development host. Neither its maximum nor its percentile is a proven WCET. Recorded wall time includes host scheduler noise and is not suitable for calculating a real hardware control-loop deadline.

## Sensor and data contracts

- C++ control cycle uses independent `AxisObservation.timestamp_s` (monotonic loop clock) and `feedback_sample_time_s` (acquisition time); future timestamps and stale samples cause inhibited output.
- Encoder conversion and direction must be calibrated against a measured linear travel reference; never rely on nominal counts alone.
- Reference positions and velocities use metres and m/s, motor speed uses rad/s, current uses amperes, command voltage uses volts.
- Software drive demand from `HostPortableAxis` is a signed **normalised voltage fraction**, not a PWM gate sequence or FOC waveform.
- The simulated hard travel limits do not represent real protective limit switches.

## Industrial-drive boundaries

`cpp/include/servo/drive402.hpp` implements **state semantics inspired by CiA 402** (shutdown, switch-on, enable operation, quick-stop, fault reset), but has no EDS, SDO, PDO, NMT, heartbeat producer/consumer, SYNC, network timing, bus-off recovery, CAN controller, or validated compliant drive.

`src/servo_lab/plc_contract.py` defines zero-based registers; `modbus_tcp.py` implements a loopback-only test server with function codes 3/4/6/16. No access controls or secure network services are present. No physical connection should use this server.

### Register map (zero-based protocol addresses)

| Address | Direction | Meaning |
|---:|---|---|
| 0 | holding/write | command (none/move/stop/home/reset) |
| 1 | holding/write | command sequence (16-bit; wrap requires explicit resync) |
| 2–3 | holding/write | signed 32-bit target position, micrometres, high/low word |
| 100 | input/read | axis state code |
| 101 | input/read | fault code (future device mapping required) |
| 102–103 | input/read | signed 32-bit feedback position, micrometres |
| 104 | input/read | signed signed-16 feedback speed, millimetres/second |
| 105 | input/read | last acknowledged command sequence |

Register map is a **host simulation contract**, not a production PLC address allocation. Real PLC integration also requires atomic command latching, timeout/lost-communications behaviour, privilege management, and safety validation.

## Embedded firmware responsibilities reserved for Work/Codex

1. Confirm exact MCU, motor, power stage, encoder and drive datasheets.
2. Create a real vendor toolchain target from this portable control code, without copying SIL bypass methods into production.
3. Implement and calibrate actual ADC/DMA/PWM/encoder/timer interfaces, synchronised sampling, signal limits and watchdog resets.
4. Establish measured interrupt/RTOS jitter, execution-time histograms and conservative true WCET margins on the selected hardware.
5. Connect a vendor-qualified CANopen or EtherCAT transport with real fault, network and lifecycle tests.
6. Demonstrate hardware-independent safety circuits and supervised commissioning **before** energising the motor.

The physical system must never be declared safe based on software-only unit tests.
