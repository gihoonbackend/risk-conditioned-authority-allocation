import math
from pathlib import Path

import numpy as np
import pandas as pd

from common import write_json


def rms(values):
    return float(np.sqrt(np.mean(np.asarray(values, dtype=float) ** 2)))


def distribution(values):
    values = np.asarray(values, dtype=float)
    return {"min": float(np.min(values)), "mean": float(np.mean(values)),
            "median": float(np.median(values)), "max": float(np.max(values)),
            "p95": float(np.percentile(values, 95))}


def performance(frame):
    timestamps = frame["time_s"].to_numpy()
    intervals = np.diff(timestamps)
    jerk = np.diff(frame["ax_command_mps2"].to_numpy()) / intervals
    steering_rate = np.diff(frame["delta_applied_equivalent_rad"].to_numpy()) / intervals
    distance_error = frame["d_bumper_m"].to_numpy() - frame["dref_m"].to_numpy()
    relative_speed = frame["lead_speed_mps"].to_numpy() - frame["vx_mps"].to_numpy()
    finite_ttc = frame.loc[frame["ttc_valid"], "ttc_s"].to_numpy()
    result = {
        "samples": int(len(frame)), "sample_span_s": float(timestamps[-1] - timestamps[0]),
        "MAE_d_m": float(np.mean(np.abs(distance_error))), "RMS_d_m": rms(distance_error),
        "MAE_relative_speed_mps": float(np.mean(np.abs(relative_speed))),
        "jerk_MAE_mps3": float(np.mean(np.abs(jerk))), "jerk_RMS_mps3": rms(jerk),
        "min_TTC_s": float(np.min(finite_ttc)) if len(finite_ttc) else None,
        "TTC_valid_samples": int(len(finite_ttc)), "acceleration_RMS_mps2": rms(frame["ax_command_mps2"]),
        "MAE_ey_m": float(np.mean(np.abs(frame["ey_m"]))), "RMS_ey_m": rms(frame["ey_m"]),
        "MAE_epsi_rad": float(np.mean(np.abs(frame["epsi_rad"]))), "RMS_epsi_rad": rms(frame["epsi_rad"]),
        "steering_command_RMS_rad": rms(frame["delta_command_rad"]),
        "steering_applied_equivalent_RMS_rad": rms(frame["delta_applied_equivalent_rad"]),
        "steering_rate_RMS_radps": rms(steering_rate),
        "alpha_shared_mean": float(frame["alpha_shared"].mean()),
        "alpha_lon_mean": float(frame["alpha_lon"].mean()),
        "alpha_lat_mean": float(frame["alpha_lat"].mean()),
        "alpha_shared_gt_0p5_ratio": float((frame["alpha_shared"] > 0.5).mean()),
        "alpha_lon_gt_0p5_ratio": float((frame["alpha_lon"] > 0.5).mean()),
        "alpha_lat_gt_0p5_ratio": float((frame["alpha_lat"] > 0.5).mean()),
        "alpha_shared_gt_0p8_ratio": float((frame["alpha_shared"] > 0.8).mean()),
        "alpha_lon_gt_0p8_ratio": float((frame["alpha_lon"] > 0.8).mean()),
        "alpha_lat_gt_0p8_ratio": float((frame["alpha_lat"] > 0.8).mean()),
    }
    return result


def saturation_statistics(mask, sample_time):
    mask = np.asarray(mask, dtype=bool)
    longest = current = 0
    for active in mask:
        current = current + 1 if active else 0
        longest = max(longest, current)
    return {"fraction": float(np.mean(mask)), "longest_duration_s": longest * sample_time}


