#include "servo/runtime.hpp"
#include "servo/generated_assumptions.hpp"
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <vector>

// Best-effort HOST compute-time microbenchmark, not a real-time jitter measurement.
int main(){
    constexpr int n=60000;
    const auto cfg=servo::kAssumedConfig;
    const servo::SupervisorConfig supervisor{.command_timeout_s=.2,.sensor_timeout_s=.02,.min_bus_v=18,
        .max_temperature_c=85,.travel_min_m=0,.travel_max_m=.3};
    servo::EmbeddedLoop loop(cfg,supervisor,servo::LoopPolicy{});
    loop.authorize_simulation_only(0);
    std::vector<double> us;
    us.reserve(n);
    std::uint64_t valid_count=0;
    double observable_checksum=0.0;
    for(int i=0;i<n+1200;++i){
        const double t=i*.001;
        if(i%50==0)loop.heartbeat(t);
        const servo::SensorStatus status{.position_m=.0,.sample_time_s=t,.bus_voltage_v=24,
            .motor_temperature_c=35,.encoder_valid=true,.drive_ready=true,.emergency_stop=false};
        const servo::Reference ref{.position_m=.02,.velocity_m_s=0,.acceleration_m_s2=0};
        const servo::Feedback fb{.position_m=0,.speed_rad_s=0,.current_a=0};
        const auto a=std::chrono::steady_clock::now();
        const auto result=loop.cycle(t,ref,fb,status);
        const auto b=std::chrono::steady_clock::now();
        if(i>=1200){
            const double cost=std::chrono::duration<double,std::micro>(b-a).count();
            us.push_back(cost);
            valid_count+=result.command.valid ? 1u:0u;
            observable_checksum+=result.command.voltage_v+0.13*result.command.target_current_a;
        }
    }
    std::sort(us.begin(),us.end());
    const auto pct=[&](double p){const std::size_t idx=static_cast<std::size_t>((us.size()-1)*p);return us[idx];};
    std::cout<<std::fixed<<std::setprecision(6)
       <<"{\"scope\":\"native host loop compute time; NOT deterministic real-time jitter or WCET\","
       <<"\"samples\":"<<us.size()<<",\"valid_commands\":"<<valid_count
       <<",\"p50_us\":"<<pct(.5)<<",\"p95_us\":"<<pct(.95)
       <<",\"p99_us\":"<<pct(.99)<<",\"max_us\":"<<us.back()
       <<",\"missed_logical_deadlines\":"<<loop.missed_deadlines()
       <<",\"observable_output_checksum\":"<<observable_checksum<<"}\n";
    return valid_count==n && loop.missed_deadlines()==0 ? 0:1;
}
