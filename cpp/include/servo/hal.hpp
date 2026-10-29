#pragma once
// Portable hardware abstraction. The host fake is testable; no vendor HAL is wired.
// A real machine still requires an independent, verified safety circuit.
#include "servo/runtime.hpp"
#include <cstdint>

namespace servo {
struct AxisObservation {
    double timestamp_s{}; // monotonic control-loop time
    double feedback_sample_time_s{}; // independent sensor acquisition time
    double position_m{};
    double velocity_rad_s{};
    double current_a{};
    double dc_bus_v{};
    double motor_temperature_c{};
    bool encoder_valid{};
    bool drive_ready{};
    bool independent_interlock_ok{}; // Observed external safety-chain status only.
    bool emergency_stop{};
};
struct DriveDemand {
    bool enable{};
    double normalized_voltage_duty{}; // illustrative sign/direction, [-1,1].
};
struct IOPort {
    void* context{};
    AxisObservation (*read)(void*) noexcept{};
    void (*write)(void*,DriveDemand) noexcept{};
};
class HostPortableAxis {
public:
    HostPortableAxis(AxisConfig axis,SupervisorConfig supervision,LoopPolicy timing,IOPort port) noexcept;
    // This intentionally requires explicit operator action for SIL. Real firmware
    // must implement validated homing, safety handshake and commissioning gates.
    void authorize_simulation_only(double now_s) noexcept {loop_.authorize_simulation_only(now_s);}
    void heartbeat(double now_s) noexcept {loop_.heartbeat(now_s);}
    bool reset_for_simulation() noexcept {return loop_.reset_fault_for_simulation();}
    CycleResult cycle(Reference target) noexcept;
    void force_disabled() noexcept;
private:
    EmbeddedLoop loop_;
    IOPort port_;
};
}
