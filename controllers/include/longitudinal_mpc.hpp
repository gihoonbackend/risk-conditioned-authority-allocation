#pragma once

#include "agentix_types.hpp"

double mpc_longitudinal_ax_full(double vx, double d,
                                double v_lead, double v_ref,
                                const CtgOpts& ctg,
                                const Limits& lim,
                                const MpcOpts& mpc);
