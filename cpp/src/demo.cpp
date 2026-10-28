#include "servo/control.hpp"
#include "servo/generated_assumptions.hpp"
#include <iostream>
#include <iomanip>
#include <cmath>
#include <algorithm>
// Deterministic C++ control-loop + simplified rigid transmission plant.
// Deliberately independent of the Python plant; used only as SIL smoke check.
int main(){
    auto c=servo::kAssumedConfig;
    servo::CascadedController ctrl(c);
    double pos=0,omega=0,current=0;
    const double j_eq=.00015+c.moving_mass_kg*c.pulley_radius_m*c.pulley_radius_m/(c.gear_ratio*c.gear_ratio*c.efficiency);
    std::cout<<"t_s,ref_m,pos_m,speed_m_s,current_a,voltage_v\n";
    for(int k=0;k<=2500;++k){
        const double t=k*c.dt_s;
        // Smooth rest-to-rest reference; duration generated from the shared JSON configuration.
        const double T=servo::kNominalMoveDurationS;
        const double s=std::clamp(t/T,0.0,1.0);
        const double x=.10*(10*s*s*s-15*s*s*s*s+6*s*s*s*s*s);
        const double v=t<T ? .10*(30*s*s-60*s*s*s+30*s*s*s*s)/T : 0;
        const double a=t<T ? .10*(60*s-180*s*s+120*s*s*s)/(T*T) : 0;
        auto out=ctrl.step({x,v,a},{pos,omega,current,true,true,false});
        const double vmotor=omega*c.pulley_radius_m/c.gear_ratio;
        const double friction=c.friction_coefficient*c.moving_mass_kg*c.gravity_m_s2*std::tanh(vmotor/c.smoothing_speed_m_s);
        const double reaction=friction*c.pulley_radius_m/(c.gear_ratio*c.efficiency);
        const double didt=(out.voltage_v-c.winding_resistance*current-c.back_emf_constant*omega)/.003;
        const double dwdt=(c.torque_constant*current-0.00018*omega-reaction)/j_eq;
        if(k<2500){
          current+=didt*c.dt_s;
          omega+=dwdt*c.dt_s;
          pos+=omega*c.dt_s*c.pulley_radius_m/c.gear_ratio;
        }
        if(k%10==0) std::cout<<std::setprecision(12)<<t<<','<<x<<','<<pos<<','<<vmotor<<','<<current<<','<<out.voltage_v<<'\n';
    }
    return 0;
}
