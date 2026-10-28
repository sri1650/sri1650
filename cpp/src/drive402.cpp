#include "servo/drive402.hpp"
namespace servo {
std::uint16_t VirtualDrive402::statusword() const noexcept {
    switch(state_) {
      case DriveState::SwitchOnDisabled: return 0x0040;
      case DriveState::ReadyToSwitchOn: return 0x0021;
      case DriveState::SwitchedOn: return 0x0023;
      case DriveState::OperationEnabled: return 0x0027;
      case DriveState::QuickStopActive: return 0x0007;
      case DriveState::Fault: return 0x0008;
    }
    return 0x0000;
}
void VirtualDrive402::command(std::uint16_t cw) noexcept {
    if(state_==DriveState::Fault){
        if((cw&0x0080)!=0 && !fault_present_)state_=DriveState::SwitchOnDisabled;
        return;
    }
    if((cw&0x0002)==0){state_=DriveState::SwitchOnDisabled;return;}
    if(state_==DriveState::OperationEnabled && (cw&0x0004)==0){state_=DriveState::QuickStopActive;return;}
    if(state_==DriveState::QuickStopActive){
        if((cw&0x000F)==0x0006)state_=DriveState::ReadyToSwitchOn;
        return;
    }
    if(state_==DriveState::SwitchOnDisabled && (cw&0x000F)==0x0006)
        state_=DriveState::ReadyToSwitchOn;
    else if(state_==DriveState::ReadyToSwitchOn && (cw&0x000F)==0x0007)
        state_=DriveState::SwitchedOn;
    else if(state_==DriveState::SwitchedOn && (cw&0x000F)==0x000F)
        state_=DriveState::OperationEnabled;
    else if(state_==DriveState::OperationEnabled && (cw&0x000F)==0x0007)
        state_=DriveState::SwitchedOn;
}
}
