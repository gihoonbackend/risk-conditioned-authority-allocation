import ast
import ctypes
import math

import numpy as np

from common import ROOT


class Parameters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_double) for name in (
        "mass", "inertia", "front_length", "rear_length", "front_stiffness", "rear_stiffness",
        "ax_min", "ax_max", "delta_max", "time_gap", "standstill_gap", "proportional_gain",
        "derivative_gain", "sample_time", "horizon", "iterations", "distance_cost", "speed_cost",
        "action_cost", "step_size", "fd_epsilon")]
    _fields_ += [("lateral_cost", ctypes.c_double * 4), ("steering_cost", ctypes.c_double)]


class Output(ctypes.Structure):
    _fields_ = [(name, ctypes.c_double) for name in (
        "ax_ctg", "ax_mpc", "dref", "delta_lqr", "delta_lqr_unlimited", "vdot_nom")]


class Controller:
    def __init__(self, library_path, config):
        self.library = ctypes.CDLL(str(library_path))
        self.library.revision_create.argtypes = [ctypes.POINTER(Parameters)]
        self.library.revision_create.restype = ctypes.c_void_p
        self.library.revision_step.argtypes = [ctypes.c_void_p, *([ctypes.c_double] * 4), ctypes.POINTER(ctypes.c_double)]
        self.library.revision_step.restype = Output
        self.library.revision_destroy.argtypes = [ctypes.c_void_p]
        self.library.revision_destroy.restype = None
        control = config["controller"]
        vehicle, limits, ctg, mpc, lqr = [control[key] for key in ("vehicle_model", "limits", "ctg", "mpc", "lqr")]
        parameters = Parameters(
            *[vehicle[key] for key in ("m", "Iz", "lf", "lr", "Cf", "Cr")],
            *[limits[key] for key in ("ax_min", "ax_max", "delta_max")],
            *[ctg[key] for key in ("Tg", "d0", "Kp", "Kv", "Ts")],
            *[mpc[key] for key in ("N", "max_iter", "q1", "q2", "r", "step_size", "fd_eps")],
            (ctypes.c_double * 4)(*lqr["Q"]), lqr["R"],
        )
        self.handle = self.library.revision_create(ctypes.byref(parameters))
        if not self.handle:
            raise RuntimeError("Controller allocation failed")

    def step(self, speed, distance, lead_speed, target_speed, state):
        if not np.isfinite([speed, distance, lead_speed, target_speed, *state]).all():
            raise ValueError("Nonfinite input to C++ controller")
        output = self.library.revision_step(self.handle, speed, distance, lead_speed, target_speed,
                                            (ctypes.c_double * 4)(*state))
        result = {name: float(getattr(output, name)) for name, _kind in Output._fields_}
        if not np.isfinite(list(result.values())).all():
            raise ValueError("Nonfinite output from C++ controller")
        return result

    def close(self):
        if self.handle:
            self.library.revision_destroy(self.handle)
            self.handle = None


def load_geometry(config):
    settings = config["controller"]["state_geometry"]
    path = ROOT / settings["source"]
    tree = ast.parse(path.read_text(), filename=str(path))
    names = set(settings["functions"])
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in definitions} != names:
        raise ValueError("Legacy geometry function missing")
    module = ast.Module(body=definitions, type_ignores=[])
    namespace = {"np": np, "math": math, "REF_LANE_ID": None, "REF_ROAD_ID": None}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace


