#include "servo/hal.hpp"
#include "servo/generated_assumptions.hpp"
#include <cassert>
#include <cmath>

struct FakeBoard {
    servo::AxisObservation observation{};
    servo::DriveDemand last_demand{};
    unsigned writes{};
    static servo::AxisObservation read(void* p) noexcept {return static_cast<FakeBoard*>(p)->observation;}
    static void write(void* p,servo::DriveDemand d) noexcept {
        auto &x=*static_cast<FakeBoard*>(p);
        x.last_demand=d;++x.writes;
    }
};
int main(){
    using namespace servo;
    auto cfg=kAssumedConfig;
    SupervisorConfig limits{.command_timeout_s=.20,.sensor_timeout_s=.020,.min_bus_v=18,
        .max_temperature_c=85,.travel_min_m=0,.travel_max_m=.30};
    FakeBoard board;
    board.observation={.timestamp_s=0,.feedback_sample_time_s=0,.position_m=0,.velocity_rad_s=0,.current_a=0,
        .dc_bus_v=24,.motor_temperature_c=35,.encoder_valid=true,.drive_ready=true,
        .independent_interlock_ok=true,.emergency_stop=false};
    HostPortableAxis loop(cfg,limits,LoopPolicy{},IOPort{&board,&FakeBoard::read,&FakeBoard::write});
    const Reference target{.position_m=.025};
    loop.cycle(target);assert(!board.last_demand.enable); // default OFF
    loop.authorize_simulation_only(.001);
    board.observation.timestamp_s=.001;board.observation.feedback_sample_time_s=.001;
    assert(loop.cycle(target).command.valid);
    assert(board.last_demand.enable);
    assert(std::abs(board.last_demand.normalized_voltage_duty)<=1.0);
    board.observation.independent_interlock_ok=false;
    board.observation.timestamp_s=.002;board.observation.feedback_sample_time_s=.002;
    loop.cycle(target);assert(!board.last_demand.enable); // external interlock dominates
    board.observation.independent_interlock_ok=true;
    board.observation.timestamp_s=.003;board.observation.feedback_sample_time_s=.003;
    loop.cycle(target);assert(!board.last_demand.enable); // cannot re-enable automatically
    loop.authorize_simulation_only(.004);
    board.observation.timestamp_s=.004;board.observation.feedback_sample_time_s=.004;
    loop.cycle(target);assert(board.last_demand.enable);
    board.observation.emergency_stop=true;
    board.observation.timestamp_s=.005;board.observation.feedback_sample_time_s=.005;
    loop.cycle(target);assert(!board.last_demand.enable);
    board.observation.emergency_stop=false;
    board.observation.timestamp_s=.006;board.observation.feedback_sample_time_s=.006;
    loop.cycle(target);assert(!board.last_demand.enable); // latched
    assert(loop.reset_for_simulation());
    board.observation.timestamp_s=.007;board.observation.feedback_sample_time_s=.007;
    loop.cycle(target);assert(!board.last_demand.enable); // explicit re-arm required
    assert(!loop.reset_for_simulation());
    loop.authorize_simulation_only(.008);
    board.observation.timestamp_s=.008;board.observation.feedback_sample_time_s=.008;
    loop.cycle(target);assert(board.last_demand.enable);
    board.observation.timestamp_s=.050;board.observation.feedback_sample_time_s=.009;
    loop.cycle(target);assert(!board.last_demand.enable); // true stale time now observable
}
