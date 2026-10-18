#pragma once

#include "agentix_types.hpp"
#include "agentix_utils.hpp"

// CTG 계산 함수 선언
CtgOutput compute_ctg(const CtgOpts& ctg,
                      const Limits& lim,
                      CtgState state,
                      double vx,
                      double d);
