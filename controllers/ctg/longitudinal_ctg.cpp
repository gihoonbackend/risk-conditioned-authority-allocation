// longitudinal_ctg.cpp
#include "longitudinal_ctg.hpp"

CtgOutput compute_ctg(const CtgOpts& ctg,
                      const Limits& lim,
                      CtgState state,
                      double vx, double d)
{
    double dref = vx*ctg.Tg + ctg.d0;      // (20)
    double ed   = d - dref;               // (21)
    double edot = state.inited
                ? (ed - state.ed_prev)/ctg.Ts
                : 0.0;

    state.ed_prev = ed;
    state.inited  = true;

    double ax_ctg = ctg.Kp*ed + ctg.Kv*edot;  // (22)
    ax_ctg = clampv(ax_ctg, lim.ax_min, lim.ax_max);

    CtgOutput out;
    out.ax_ctg = ax_ctg;
    out.dref   = dref;
    out.state  = state;
    return out;
}