def analyze_run(run_dir, config, execution):
    run_dir = Path(run_dir)
    frame = pd.read_csv(run_dir / "raw.csv")
    numeric_columns = frame.select_dtypes(include=[np.number]).columns.difference(["ttc_s"])
    finite = bool(np.isfinite(frame[numeric_columns].to_numpy()).all())
    ttc_consistent = bool(frame.loc[frame["ttc_valid"], "ttc_s"].notna().all()
                          and frame.loc[~frame["ttc_valid"], "ttc_s"].isna().all())
    ttc_positive = bool((frame.loc[frame["ttc_valid"], "ttc_s"] >= 0).all())
    simulation = config["simulation"]
    sample_time = simulation["fixed_delta_seconds"]
    evaluation = frame.loc[frame["evaluation_sample"]]
    enough = len(evaluation) >= 2
    path1 = bool((frame["active_path"] == "path1").any())
    out_of_radius = frame["path_source"].eq("spatial_out_of_radius")
    architecture = config["experiment"].get("alpha_architecture", "shared_sigmoid")
    shared_expected = architecture == "shared_sigmoid"
    if architecture == "system1":
        channel_alpha_check = bool((frame["alpha_lon"] == 0).all() and (frame["alpha_lat"] == 0).all())
    elif architecture == "system2":
        channel_alpha_check = bool((frame["alpha_lon"] == 1).all() and (frame["alpha_lat"] == 1).all())
    elif shared_expected:
        channel_alpha_check = bool(np.allclose(frame["alpha_shared"], frame["alpha_lon"], rtol=0, atol=0)
                                    and np.allclose(frame["alpha_shared"], frame["alpha_lat"], rtol=0, atol=0))
    elif architecture in ("threshold_shared", "linear_shared"):
        channel_alpha_check = bool(np.allclose(frame["alpha_lon"], frame["alpha_lat"], rtol=0, atol=0))
    else:
        channel_alpha_check = bool((frame["alpha_lon"].between(0, 1) & frame["alpha_lat"].between(0, 1)).all())
    if architecture in ("shared_sigmoid", "separate_sigmoid", "system1", "system2"):
        alpha_mapping_check = bool(np.allclose(
            frame["alpha_shared"],
            1 / (1 + np.exp(-config["risk"]["k"] * (frame["R_ctrl"] - config["risk"]["R_th"]))),
            rtol=0, atol=1e-12))
    elif architecture == "threshold_shared":
        alpha_mapping_check = bool(np.allclose(
            frame["alpha_lon"], (frame["R_ctrl"] >= config["risk"]["R_th"]).astype(float), rtol=0, atol=1e-12))
    elif architecture == "linear_shared":
        lower = float(config["risk"].get("linear_lower", 0.3))
        upper = float(config["risk"].get("linear_upper", 0.7))
        alpha_mapping_check = bool(np.allclose(
            frame["alpha_lon"], np.clip((frame["R_ctrl"] - lower) / (upper - lower), 0, 1), rtol=0, atol=1e-12))
    else:
        alpha_mapping_check = False
    if architecture == "separate_sigmoid":
        channel_alpha_mapping_check = bool(
            np.allclose(frame["alpha_lon"],
                        1 / (1 + np.exp(-config["risk"]["k"] * (frame["R_lon"] - config["risk"]["R_th"]))),
                        rtol=0, atol=1e-12)
            and np.allclose(frame["alpha_lat"],
                            1 / (1 + np.exp(-config["risk"]["k"] * (frame["R_lat"] - config["risk"]["R_th"]))),
                            rtol=0, atol=1e-12)
        )
    elif architecture == "shared_sigmoid":
        channel_alpha_mapping_check = bool(
            np.allclose(frame["alpha_lon"], frame["alpha_shared"], rtol=0, atol=1e-12)
            and np.allclose(frame["alpha_lat"], frame["alpha_shared"], rtol=0, atol=1e-12)
        )
    elif architecture == "system1":
        channel_alpha_mapping_check = bool((frame["alpha_lon"] == 0).all() and (frame["alpha_lat"] == 0).all())
    elif architecture == "system2":
        channel_alpha_mapping_check = bool((frame["alpha_lon"] == 1).all() and (frame["alpha_lat"] == 1).all())
    else:
        channel_alpha_mapping_check = channel_alpha_check
    residual_guard_check = residual_authority_guard_check(frame, config)
    normalized_risk_columns = ["R_d_norm", "R_v_norm", "R_kappa_norm"]
    normalized_risk_check = bool(
        all(column in frame and frame[column].between(0.0, 1.0).all() for column in normalized_risk_columns)
    )
    lateral_gain_check = lateral_vlm_gain_check(frame, config)
    checks = {
        "completed_without_exception": not execution.get("raised_error", False),
        "numeric_finite_except_undefined_TTC": finite,
        "TTC_validity_consistent": ttc_consistent and ttc_positive,
        "complete_control_sample_count": len(frame) == simulation["expected_control_samples"],
        "single_alpha_source": frame["alpha_source"].nunique() == 1 and frame["alpha_source"].iloc[0] == config["risk"]["alpha_source"],
        "alpha_in_unit_interval": bool(frame["alpha"].between(0, 1).all()),
        "risk_sum_matches_logged_contributions": bool(np.allclose(frame["R_ctrl"],
            frame["weighted_R_d"] + frame["weighted_R_v"] + frame["weighted_R_kappa"], rtol=0, atol=1e-12)),
        "alpha_mapping_matches_logged_risk": alpha_mapping_check,
        "channel_alpha_mapping_matches_logged_channel_risks": channel_alpha_mapping_check,
        "normalized_risks_in_unit_interval": normalized_risk_check,
        "lateral_vlm_gain_mapping_matches_logged_law": lateral_gain_check,
        "channel_alpha_architecture": channel_alpha_check,
        "evaluation_paths_resolved_spatially": bool(enough and evaluation["path_source"].str.startswith("spatial").all()),
        "no_out_of_radius_path_resolution": not bool(out_of_radius.any()),
        "path1_entry_when_required": path1 or config["experiment"]["scenario"] != "nominal_integrated",
        "checkpoint_loaded_and_verified": execution.get("checkpoint_loaded", False),
        "one_frame_per_control_step": bool((np.diff(frame["frame"]) == 1).all()),
        "sampling_interval": bool(np.allclose(np.diff(frame["time_s"]), sample_time, rtol=0, atol=1e-5)),
        "simulation_duration": math.isclose(execution.get("completed_simulation_duration_s", -1), simulation["duration_s"], abs_tol=config["smoke_checks"]["duration_tolerance_s"]),
        "logged_sample_span": math.isclose(float(frame["time_s"].iloc[-1] - frame["time_s"].iloc[0]), simulation["expected_logged_sample_span_s"], abs_tol=config["smoke_checks"]["duration_tolerance_s"]),
        "controller_output_bounds": bool(frame["ax_command_mps2"].between(config["controller"]["limits"]["ax_min"] - 1e-9, config["controller"]["limits"]["ax_max"] + 1e-9).all()
                                          and (frame["delta_command_rad"].abs() <= config["controller"]["limits"]["delta_max"] + 1e-9).all()
                                          and (frame["steer_applied"].abs() <= 1 + 1e-9).all()),
        "residual_authority_guard_matches_logged_law": residual_guard_check,
    }
    limits = config["controller"]["limits"]
    saturation = {}
    for scope, subset in (("full", frame), ("evaluation", evaluation)):
        if subset.empty:
            continue
        for name in ("ax_ctg", "ax_mpc", "ax_command_mps2"):
            values = subset[name].to_numpy()
            saturation[scope + "/" + name] = saturation_statistics(
                (values <= limits["ax_min"] + 1e-8) | (values >= limits["ax_max"] - 1e-8), sample_time)
        for name in ("delta_lqr", "delta_command_rad"):
            saturation[scope + "/" + name] = saturation_statistics(np.abs(subset[name]) >= limits["delta_max"] - 1e-8, sample_time)
    warnings = []
    if out_of_radius.any():
        warnings.append("Out-of-radius spatial path assignment: %d samples, max distance %.3f m" %
                        (int(out_of_radius.sum()), float(frame.loc[out_of_radius, "path_distance_m"].max())))
    for name, values in saturation.items():
        if name.startswith("evaluation/") and (
            values["fraction"] >= config["smoke_checks"]["evaluation_saturation_warning_ratio"]
            or values["longest_duration_s"] >= config["smoke_checks"]["persistent_saturation_warning_s"]
        ):
            warnings.append("Persistent evaluation saturation: " + name)
    summary = {
        "scenario": config["experiment"]["scenario"], "checks": checks,
        "technical_checks_passed": bool(all(checks.values())), "warnings": warnings,
        "full_route": performance(frame) if len(frame) >= 2 else None,
        "evaluation": performance(evaluation) if enough else None,
        "risk_distributions_full": {name: distribution(frame[name]) for name in ("R_d", "R_v", "R_kappa", "R_ctrl", "R_lon", "R_lat", "g_kappa", "alpha_shared", "alpha_lon", "alpha_lat")},
        "cross_channel_activation": cross_channel_statistics(frame),
        "cross_channel_activation_evaluation": cross_channel_statistics(evaluation) if enough else None,
        "empirical_boundedness": empirical_boundedness(frame),
        "path_sample_counts": {str(key): int(value) for key, value in frame["active_path"].value_counts().items()},
        "path_resolution": {"out_of_radius_samples": int(out_of_radius.sum()),
                            "out_of_radius_fraction": float(out_of_radius.mean()),
                            "max_distance_m": float(frame["path_distance_m"].max())},
        "saturation": saturation,
        "interpretation": "STEP1 engineering smoke, not an architecture comparison or statistical performance claim",
    }
    write_json(run_dir / "summary.json", summary)
    metrics_rows = []
    for scope in ("full_route", "evaluation"):
        if summary[scope]:
            metrics_rows.append({"scenario": summary["scenario"], "scope": scope, **summary[scope]})
    pd.DataFrame(metrics_rows).to_csv(run_dir / "summary.csv", index=False)
    return summary


