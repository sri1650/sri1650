#include "servo/hal.hpp"
#include <algorithm>
#include <cmath>
namespace servo {
HostPortableAxis::HostPortableAxis(AxisConfig cfg,SupervisorConfig supervision,LoopPolicy timing,IOPort p) noexcept
    :loop_(cfg,supervision,timing),port_(p),dc_bus_nominal_v_(cfg.bus_voltage_v) {}
void HostPortableAxis::force_disabled() noexcept {
    loop_.stop();
    if(port_.write)port_.write(port_.context,{false,0.0});
}
CycleResult HostPortableAxis::cycle(Reference reference) noexcept {
    if(!port_.read || !port_.write){
        loop_.stop();
        return {};
    }
    const auto obs=port_.read(port_.context);
    const Feedback fb{obs.position_m,obs.velocity_rad_s,obs.current_a,
        obs.encoder_valid,obs.drive_ready,obs.emergency_stop};
    const SensorStatus sensor{obs.position_m,obs.feedback_sample_time_s,obs.dc_bus_v,
        obs.motor_temperature_c,obs.encoder_valid,obs.drive_ready,obs.emergency_stop};
    // Check external interlock at *every* cycle. It is NOT a software safety function.
    if(!obs.independent_interlock_ok){force_disabled();return {};}
    const auto r=loop_.cycle(obs.timestamp_s,reference,fb,sensor);
    const bool enabled=r.command.valid && r.supervisor.permit_drive &&
        std::isfinite(r.command.voltage_v) && std::isfinite(obs.dc_bus_v) && obs.dc_bus_v>0;
    const double duty=enabled?std::clamp(r.command.voltage_v/obs.dc_bus_v,-1.0,1.0):0.0;
    port_.write(port_.context,{enabled,duty});
    return r;
}
}
