#pragma once
// Virtual CAN-FD-sized command envelope, NOT CANopen and NOT a certified safety bus.
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace servo {
enum class Operation :std::uint8_t {Move=1,Stop=2,Heartbeat=3,Home=4,Reset=5};
struct Command {std::uint32_t sequence{};Operation operation{};std::int32_t position_um{};};
using BusFrame=std::array<std::uint8_t,12>;
std::uint16_t crc16_ccitt(const std::uint8_t* p,std::size_t n) noexcept;
BusFrame encode(const Command& c) noexcept;
std::optional<Command> decode(const BusFrame& f) noexcept;
enum class FrameResult {Accepted,Duplicate,RejectedBadCrc,RejectedSequence};
class Receiver {
public:
    FrameResult submit(const BusFrame& frame) noexcept;
    [[nodiscard]] std::optional<Command> last() const noexcept {return last_command_;}
private:
    std::optional<Command> last_command_{};
    BusFrame last_frame_{};
};
}
