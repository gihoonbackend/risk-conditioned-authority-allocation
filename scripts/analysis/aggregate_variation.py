import numpy as np
import pandas as pd
PASSING_STATUSES = {"passed", "passed_with_warnings"}

def aggregate_variation(metrics: pd.DataFrame) -> pd.DataFrame:
    successful = metrics.loc[metrics["status"].isin(PASSING_STATUSES)].copy()
    fields = (
        "MAE_d_m", "RMS_d_m", "MAE_relative_speed_mps", "jerk_RMS_mps3", "acceleration_RMS_mps2", "min_TTC_s",
        "MAE_ey_m", "RMS_ey_m", "MAE_epsi_rad", "RMS_epsi_rad", "steering_applied_equivalent_RMS_rad",
        "steering_rate_RMS_radps", "alpha_lon_mean", "alpha_lat_mean", "R_lon_mean", "R_lat_mean", "R_kappa_mean",
        "alpha_lat_mean_path1", "alpha_lat_mean_path2", "alpha_lat_mean_path3",
    )
    rows = []
    for keys, group in successful.groupby(["scenario_id", "scenario_label", "architecture_id", "architecture_label"], sort=False):
        for metric in fields:
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy(dtype=float)
            rows.append({
                "scenario_id": keys[0], "scenario_label": keys[1], "architecture_id": keys[2], "architecture_label": keys[3],
                "metric": metric, "n_controlled_conditions": int(values.size),
                "mean": float(values.mean()) if values.size else np.nan,
                "std_population": float(values.std(ddof=0)) if values.size else np.nan,
                "min": float(values.min()) if values.size else np.nan, "max": float(values.max()) if values.size else np.nan,
            })
    return pd.DataFrame(rows)
