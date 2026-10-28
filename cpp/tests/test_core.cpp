#include "servo/control.hpp"
#include "servo/supervisor.hpp"
#include "servo/generated_assumptions.hpp"
#include <cassert>
#include <cmath>
#include <limits>
int main() {
    servo::CascadedController controller(servo::kAssumedConfig);
    const servo::Reference ref{0.10,0.05,0.0};
    const servo::Feedback fb{0.01,0.0,0.0,true,true,false};
    for(int i=0;i<1000;++i){
        const auto out=controller.step(ref,fb);
        assert(out.valid);
        assert(std::abs(out.voltage_v)<=servo::kAssumedConfig.bus_voltage_v+1e-12);
        assert(std::abs(out.target_current_a)<=servo::kAssumedConfig.current_limit_a+1e-12);
        assert(std::isfinite(out.voltage_v));
    }
    assert(controller.ticks()==1000);
    controller.reset();assert(controller.ticks()==0);
    auto invalid=fb;invalid.encoder_valid=false;
    const auto off=controller.step(ref,invalid);
    assert(!off.valid && off.voltage_v==0 && controller.ticks()==0);
    const auto nan=std::numeric_limits<double>::quiet_NaN();
    auto bad=fb;bad.speed_rad_s=nan;
    assert(!controller.step(ref,bad).valid);
    const servo::SupervisorConfig sc{.2,.02,18.0,85.0,0.0,.3};
    servo::Supervisor sup(sc);
    sup.sil_enable(0);
    sup.heartbeat(0.1);
    auto healthy=sup.update(.1,{.05,.1,24.,35.,true,true,false});
    assert(healthy.mode==servo::Mode::Enabled && healthy.permit_drive);
    auto fault=sup.update(.35,{.05,.35,24.,35.,true,true,false});
    assert(fault.mode==servo::Mode::Fault && fault.cause==servo::Cause::HeartbeatTimeout);
    assert(!sup.update(.4,{.05,.4,24.,35.,true,true,false}).permit_drive);
    assert(sup.reset_latch());
    sup.sil_enable(.5);
    assert(sup.update(.5,{.05,.5,24.,35.,true,true,true}).mode==servo::Mode::Estop);
    return 0;
}
