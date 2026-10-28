#pragma once
#include <cstdint>
namespace servo {
enum class Mode {Disabled,HomingSeek,HomingBackoff,Enabled,Fault,Estop};
enum class Cause {None,HeartbeatTimeout,StaleSensor,EncoderInvalid,DriveNotReady,UnderVoltage,OverTemperature,PositionOutOfRange,EmergencyStop,DeadlineMiss,InvalidNumericInput,TimeWentBackwards};
struct SensorStatus {
    double position_m{};
    double sample_time_s{};
    double bus_voltage_v{24.0};
    double motor_temperature_c{35.0};
    bool encoder_valid{true};
    bool drive_ready{true};
    bool emergency_stop{false};
};
struct SupervisorConfig {
    double command_timeout_s{}, sensor_timeout_s{}, min_bus_v{}, max_temperature_c{}, travel_min_m{},travel_max_m{};
};
struct SupervisorResult {Mode mode{};Cause cause{};bool permit_drive{};};
class Supervisor {
public:
    explicit Supervisor(SupervisorConfig c) noexcept:c_(c){}
    void heartbeat(double now) noexcept {last_command_s_=now;}
    void sil_enable(double now) noexcept {if(mode_==Mode::Disabled){mode_=Mode::Enabled;heartbeat(now);}}
    void software_fault(Cause reason) noexcept {if(mode_!=Mode::Estop) latch(Mode::Fault,reason);}
    void stop() noexcept {if(mode_!=Mode::Fault && mode_!=Mode::Estop) mode_=Mode::Disabled;}
    bool reset_latch() noexcept {if(mode_==Mode::Fault||mode_==Mode::Estop){mode_=Mode::Disabled;cause_=Cause::None;return true;}return false;}
    [[nodiscard]] SupervisorResult update(double now,const SensorStatus& status) noexcept;
private:
    void latch(Mode mode,Cause reason) noexcept {mode_=mode;cause_=reason;}
    SupervisorConfig c_{};
    Mode mode_{Mode::Disabled};Cause cause_{Cause::None};double last_command_s_{};
};
}
