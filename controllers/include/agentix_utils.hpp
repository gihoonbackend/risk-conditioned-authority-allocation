#pragma once

#include <algorithm>

// Clamp value to [lo, hi]
inline double clampv(double v, double lo, double hi) {
    return std::min(std::max(v, lo), hi);
}
