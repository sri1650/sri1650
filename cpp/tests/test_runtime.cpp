#include "servo/runtime.hpp"
#include "servo/drive402.hpp"
#include "servo/generated_assumptions.hpp"
#include <cassert>
#include <cmath>
#include <limits>
int main(){
 using namespace servo;
 const auto c=kAssumedConfig;
 const SupervisorConfig s{.command_timeout_s=.2,.sensor_timeout_s=.02,.min_bus_v=18,
   .max_temperature_c=85,.travel_min_m=0,.travel_max_m=.3};
 const LoopPolicy policy{};
 const Reference command{.position_m=.025,.velocity_m_s=0,.acceleration_m_s2=0};
 const Feedback fb{.position_m=0,.speed_rad_s=0,.current_a=0};
 const SensorStatus nominal{.position_m=0,.sample_time_s=0,.bus_voltage_v=24,
   .motor_temperature_c=35,.encoder_valid=true,.drive_ready=true,.emergency_stop=false};
 EmbeddedLoop loop(c,s,policy);
 assert(!loop.cycle(0,command,fb,nominal).command.valid); // disabled on boot
 loop.authorize_simulation_only(.001);
 assert(loop.cycle(.001,command,fb,nominal).command.valid);
 auto stale=nominal;stale.sample_time_s=.005;
 assert(!loop.cycle(.030,command,fb,stale).command.valid); // deadline and stale
 assert(loop.missed_deadlines()==1);
 assert(!loop.cycle(.031,command,fb,stale).command.valid); // sticky fault
 assert(loop.reset_fault_for_simulation());
 assert(!loop.cycle(.04,command,fb,nominal).command.valid); // explicit re-arm needed
 loop.authorize_simulation_only(.05);
 auto estop=nominal;estop.sample_time_s=.05;estop.emergency_stop=true;
 assert(!loop.cycle(.05,command,fb,estop).command.valid);
 assert(loop.cycle(.051,command,fb,nominal).supervisor.mode==Mode::Estop); // latched
 assert(loop.reset_fault_for_simulation());
 loop.authorize_simulation_only(.06);
 auto bad=nominal;bad.sample_time_s=.06;
 const auto nan=std::numeric_limits<double>::quiet_NaN();
 assert(!loop.cycle(.06,{nan,0,0},fb,bad).command.valid);
 assert(loop.reset_fault_for_simulation());
 loop.authorize_simulation_only(.07);
 bad.sample_time_s=.07;
 assert(loop.cycle(.07,command,fb,bad).command.valid);
 assert(!loop.cycle(.069,command,fb,bad).command.valid); // monotonicity
 assert(loop.reset_fault_for_simulation());
 loop.authorize_simulation_only(.08);
 bad.sample_time_s=10;
 assert(!loop.cycle(.08,command,fb,bad).command.valid); // future-stamped sensors forbidden
 assert(loop.reset_fault_for_simulation());
 VirtualDrive402 drive;
 assert(!drive.may_accept_motion() && drive.statusword()==0x40);
 drive.command(0x000F);assert(!drive.may_accept_motion()); // can't skip states
 drive.command(0x0006);assert(drive.state()==DriveState::ReadyToSwitchOn);
 drive.command(0x0007);assert(drive.state()==DriveState::SwitchedOn);
 drive.command(0x000F);assert(drive.may_accept_motion());
 drive.command(0x000B);assert(drive.state()==DriveState::QuickStopActive);
 drive.command(0x000F);assert(!drive.may_accept_motion());
 drive.command(0x0006);drive.command(0x0007);drive.command(0x000F);
 assert(drive.may_accept_motion());
 drive.inject_fault();drive.command(0x0080);
 assert(drive.state()==DriveState::Fault);
 drive.clear_fault_input();drive.command(0x0080);assert(drive.state()==DriveState::SwitchOnDisabled);
 return 0;
}