def lateral_vlm_gain_check(frame, config):
    required = {"R_kappa_norm", "R_lat", "R_lat_pre_clip", "g_kappa", "w_kappa_path", "w_kappa_path_max"}
    if not required.issubset(frame.columns):
        return False
    policy = config["risk"].get("separate_lateral_vlm_gain_policy", "none")
    gain = frame["g_kappa"].to_numpy(dtype=float)
    kappa = frame["R_kappa_norm"].to_numpy(dtype=float)
    logged_pre_clip = frame["R_lat_pre_clip"].to_numpy(dtype=float)
    logged_lateral = frame["R_lat"].to_numpy(dtype=float)
    if policy == "normalized_path_max":
        expected_gain = frame["w_kappa_path"].to_numpy(dtype=float) / frame["w_kappa_path_max"].to_numpy(dtype=float)
        expected_pre_clip = expected_gain * kappa
        expected_lateral = np.clip(expected_pre_clip, 0.0, 1.0)
        return bool(
            np.all((gain >= -1e-12) & (gain <= 1.0 + 1e-12))
            and np.allclose(gain, expected_gain, rtol=0, atol=1e-12)
            and np.allclose(logged_pre_clip, expected_pre_clip, rtol=0, atol=1e-12)
            and np.allclose(logged_lateral, expected_lateral, rtol=0, atol=1e-12)
        )
    if policy == "none":
        return bool(
            np.allclose(gain, 1.0, rtol=0, atol=1e-12)
            and np.allclose(logged_pre_clip, frame["R_kappa"], rtol=0, atol=1e-12)
            and np.allclose(logged_lateral, frame["R_kappa"], rtol=0, atol=1e-12)
        )
    return False


