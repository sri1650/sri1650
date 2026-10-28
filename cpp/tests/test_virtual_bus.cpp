#include "servo/virtual_bus.hpp"
#include <cassert>
#include <cstring>
#include <cstdint>
int main(){
    constexpr unsigned char v[]={'1','2','3','4','5','6','7','8','9'};
    assert(servo::crc16_ccitt(v,sizeof(v))==0x29b1u); // canonical CRC-16/CCITT-FALSE vector
    const servo::Command c{42,servo::Operation::Move,100000};
    const auto frame=servo::encode(c);
    auto dec=servo::decode(frame);
    assert(dec && dec->sequence==42 && dec->position_um==100000 && dec->operation==servo::Operation::Move);
    servo::Receiver receiver;
    assert(receiver.submit(frame)==servo::FrameResult::Accepted);
    assert(receiver.submit(frame)==servo::FrameResult::Duplicate);
    auto older=servo::encode({41,servo::Operation::Stop,0});
    assert(receiver.submit(older)==servo::FrameResult::RejectedSequence);
    auto clash=servo::encode({42,servo::Operation::Move,200000});
    assert(receiver.submit(clash)==servo::FrameResult::RejectedSequence);
    auto bad=frame;bad[6]^=1;
    assert(receiver.submit(bad)==servo::FrameResult::RejectedBadCrc);
    auto neg=servo::encode({43,servo::Operation::Move,-20000});
    assert(servo::decode(neg)->position_um==-20000);
    auto reserved=frame;
    reserved[9]=7;
    const auto newcrc=servo::crc16_ccitt(reserved.data(),10);
    reserved[10]=static_cast<std::uint8_t>(newcrc>>8);
    reserved[11]=static_cast<std::uint8_t>(newcrc);
    assert(!servo::decode(reserved)); // reserved field must be zero even with valid CRC
    std::uint32_t seed=17;
    for(int i=0;i<10000;++i){
        servo::BusFrame malformed{};
        for(auto &x:malformed){seed=seed*1664525u+1013904223u;x=static_cast<std::uint8_t>(seed>>24);}
        (void)servo::decode(malformed); // malformed frames cannot crash or invoke UB
    }
}
