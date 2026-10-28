#pragma once
// Hardware-agnostic deterministic loop wrapper; SIL permit only, NEVER a physical safety function.
#include "servo/control.hpp"
#include "servo/supervisor.hpp"
#include <cstdint>

namespace servo {
struct LoopPolicy {
    double nominal_period_s{0.001};
    double maximum_tick_gap_s{0.003};
};
struct CycleResult {
    ControlOutput command{};
    SupervisorResult supervisor{};
    std::uint64_t ticks{};
    std::uint64_t missed_deadlines{};
};
class EmbeddedLoop {
public:
    EmbeddedLoop(AxisConfig axis,SupervisorConfig supervisor,LoopPolicy timing) noexcept;
    // Explicit SIL-only bypass: not a commissioning/homing implementation.
    void authorize_simulation_only(double now_s) noexcept;
    void heartbeat(double now_s) noexcept;
    void stop() noexcept;
    bool reset_fault_for_simulation() noexcept;
    [[nodiscard]] CycleResult cycle(double now_s,Reference target,Feedback feedback,SensorStatus sensors) noexcept;
    [[nodiscard]] std::uint64_t ticks() const noexcept {return ticks_;}
    [[nodiscard]] std::uint64_t missed_deadlines() const noexcept {return missed_deadlines_;}
private:
    static bool finite(Reference target,Feedback feedback,SensorStatus sensors) noexcept;
    CascadedController controller_;
    Supervisor supervisor_;
    LoopPolicy timing_;
    bool seen_tick_{};
    double last_tick_s_{};
    std::uint64_t ticks_{};
    std::uint64_t missed_deadlines_{};
};
}