class ResidualPolicy:
    def __init__(self, config):
        import torch
        from torch import nn

        self.settings = config["controller"]["rl"]
        self.device = self.settings["device"]
        checkpoint = torch.load(config["artifacts"]["rl_checkpoint"]["absolute_path"], map_location=self.device)
        state_dim = int(checkpoint["actor"]["0.weight"].shape[1])
        hidden = int(checkpoint["actor"]["0.weight"].shape[0])
        if state_dim != self.settings["state_dim"] or hidden != self.settings["hidden_dim"]:
            raise ValueError("Checkpoint architecture disagrees with canonical configuration")
        self.model = nn.Sequential(nn.Linear(state_dim, hidden), nn.ReLU(), nn.Linear(hidden, hidden),
                                   nn.ReLU(), nn.Linear(hidden, 1), nn.Tanh()).to(self.device)
        self.model.load_state_dict(checkpoint["actor"])
        self.model.eval()
        self.mean = np.asarray(checkpoint["norm_mean"], dtype=np.float32).reshape(-1)
        self.variance = np.asarray(checkpoint["norm_var"], dtype=np.float32).reshape(-1)
        if self.mean.shape != (state_dim,) or self.variance.shape != (state_dim,):
            raise ValueError("Checkpoint normalization shape mismatch")
        if not np.isfinite(self.mean).all() or not np.isfinite(self.variance).all() or (self.variance < 0).any():
            raise ValueError("Invalid checkpoint normalization")
        self.previous = 0.0

    def step(self, state):
        import torch

        values = np.asarray(state, dtype=np.float32)
        normalized = (values - self.mean) / (np.sqrt(self.variance) + 1e-6)
        if not np.isfinite(normalized).all():
            raise ValueError("Nonfinite normalized RL state")
        with torch.no_grad():
            actor_output = float(self.model(torch.from_numpy(normalized).to(self.device)).cpu().item())
        if not math.isfinite(actor_output):
            raise ValueError("Nonfinite RL action")
        bound = self.settings["action_bound_rad"]
        raw = actor_output * bound
        filtered = filter_residual(raw, self.previous, self.settings)
        self.previous = filtered
        return {"actor_output": actor_output, "residual_raw_rad": raw, "residual_filtered_rad": filtered}


def filter_residual(raw, previous, settings):
    bound = settings["action_bound_rad"]
    clipped = float(np.clip(raw, -bound, bound))
    slew = settings["slew_limit_rad_per_step"]
    limited = float(np.clip(clipped, previous - slew, previous + slew))
    coefficient = settings["lpf_previous_coefficient"]
    return float(np.clip(coefficient * previous + (1 - coefficient) * limited, -bound, bound))


def guard_residual_authority(delta_lqr, alpha_lat, residual_filtered, settings):
    guard = settings.get("residual_authority_guard", {"enabled": False})
    unguarded = float(alpha_lat * residual_filtered)
    if not guard.get("enabled", False):
        return {"residual_effective_unguarded_rad": unguarded,
                "residual_effective_guarded_rad": unguarded,
                "residual_guard_active": False,
                "residual_guard_reason": "disabled"}
    lqr_floor = float(guard["lqr_floor_rad"])
    retained_fraction = float(guard["minimum_lqr_retained_fraction"])
    low_lqr_bound = float(guard["low_lqr_effective_bound_rad"])
    if not 0 <= retained_fraction <= 1 or lqr_floor < 0 or low_lqr_bound < 0:
        raise ValueError("Invalid residual authority guard configuration")
    effective = unguarded
    reason = "none"
    if abs(delta_lqr) < lqr_floor:
        effective = float(np.clip(effective, -low_lqr_bound, low_lqr_bound))
        if effective != unguarded:
            reason = "low_lqr_bound"
    elif delta_lqr * effective < 0:
        opposing_bound = (1 - retained_fraction) * abs(delta_lqr)
        effective = math.copysign(min(abs(effective), opposing_bound), effective)
        if effective != unguarded:
            reason = "preserve_lqr_authority"
    return {"residual_effective_unguarded_rad": unguarded,
            "residual_effective_guarded_rad": effective,
            "residual_guard_active": reason != "none",
            "residual_guard_reason": reason}