def residual_authority_guard_check(frame, config):
    guard = config["controller"]["rl"].get("residual_authority_guard", {"enabled": False})
    if not guard.get("enabled", False):
        return True
    required = {
        "delta_lqr", "alpha_lat", "residual_filtered_rad", "residual_effective_unguarded_rad",
        "residual_effective_guarded_rad", "delta_combined_rad",
    }
    if not required.issubset(frame.columns):
        return False
    lqr = frame["delta_lqr"].to_numpy(dtype=float)
    unguarded = frame["residual_effective_unguarded_rad"].to_numpy(dtype=float)
    effective = frame["residual_effective_guarded_rad"].to_numpy(dtype=float)
    expected_unguarded = frame["alpha_lat"].to_numpy(dtype=float) * frame["residual_filtered_rad"].to_numpy(dtype=float)
    if not np.allclose(unguarded, expected_unguarded, rtol=0, atol=1e-12):
        return False
    retained_fraction = float(guard["minimum_lqr_retained_fraction"])
    lqr_floor = float(guard["lqr_floor_rad"])
    low_lqr_bound = float(guard["low_lqr_effective_bound_rad"])
    expected_effective = unguarded.copy()
    low_lqr = np.abs(lqr) < lqr_floor
    expected_effective[low_lqr] = np.clip(expected_effective[low_lqr], -low_lqr_bound, low_lqr_bound)
    opposing = ~low_lqr & (lqr * unguarded < 0)
    opposing_bound = (1 - retained_fraction) * np.abs(lqr[opposing])
    expected_effective[opposing] = np.sign(unguarded[opposing]) * np.minimum(
        np.abs(unguarded[opposing]), opposing_bound)
    combined = frame["delta_combined_rad"].to_numpy(dtype=float)
    return bool(
        np.allclose(effective, expected_effective, rtol=0, atol=1e-12)
        and np.allclose(combined, lqr + effective, rtol=0, atol=1e-12)
        and np.all(lqr[opposing] * combined[opposing] >= -1e-12)
    )


