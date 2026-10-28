#pragma once
#include <cstdint>

namespace servo {
struct AxisConfig {
    double dt_s{};
    std::uint32_t position_divisor{}, velocity_divisor{};
    double position_kp{},velocity_kp{},velocity_ki{},current_kp{},current_ki{};
    double current_limit_a{},speed_limit_m_s{}, bus_voltage_v{};
    double winding_resistance{},back_emf_constant{},torque_constant{};
    double moving_mass_kg{},friction_coefficient{},gravity_m_s2{},smoothing_speed_m_s{};
    double gear_ratio{},pulley_radius_m{},efficiency{},travel_min_m{},travel_max_m{},soft_margin_m{};
};
struct Reference {
    double position_m{},velocity_m_s{},acceleration_m_s2{};
};
struct Feedback {
    double position_m{}, speed_rad_s{},current_a{};
    bool encoder_valid{true},drive_ready{true},emergency_stop{false};
};
struct ControlOutput {
    double voltage_v{},target_current_a{},target_velocity_m_s{};
    bool valid{};
};
class CascadedController {
public:
    explicit CascadedController(AxisConfig config) noexcept;
    [[nodiscard]] ControlOutput step(const Reference& reference,const Feedback& feedback) noexcept;
    void reset() noexcept;
    [[nodiscard]] std::uint64_t ticks() const noexcept {return tick_;}
private:
    static double clamp(double value,double limit) noexcept;
    static double conditional_integral(double integral,double error,double dt,double ki,double kp,double ff,double limit,double imax) noexcept;
    AxisConfig c_{};
    std::uint64_t tick_{};
    double target_velocity_m_s_{}, target_current_a_{}, speed_integral_{}, current_integral_{};
};
}
