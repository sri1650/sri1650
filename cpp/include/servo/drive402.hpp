#pragma once
// CiA 402-inspired *virtual state semantics* only. No CANopen/EtherCAT transport,
// object dictionary, drive certification or safety-rated quick-stop is implemented.
#include <cstdint>
namespace servo {
enum class DriveState {SwitchOnDisabled,ReadyToSwitchOn,SwitchedOn,OperationEnabled,QuickStopActive,Fault};
class VirtualDrive402 {
public:
    [[nodiscard]] DriveState state() const noexcept {return state_;}
    [[nodiscard]] std::uint16_t statusword() const noexcept;
    [[nodiscard]] bool may_accept_motion() const noexcept {return state_==DriveState::OperationEnabled;}
    void inject_fault() noexcept {state_=DriveState::Fault; fault_present_=true;}
    void clear_fault_input() noexcept {fault_present_=false;}
    void command(std::uint16_t controlword) noexcept;
private:
    DriveState state_{DriveState::SwitchOnDisabled};
    bool fault_present_{};
};
}
