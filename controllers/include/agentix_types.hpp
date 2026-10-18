#pragma once

#include <array>
#include <vector>

// ---- LQR용 간단 타입 ----
struct Mat4 {
    double a[4][4]{};  // zero-initialized
};

struct Vec4 {
    double v[4]{};     // zero-initialized
};

// ---- 차량/제약/옵션 ----
struct VehicleParams {
    double m  = 1500.0;
    double Iz = 3000.0;
    double lf = 1.2;
    double lr = 1.6;
    double Cf = 80000.0;
    double Cr = 80000.0;
};

struct Limits {
    double ax_min    = -4.0;
    double ax_max    =  3.0;
    double delta_max =  0.3;   // rad
};

struct CtgOpts {
    double Tg = 1.6;
    double d0 = 5.0;
    double Kp = 0.65;
    double Kv = 0.45;
    double Ts = 0.05;
};

struct CtgState {
    bool   inited  = false;
    double ed_prev = 0.0;
};

struct CtgOutput {
    double   ax_ctg = 0.0;
    double   dref   = 0.0;
    CtgState state{};
};

struct LqrOpts {
  // [ey, eydot, epsi, epsidot]
  std::array<double,4> Q{{3.0, 0.5, 6.0, 5.0}};
  double R = 5.0;
};
struct MpcOpts {
    int    N         = 20;
    int    max_iter  = 10;
    double Ts        = 0.05;
    double q1        = 1.0;
    double q2        = 1.0;
    double r         = 5.0;
    double step_size = 0.5;
    double fd_eps    = 1e-2;

    double R_th      = 1.0;
    double k_alpha   = 5.0;
};

struct RiskOpts {
    double d_safe     = 30.0;
    double v_min_norm = 1.0;
    double kappa_max  = 0.05;
    double w_d        = 1.0;
    double w_v        = 1.0;
    double w_kappa    = 1.0;
    double w_s        = 0.0;
    double w_p        = 0.0;
};


// ---- LQR 결과 ----
struct LateralLqrResult {
    double delta_cmd = 0.0;
    std::array<double, 4> K{{0.0, 0.0, 0.0, 0.0}};
    double Vdot_nom  = 0.0;
};

// ---- Controller 출력 ----
struct ControlOutput {
    double delta_cmd = 0.0;
    double ax_cmd    = 0.0;
    double dref_ctg  = 0.0;

    std::array<double, 4> K{{0.0, 0.0, 0.0, 0.0}};
    double Vdot_nom  = 0.0;

    double ax_ctg    = 0.0;
    double ax_mpc    = 0.0;
    double alpha     = 0.0;
};
