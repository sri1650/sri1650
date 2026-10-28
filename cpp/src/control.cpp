#include "servo/control.hpp"
#include <algorithm>
#include <cmath>

namespace servo {
CascadedController::CascadedController(AxisConfig config) noexcept :c_(config){}
void CascadedController::reset() noexcept {
    tick_=0;target_velocity_m_s_=0;target_current_a_=0;speed_integral_=0;current_integral_=0;
}
double CascadedController::clamp(double x,double lim) noexcept {
    return std::max(-lim,std::min(lim,x));
}
double CascadedController::conditional_integral(double val,double err,double dt,double ki,double kp,double ff,double lim,double imax) noexcept {
    const auto trial=clamp(val+err*dt,imax);
    const auto unsat=ff+kp*err+ki*trial;
    if ((unsat>lim && err>0)||(unsat<-lim && err<0)) return val;
    return trial;
}
ControlOutput CascadedController::step(const Reference& r,const Feedback& f) noexcept {
    if(!f.encoder_valid || !f.drive_ready || f.emergency_stop ||
       !std::isfinite(r.position_m) || !std::isfinite(r.velocity_m_s) || !std::isfinite(r.acceleration_m_s2) ||
       !std::isfinite(f.position_m) || !std::isfinite(f.speed_rad_s) || !std::isfinite(f.current_a)) {
        reset();return {};
    }
    if ((tick_%c_.position_divisor)==0) {
        target_velocity_m_s_=clamp(r.velocity_m_s+c_.position_kp*(r.position_m-f.position_m),c_.speed_limit_m_s);
        if(f.position_m<c_.travel_min_m+c_.soft_margin_m) target_velocity_m_s_=std::max(0.0,target_velocity_m_s_);
        if(f.position_m>c_.travel_max_m-c_.soft_margin_m) target_velocity_m_s_=std::min(0.0,target_velocity_m_s_);
    }
    if ((tick_%c_.velocity_divisor)==0) {
        const auto omega_ref=target_velocity_m_s_*c_.gear_ratio/c_.pulley_radius_m;
        const auto err=omega_ref-f.speed_rad_s;
        const auto force_ff=c_.moving_mass_kg*r.acceleration_m_s2+
                            c_.friction_coefficient*c_.moving_mass_kg*c_.gravity_m_s2*std::tanh(target_velocity_m_s_/c_.smoothing_speed_m_s);
        const auto torque_ff=force_ff*c_.pulley_radius_m/(c_.gear_ratio*c_.efficiency);
        const auto i_ff=torque_ff/c_.torque_constant;
        speed_integral_=conditional_integral(speed_integral_,err,c_.dt_s*c_.velocity_divisor,
                      c_.velocity_ki,c_.velocity_kp,i_ff,c_.current_limit_a,
                      c_.current_limit_a/std::max(c_.velocity_ki,1e-9));
        target_current_a_=clamp(i_ff+c_.velocity_kp*err+c_.velocity_ki*speed_integral_,c_.current_limit_a);
    }
    const auto err_i=target_current_a_-f.current_a;
    const auto ff=c_.winding_resistance*target_current_a_+c_.back_emf_constant*f.speed_rad_s;
    current_integral_=conditional_integral(current_integral_,err_i,c_.dt_s,c_.current_ki,c_.current_kp,ff,c_.bus_voltage_v,
                                        c_.bus_voltage_v/std::max(c_.current_ki,1e-9));
    const auto voltage=clamp(ff+c_.current_kp*err_i+c_.current_ki*current_integral_,c_.bus_voltage_v);
    ++tick_;
    return {voltage,target_current_a_,target_velocity_m_s_,true};
}
}
