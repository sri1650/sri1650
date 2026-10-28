#include "servo/virtual_bus.hpp"
#include <bit>
namespace servo {
std::uint16_t crc16_ccitt(const std::uint8_t* bytes,std::size_t n) noexcept {
    std::uint16_t crc=0xffffu;
    for(std::size_t j=0;j<n;++j) {
        crc^=static_cast<std::uint16_t>(bytes[j])<<8;
        for(int i=0;i<8;++i)crc=(crc&0x8000u)?static_cast<std::uint16_t>((crc<<1)^0x1021u):static_cast<std::uint16_t>(crc<<1);
    }
    return crc;
}
BusFrame encode(const Command& c) noexcept {
    BusFrame f{};
    const auto pos=static_cast<std::uint32_t>(c.position_um);
    f[0]=static_cast<std::uint8_t>(c.sequence>>24);f[1]=static_cast<std::uint8_t>(c.sequence>>16);
    f[2]=static_cast<std::uint8_t>(c.sequence>>8);f[3]=static_cast<std::uint8_t>(c.sequence);
    f[4]=static_cast<std::uint8_t>(c.operation);
    f[5]=static_cast<std::uint8_t>(pos>>24);f[6]=static_cast<std::uint8_t>(pos>>16);
    f[7]=static_cast<std::uint8_t>(pos>>8);f[8]=static_cast<std::uint8_t>(pos);
    const auto crc=crc16_ccitt(f.data(),10);
    f[10]=static_cast<std::uint8_t>(crc>>8);f[11]=static_cast<std::uint8_t>(crc);
    return f;
}
std::optional<Command> decode(const BusFrame& f) noexcept {
    const auto expected=crc16_ccitt(f.data(),10);
    if(f[9]!=0 || f[10]!=static_cast<std::uint8_t>(expected>>8)||f[11]!=static_cast<std::uint8_t>(expected))return {};
    const auto op=f[4];
    if(op<1 || op>5)return {};
    const auto seq=(static_cast<std::uint32_t>(f[0])<<24) |(static_cast<std::uint32_t>(f[1])<<16)|
            (static_cast<std::uint32_t>(f[2])<<8)|static_cast<std::uint32_t>(f[3]);
    const auto pos=(static_cast<std::uint32_t>(f[5])<<24)|(static_cast<std::uint32_t>(f[6])<<16)|
           (static_cast<std::uint32_t>(f[7])<<8)|static_cast<std::uint32_t>(f[8]);
    return Command{seq,static_cast<Operation>(op),std::bit_cast<std::int32_t>(pos)};
}
FrameResult Receiver::submit(const BusFrame& f) noexcept {
    auto cmd=decode(f);
    if(!cmd) return FrameResult::RejectedBadCrc;
    if(last_command_) {
        if(cmd->sequence<last_command_->sequence)return FrameResult::RejectedSequence;
        if(cmd->sequence==last_command_->sequence)return (f==last_frame_)?FrameResult::Duplicate:FrameResult::RejectedSequence;
    }
    last_command_=*cmd;
    last_frame_=f;
    return FrameResult::Accepted;
}
}
