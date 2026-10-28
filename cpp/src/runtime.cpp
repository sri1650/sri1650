#include "servo/runtime.hpp"
#include <cmath>

namespace servo {
EmbeddedLoop::EmbeddedLoop(AxisConfig axis,SupervisorConfig supervisor,LoopPolicy timing) noexcept
    :controller_(axis),supervisor_(supervisor),timing_(timing) {}
void EmbeddedLoop::authorize_simulation_only(double now_s) noexcept {supervisor_.sil_enable(now_s);}
void EmbeddedLoop::heartbeat(double now_s) noexcept {supervisor_.heartbeat(now_s);}
void EmbeddedLoop::stop() noexcept {supervisor_.stop();controller_.reset();}
bool EmbeddedLoop::reset_fault_for_simulation() noexcept {
    const bool reset=supervisor_.reset_latch();
    controller_.reset();
    seen_tick_=false;
    return reset;
}
bool EmbeddedLoop::finite(Reference r,Feedback f,SensorStatus s) noexcept {
    return std::isfinite(r.position_m)&&std::isfinite(r.velocity_m_s)&&std::isfinite(r.acceleration_m_s2) &&
           std::isfinite(f.position_m)&&std::isfinite(f.speed_rad_s)&&std::isfinite(f.current_a) &&
           std::isfinite(s.position_m)&&std::isfinite(s.sample_time_s)&&
           std::isfinite(s.bus_voltage_v)&&std::isfinite(s.motor_temperature_c);
}
CycleResult EmbeddedLoop::cycle(double now_s,Reference ref,Feedback fb,SensorStatus sensors) noexcept {
    ++ticks_;
    if (!std::isfinite(now_s) || now_s<0 || !finite(ref,fb,sensors) ||
        sensors.sample_time_s<0 || sensors.sample_time_s>now_s+0.002) {
        supervisor_.software_fault(Cause::InvalidNumericInput);
    } else if (seen_tick_) {
        const double dt=now_s-last_tick_s_;
        if (dt<=0) supervisor_.software_fault(Cause::TimeWentBackwards);
        else if (dt>timing_.maximum_tick_gap_s) {
            ++missed_deadlines_;
            supervisor_.software_fault(Cause::DeadlineMiss);
        }
    }
    if(std::isfinite(now_s)) {last_tick_s_=now_s;seen_tick_=true;}
    const auto state=supervisor_.update(now_s,sensors);
    if(!state.permit_drive){controller_.reset();return {{},state,ticks_,missed_deadlines_};}
    const auto out=controller_.step(ref,fb);
    if(!out.valid || !std::isfinite(out.voltage_v)){
        supervisor_.software_fault(Cause::InvalidNumericInput);
        controller_.reset();
        return {{},supervisor_.update(now_s,sensors),ticks_,missed_deadlines_};
    }
    return {out,state,ticks_,missed_deadlines_};
}
}
