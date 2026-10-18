#include "agentix_types.hpp"
#include "agentix_utils.hpp"
#include "lateral_lqr.hpp"
#include "longitudinal_ctg.hpp"
#include "longitudinal_mpc.hpp"

extern "C" {

struct RevisionParameters {
    double mass, inertia, front_length, rear_length, front_stiffness, rear_stiffness;
    double ax_min, ax_max, delta_max;
    double time_gap, standstill_gap, proportional_gain, derivative_gain, sample_time;
    double horizon, iterations, distance_cost, speed_cost, action_cost, step_size, fd_epsilon;
    double lateral_cost[4];
    double steering_cost;
};

struct RevisionOutput {
    double ax_ctg, ax_mpc, dref, delta_lqr, delta_lqr_unlimited, vdot_nom;
};

struct RevisionHandle {
    VehicleParams vehicle;
    Limits limits;
    CtgOpts ctg;
    MpcOpts mpc;
    LqrOpts lqr;
    CtgState ctg_state;
    LateralLqr* lateral;
};

RevisionHandle* revision_create(const RevisionParameters* params) {
    auto* handle = new RevisionHandle{};
    handle->vehicle.m = params->mass;
    handle->vehicle.Iz = params->inertia;
    handle->vehicle.lf = params->front_length;
    handle->vehicle.lr = params->rear_length;
    handle->vehicle.Cf = params->front_stiffness;
    handle->vehicle.Cr = params->rear_stiffness;
    handle->limits.ax_min = params->ax_min;
    handle->limits.ax_max = params->ax_max;
    handle->limits.delta_max = params->delta_max;
    handle->ctg.Tg = params->time_gap;
    handle->ctg.d0 = params->standstill_gap;
    handle->ctg.Kp = params->proportional_gain;
    handle->ctg.Kv = params->derivative_gain;
    handle->ctg.Ts = params->sample_time;
    handle->mpc.N = static_cast<int>(params->horizon);
    handle->mpc.max_iter = static_cast<int>(params->iterations);
    handle->mpc.Ts = params->sample_time;
    handle->mpc.q1 = params->distance_cost;
    handle->mpc.q2 = params->speed_cost;
    handle->mpc.r = params->action_cost;
    handle->mpc.step_size = params->step_size;
    handle->mpc.fd_eps = params->fd_epsilon;
    for (int index = 0; index < 4; ++index) {
        handle->lqr.Q[index] = params->lateral_cost[index];
    }
    handle->lqr.R = params->steering_cost;
    handle->lateral = new LateralLqr(handle->vehicle, handle->lqr);
    return handle;
}

RevisionOutput revision_step(RevisionHandle* handle, double speed, double distance,
                             double lead_speed, double target_speed, const double* state) {
    Vec4 lateral_state{};
    for (int index = 0; index < 4; ++index) {
        lateral_state.v[index] = state[index];
    }
    auto lateral = handle->lateral->step(speed, lateral_state);
    auto ctg = compute_ctg(handle->ctg, handle->limits, handle->ctg_state, speed, distance);
    handle->ctg_state = ctg.state;
    double mpc = mpc_longitudinal_ax_full(speed, distance, lead_speed, target_speed,
                                         handle->ctg, handle->limits, handle->mpc);
    double unlimited = 0.0;
    for (int index = 0; index < 4; ++index) {
        unlimited -= lateral.K[index] * state[index];
    }
    return {ctg.ax_ctg, mpc, ctg.dref,
            clampv(lateral.delta_cmd, -handle->limits.delta_max, handle->limits.delta_max),
            unlimited, lateral.Vdot_nom};
}

void revision_destroy(RevisionHandle* handle) {
    if (handle) {
        delete handle->lateral;
        delete handle;
    }
}

}