def steering_postprocess(delta, ey, epsi, previous_steer, settings, sample_time):
    if not np.isfinite([delta, ey, epsi, previous_steer]).all():
        raise ValueError("Nonfinite steering input")
    active_deadband = abs(ey) < settings["ey_deadband_m"] and abs(epsi) < settings["epsi_deadband_rad"]
    value = 0.0 if active_deadband else delta
    soft_scale = max(settings["soft_min_scale"],
                     min(1.0, abs(ey) / settings["soft_ey_threshold_m"]),
                     min(1.0, abs(epsi) / settings["soft_epsi_threshold_rad"]))
    value *= soft_scale * settings["gain"]
    pre_clip = value
    value = float(np.clip(value, -settings["sanity_clip_rad"], settings["sanity_clip_rad"]))
    bound = settings["final_clip_rad"] * settings["gain"]
    value = float(np.clip(value, -bound, bound))
    steer_raw = float(np.clip(value / bound, -settings["carla_steer_clip"], settings["carla_steer_clip"]))
    rate_step = settings["carla_steer_rate_per_s"] * sample_time
    if abs(ey) > settings["large_ey_m"] or abs(epsi) > settings["large_epsi_rad"]:
        rate_step *= settings["large_error_rate_multiplier"]
    if np.sign(steer_raw) != np.sign(previous_steer):
        rate_step *= settings["sign_change_rate_multiplier"]
    rate_step = min(settings["carla_steer_clip"], rate_step)
    limited = float(np.clip(steer_raw, previous_steer - rate_step, previous_steer + rate_step))
    coefficient = settings["lpf_previous_coefficient"]
    steer = float(np.clip(coefficient * previous_steer + (1 - coefficient) * limited,
                          -settings["carla_steer_clip"], settings["carla_steer_clip"]))
    return {"delta_combined_rad": delta, "delta_pre_clip_rad": pre_clip, "delta_command_rad": value,
            "steer_applied": steer, "delta_applied_equivalent_rad": steer * bound,
            "steering_deadband_active": active_deadband, "steering_soft_scale": soft_scale,
            "steering_clip_active": abs(pre_clip) >= bound}


def lead_profile(time_s, config, path1_entry_s=None):
    cruise = config["controller"]["lead"]["cruise_speed_mps"]
    scenario = config["experiment"]["scenario"]
    if scenario == "high_curvature_low_longitudinal_risk":
        condition = config["experiment"].get("lead_condition")
        if condition is None:
            raise ValueError("High-curvature isolation scenario requires an explicit lead condition")
        if condition.get("profile") != "fixed_cruise_no_brake":
            raise ValueError("Unsupported high-curvature lead condition")
        target = float(condition["cruise_speed_mps"])
        if target < 0:
            raise ValueError("Lead cruise target must be nonnegative")
        return target, "curvature_isolation_cruise"
    if scenario in ("nominal_integrated", "nominal_following"):
        return cruise, "cruise"
    event = config["experiment"]["emergency"]
    if scenario == "curvature_emergency" and path1_entry_s is not None:
        brake_start = path1_entry_s + event.get("path1_entry_delay_s", 5.0)
    elif scenario == "curvature_emergency":
        return cruise, "await_path1_for_brake"
    else:
        brake_start = event["trigger_time_s"]
    brake_end = brake_start + event["brake_ramp_s"]
    hold_end = brake_end + event["stop_hold_s"]
    if time_s < brake_start:
        return cruise, "cruise"
    if time_s < brake_end:
        return cruise * (1 - (time_s - brake_start) / event["brake_ramp_s"]), "hard_brake"
    if time_s < hold_end:
        return 0.0, "full_stop"
    if event["recovery_speed_mps"] <= 1e-6:
        return 0.0, "full_stop_hold"
    if time_s < hold_end + event["recovery_ramp_s"]:
        return event["recovery_speed_mps"] * (time_s - hold_end) / event["recovery_ramp_s"], "recovery_ramp"
    return event["recovery_speed_mps"], "recovery_cruise"


def lead_control(lead, world_map, target, settings, carla):
    waypoint = world_map.get_waypoint(lead.get_location(), project_to_road=True)
    following = waypoint.next(settings["lookahead_m"])
    if not following:
        raise RuntimeError("Lead vehicle reference route ended")
    transform = lead.get_transform()
    location = following[0].transform.location
    target_yaw = math.atan2(location.y - transform.location.y, location.x - transform.location.x)
    heading = (target_yaw - math.radians(transform.rotation.yaw) + math.pi) % (2 * math.pi) - math.pi
    steer = float(np.clip(heading * settings["heading_gain"], -1, 1))
    velocity = lead.get_velocity()
    speed = math.sqrt(velocity.x ** 2 + velocity.y ** 2 + velocity.z ** 2)
    pedal = settings["base_throttle"] + settings["speed_gain"] * (target - speed)
    return carla.VehicleControl(throttle=float(np.clip(pedal, 0, 1)),
                               brake=float(np.clip(-pedal, 0, 1)), steer=steer)