def cross_channel_statistics(frame):
    longitudinal_excess = frame["alpha_shared"] - frame["alpha_lon"]
    lateral_excess = frame["alpha_shared"] - frame["alpha_lat"]
    def one(values):
        values = np.asarray(values, dtype=float)
        return {"mean": float(values.mean()), "median": float(np.median(values)),
                "max": float(values.max()), "p95": float(np.percentile(values, 95)),
                "abs_gt_0p1_ratio": float((np.abs(values) > 0.1).mean()),
                "abs_gt_0p2_ratio": float((np.abs(values) > 0.2).mean())}
    return {"shared_minus_lon": one(longitudinal_excess), "shared_minus_lat": one(lateral_excess)}


def empirical_boundedness(frame):
    lateral_norm = np.sqrt(frame["ey_m"] ** 2 + frame["eydot_mps"] ** 2 + frame["epsi_rad"] ** 2 + frame["epsidot_radps"] ** 2)
    residual = np.abs(frame["residual_filtered_rad"])
    effective_column = "residual_effective_guarded_rad" if "residual_effective_guarded_rad" in frame else None
    effective = np.abs(frame[effective_column]) if effective_column else np.abs(frame["alpha_lat"] * frame["residual_filtered_rad"])
    lqr_abs = np.abs(frame["delta_lqr"])
    longitudinal_norm = np.sqrt((frame["d_bumper_m"] - frame["dref_m"]) ** 2 + (frame["lead_speed_mps"] - frame["vx_mps"]) ** 2)
    disagreement = np.abs(frame["ax_mpc"] - frame["ax_ctg"])
    def one(values):
        values = np.asarray(values, dtype=float)
        return {"mean": float(values.mean()), "median": float(np.median(values)), "p95": float(np.percentile(values, 95)),
                "p99": float(np.percentile(values, 99)), "max": float(values.max())}
    result = {
        "residual_over_lateral_state_norm": one(residual / np.maximum(lateral_norm, 1e-6)),
        "effective_residual_abs_rad": one(effective),
        "effective_residual_to_lqr_ratio": one(effective / np.maximum(lqr_abs, 1e-6)),
        "longitudinal_disagreement_abs_mps2": one(disagreement),
        "longitudinal_disagreement_over_state_norm": one(disagreement / np.maximum(longitudinal_norm, 1e-6)),
        "interpretation": "Empirical boundedness only; not a formal stability guarantee.",
    }
    if "residual_guard_active" in frame:
        guard_active = frame["residual_guard_active"].astype(bool).to_numpy(dtype=float)
        unguarded = np.abs(frame["residual_effective_unguarded_rad"].to_numpy(dtype=float))
        result["residual_guard_active"] = one(guard_active)
        result["guarded_to_unguarded_residual_ratio"] = one(effective / np.maximum(unguarded, 1e-6))
    return result


def plot_run(run_dir):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    run_dir = Path(run_dir)
    frame = pd.read_csv(run_dir / "raw.csv")
    figure, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
    time_values = frame["time_s"]
    groups = [
        [("d_bumper_m", "Bumper gap"), ("dref_m", "CTG reference")],
        [("ax_ctg", "CTG"), ("ax_mpc", "MPC"), ("ax_command_mps2", "Shared blend")],
        [("delta_lqr", "LQR component"), ("delta_command_rad", "Combined command"),
         ("delta_applied_equivalent_rad", "Applied equivalent")],
        [("alpha", "Shared alpha"), ("weighted_R_d", "$w_d R_d$"),
         ("weighted_R_v", "$w_v R_v$"), ("weighted_R_kappa", "$w_\\kappa R_\\kappa$")],
    ]
    for axis, curves, ylabel in zip(axes, groups, ("Distance [m]", "Acceleration [m/s²]", "Steering [rad]", "Alpha / weighted risk")):
        for column, label in curves:
            axis.plot(time_values, frame[column], label=label, linewidth=1.1)
        axis.set_ylabel(ylabel)
        axis.grid(alpha=0.25)
        axis.legend(loc="upper right", ncol=2, fontsize=8)
        axis.margins(x=0)
    axes[-1].set_xlabel("Simulation time [s]")
    figure.tight_layout()
    figure.savefig(run_dir / "smoke_timeseries.png", dpi=180)
    figure.savefig(run_dir / "smoke_timeseries.pdf")
    plt.close(figure)
