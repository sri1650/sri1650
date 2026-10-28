#include "servo/supervisor.hpp"
#include <cmath>
namespace servo {
SupervisorResult Supervisor::update(double now,const SensorStatus& s) noexcept {
    if(s.emergency_stop) latch(Mode::Estop,Cause::EmergencyStop);
    else if(mode_==Mode::Enabled||mode_==Mode::HomingSeek||mode_==Mode::HomingBackoff) {
        if(!std::isfinite(now)||now-last_command_s_>c_.command_timeout_s)latch(Mode::Fault,Cause::HeartbeatTimeout);
        else if(!std::isfinite(s.sample_time_s)||now-s.sample_time_s>c_.sensor_timeout_s)latch(Mode::Fault,Cause::StaleSensor);
        else if(!s.encoder_valid)latch(Mode::Fault,Cause::EncoderInvalid);
        else if(!s.drive_ready)latch(Mode::Fault,Cause::DriveNotReady);
        else if(s.bus_voltage_v<c_.min_bus_v)latch(Mode::Fault,Cause::UnderVoltage);
        else if(s.motor_temperature_c>=c_.max_temperature_c)latch(Mode::Fault,Cause::OverTemperature);
        else if(s.position_m<c_.travel_min_m-1e-6||s.position_m>c_.travel_max_m+1e-6)latch(Mode::Fault,Cause::PositionOutOfRange);
    }
    const auto permit=(mode_==Mode::Enabled || mode_==Mode::HomingSeek || mode_==Mode::HomingBackoff);
    return {mode_,cause_,permit};
}
}
