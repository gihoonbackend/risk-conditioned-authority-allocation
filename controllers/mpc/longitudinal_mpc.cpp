// longitudinal_mpc.cpp
#include "longitudinal_mpc.hpp"
#include "agentix_utils.hpp"
#include <cmath>

double mpc_longitudinal_ax_full(double vx, double d,
                                double v_lead, double v_ref,
                                const CtgOpts& ctg,
                                const Limits& lim,
                                const MpcOpts& mpc)
{
    const int MAXN = 32;
    int N = mpc.N;
    if(N <= 0) return 0.0;
    if(N > MAXN) N = MAXN;

    double a[MAXN];
    double grad[MAXN];

    for(int k=0;k<N;k++) a[k] = 0.0;

    auto cost_func = [&](const double a_seq[MAXN])->double{
        double v    = vx;
        double dist = d;
        double J    = 0.0;
        for(int k=0;k<N;k++){
            double d_ref_k = v*ctg.Tg + ctg.d0;
            double v_ref_k = v_ref;

            double ed = dist - d_ref_k;
            double ev = v - v_ref_k;

            J += mpc.q1 * ed*ed + mpc.q2 * ev*ev + mpc.r * a_seq[k]*a_seq[k];

            double v_next = v + mpc.Ts * a_seq[k];
            double d_next = dist + mpc.Ts*(v_lead - v);

            v    = v_next;
            dist = d_next;
        }
        return J;
    };

    for(int it=0; it<mpc.max_iter; ++it){
        for(int k=0;k<N;k++){
            double a_plus[MAXN], a_minus[MAXN];
            for(int j=0;j<N;j++){ a_plus[j]=a[j]; a_minus[j]=a[j]; }

            a_plus[k]  = clampv(a_plus[k]  + mpc.fd_eps, lim.ax_min, lim.ax_max);
            a_minus[k] = clampv(a_minus[k] - mpc.fd_eps, lim.ax_min, lim.ax_max);

            double Jp = cost_func(a_plus);
            double Jm = cost_func(a_minus);
            grad[k] = (Jp - Jm)/(2.0*mpc.fd_eps);
        }

        for(int k=0;k<N;k++){
            a[k] -= mpc.step_size * grad[k];
            a[k]  = clampv(a[k], lim.ax_min, lim.ax_max);
        }
    }

    return clampv(a[0], lim.ax_min, lim.ax_max);
}
