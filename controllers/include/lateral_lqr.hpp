#pragma once

#include "agentix_types.hpp"

class LateralLqr {
public:
    LateralLqr(const VehicleParams& vp, const LqrOpts& lqr);
    LateralLqrResult step(double Ux, const Vec4& x_lat);

private:
    VehicleParams vp_;
    LqrOpts       lqr_;
    std::array<double, 4> K_{ {0.0, 0.0, 0.0, 0.0} };
    Mat4 S_{};          // for Vdot estimate
    double Ux_nom_ = 8.0;  // m/s, nominal speed for gain calc
    // runtime state / limits
    double prev_delta_     = 0.0;
    double delta_rate_max_ = 2.0;   // [rad/s] rate limit to avoid bang-bang
    double ey_deadband_    = 0.05;  // [m] small-error suppression
    double epsi_deadband_  = 0.05;  // [rad]
    double Ts_             = 0.05;  // controller step [s]
};
