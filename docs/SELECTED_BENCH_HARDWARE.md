# Selected reference hardware — Project 4 bench revision A

**Decision date:** 2026-10-28  
**Status:** parts selected for a future *benchtop demonstration*, not ordered, wired, commissioned, integrated or tested. No production- or safety-rated claim.

## Why this hardware

The existing Python/C++ controller is deliberately portable and has **no physical motor measurements**. This reference stack provides a reasonable first real target for PWM actuation, quadrature-encoder position feedback, fault-line sampling, timing measurements and controller identification on an STM32 MCU. These are supplier-specified items, **not** the currently assumed electrical/mechanical SIL plant or the previously designed CAD bracket.

| Function | Selected exact item | Supplier-level facts | Integration boundary |
|---|---|---|---|
| MCU target | ST **NUCLEO-G474RE**, STM32G474RET6 | Cortex-M4 170 MHz, 512 KiB Flash, encoder-capable timers, ADC, advanced PWM timers and FDCAN peripheral; integrated ST-LINK | Choose actual STM32 timer/GPIO/ADC pins in CubeMX; CAN requires an external transceiver and actual protocol stack |
| Feedback motor | Pololu **#4693**, 50:1 37Dx70L 24 V brushed gearmotor, integrated 64 CPR encoder | 200 rpm no-load at 24 V; 3 A **extrapolated stall current**, 64 CPR motor shaft / approximately 3200 counts per gearbox-output revolution on x4 decoding; encoder supply **3.5–20 V** | Gearmotor differs from original generic simulated servo, and its gearbox has load restrictions; mechanical interface must be redesigned |
| H-bridge | Pololu **#2992**, G2 24v13 brushed motor driver | 6.5–40 V driver supply range, 3.3 V-compatible direction/PWM inputs, output current sensing and FLT; **default current chopping threshold around 30 A**, not protective for a 3 A-stall motor | Implement independent current limiting, fuse, measured thermal checks and hardwired power removal; driver SLP can be enabled by default |
| Electrical supply | Current-limited bench power supply with adjustable output up to 24 V; suitable 5 V regulator / encoder level shifter | **Not yet vendor-selected**; assess actual load and wiring before purchase | Begin at reduced voltage/current, current-limit hardware, tie logic grounds appropriately, prevent encoder's 5 V output reaching non-5-V-tolerant MCU pins |
| Mechanics | Isolated motor test fixture with guarding and uncoupled load | **Not yet designed/validated** | No personnel-accessible moving conveyor/axis; no assumed compatibility with Project 3 motor bracket |

## Supplier documentation

- ST NUCLEO-G474RE / UM2505: https://www.st.com/resource/en/user_manual/um2505-stm32g4-nucleo64-boards-mb1367-stmicroelectronics.pdf
- STM32G474 family datasheet: https://www.st.com/resource/en/datasheet/stm32g474re.pdf
- Pololu #4693 motor: https://www.pololu.com/product/4693
- Pololu 37D dimension drawing: https://www.pololu.com/file/0J1704/37d-metal-gearmotors-dimension-diagram.pdf
- Pololu #2992 driver: https://www.pololu.com/product/2992

## Required software adaptation — **not implemented yet**

1. Stand up MCU firmware build and on-target debug with STM32CubeIDE/STM32CubeMX or verified CMake GCC-ARM toolchain.
2. Define and verify PWM timer, DIR output, low-active hardware gate/disable, encoder input capture/interrupts, ADC current sensing, independent fault/limit/stop input, and monotonic timer timestamps.
3. Implement a vendor-specific STM32 hardware adapter for existing portable C++ `EmbeddedLoop` and `HostPortableAxis`; keep default-off outputs and independently test every enable/rearm transition.
4. Capture motor electrical and mechanical constants from **actual** bench measurements and independently validate against held-out real traces. Replace `config/assumed_axis.json` with a separate *measured* configuration; never silently overwrite simulated assumptions.
5. Perform low-current, uncoupled startup first, then gated position/velocity control, fault timing, current/temperature and physical coast/stop measurements. Record instruments, uncertainties and test conditions.
6. Treat the virtual CiA 402 and localhost Modbus interface as protocol prototypes only. Real CANopen/CiA 402 and EtherCAT are **not** implemented by this motor-driver combination, and neither can be claimed merely because the MCU contains FDCAN peripherals.

## Safety and fit review

- **No safety-rated stop**: firmware disable, Pololu SLP and the software fault latch cannot replace an independent supply-disconnect path or a properly assessed safe motor-stop design.
- **Current limiting:** the H-bridge's default ~30 A threshold far exceeds the motor's 3 A extrapolated stall draw. Use a separately verified lower-current limit or current-limited bench supply; never rely on the board default for motor protection.
- **Encoder voltage:** because the encoder supply minimum is 3.5 V, a separate regulated supply (typically 5 V) and voltage-safe signal interfacing are required; ST MCU pin tolerance must be checked by chosen physical pin.
- **Gearbox and torque:** extrapolated stall torque is not continuous rated torque. Do not use it for load-bearing qualification.
- **Axis-model mismatch:** existing SIL assumes an 8 kg moved mass, 20 mm pulley, 3:1 gearing and hypothetical electrical constants. The 50:1 gearmotor reference is for **controller prototyping**, not a drop-in design approval for the 100 mm test axis.

**Decision:** proceed with a NUCLEO-G474RE + Pololu #4693 + Pololu #2992 as the **reference hardware integration target**. Do not order irreversible mechanical items or energise any bench until the wiring, independent disable, power protection and engineering safety review are complete.
