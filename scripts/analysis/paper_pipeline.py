from __future__ import annotations
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "controllers/runtime"))
from control import guard_residual_authority, steering_postprocess
PAPER_FIGURES = ROOT / "generated/figures"
PAPER_TABLES = ROOT / "generated/tables"
REAL_SOURCE_CSV = ROOT / "data/vehicle/processed/replay_source_signals.csv.gz"
REAL_SOURCE_PDF = ROOT / "figures/fig10_recorded_state_replay_vlm_lateral_gain.pdf"
REAL_LAYOUT_SCRIPT = ROOT / "scripts/analysis/paper_pipeline.py"
PASSING = {"passed", "passed_with_warnings"}
COLORS = {
    "ctg": "#1f77b4", "mpc": "#ff7f0e", "proposed": "#9467bd", "shared": "#202020",
    "lqr": "#d62728", "alpha_lon": "#1f77b4", "alpha_lat": "#d95f02",
    "risk_d": "#6c757d", "risk_v": "#4c9bb0", "risk_kappa": "#6a994e",
}
PATH_COLORS = {"path1": "#eaf2ff", "path2": "#fff4ea", "path3": "#eef8f0"}
def rel(path):
    return str(path.relative_to(ROOT))

def configure_style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Serif", "mathtext.fontset": "dejavuserif", "font.size": 8.6,
        "axes.titlesize": 10.2, "axes.labelsize": 8.8, "xtick.labelsize": 7.8, "ytick.labelsize": 7.8,
        "legend.fontsize": 7.3, "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.75, "grid.alpha": 0.25, "grid.linewidth": 0.55,
        "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.bbox": "tight",
    })


def save_figure(figure: plt.Figure, stem: str) -> dict:
    PAPER_FIGURES.mkdir(parents=True, exist_ok=True)
    png = PAPER_FIGURES / (stem + ".png")
    pdf = PAPER_FIGURES / (stem + ".pdf")
    figure.savefig(png, dpi=320, bbox_inches="tight")
    figure.savefig(pdf, bbox_inches="tight")
    plt.close(figure)
    return {"png": rel(png), "pdf": rel(pdf)}


def sigmoid(values: np.ndarray, k: float, threshold: float) -> np.ndarray:
    arguments = k * (np.asarray(values, dtype=float) - threshold)
    answer = np.empty_like(arguments, dtype=float)
    positive = arguments >= 0.0
    answer[positive] = 1.0 / (1.0 + np.exp(-arguments[positive]))
    negative_exp = np.exp(arguments[~positive])
    answer[~positive] = negative_exp / (1.0 + negative_exp)
    return answer


def sample_at_control_period(frame: pd.DataFrame, period_s: float) -> pd.DataFrame:
    bins = np.floor(frame["time_s"].to_numpy(dtype=float) / period_s + 1e-9).astype(np.int64)
    return frame.loc[~pd.Series(bins).duplicated().to_numpy()].reset_index(drop=True)


def standardize(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    deviation = float(np.nanstd(values))
    return np.zeros_like(values) if deviation < 1e-12 else (values - float(np.nanmean(values))) / deviation


def path_assignment(time_values: np.ndarray) -> np.ndarray:
    starts = np.asarray([25.0, 75.0, 125.0], dtype=float)
    names = np.asarray(["path1", "path2", "path3"], dtype=object)
    indexes = np.clip(np.searchsorted(starts, time_values, side="right") - 1, 0, len(names) - 1)
    return names[indexes]


def path_spans(frame: pd.DataFrame) -> list[tuple[str, float, float]]:
    time_values = frame["relative_time_s"].to_numpy(dtype=float)
    values = frame["active_path"].astype(str).to_numpy()
    spans: list[tuple[str, float, float]] = []
    if not len(values):
        return spans
    start = 0
    for index in range(1, len(values) + 1):
        if index == len(values) or values[index] != values[start]:
            end = float(time_values[index - 1])
            if end <= time_values[start] and len(time_values) > 1:
                end = float(time_values[start] + np.median(np.diff(time_values)))
            spans.append((values[start], float(time_values[start]), end))
            start = index
    return spans


def add_path_bands(axes: list[plt.Axes], frame: pd.DataFrame) -> None:
    for path, start, end in path_spans(frame):
        for axis in axes:
            axis.axvspan(start, end, color=PATH_COLORS.get(path, "#f3f3f3"), alpha=0.78, zorder=0)


def raw_path(metrics: pd.DataFrame, scenario: str, architecture: str) -> Path:
    selected = metrics.loc[(metrics["scenario_id"] == scenario) & (metrics["architecture_id"] == architecture)]
    if len(selected) != 1:
        raise RuntimeError("Expected one raw trajectory for %s/%s" % (scenario, architecture))
    record = selected.iloc[0]
    if str(record["status"]) not in PASSING:
        raise RuntimeError("Required run did not pass: " + str(record["run_dir"]))
    return ROOT / str(record["run_dir"]) / "raw.csv.gz"


def evaluation_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    selected = frame["evaluation_sample"].astype(str).str.lower().isin({"true", "1", "yes"})
    output = frame.loc[selected].copy().reset_index(drop=True)
    if output.empty:
        raise RuntimeError("No evaluation rows: " + str(path))
    output["relative_time_s"] = output["time_s"] - float(output["time_s"].iloc[0])
    return output


def replay(configuration: dict) -> tuple[pd.DataFrame, dict]:
    source = pd.read_csv(REAL_SOURCE_CSV).sort_values("time_s").reset_index(drop=True)
    period = float(configuration["simulation"]["fixed_delta_seconds"])
    source = sample_at_control_period(source, period)
    risk = configuration["risk"]
    weights = json.loads(Path(configuration["artifacts"]["vlm_weights"]["absolute_path"]).read_text())["by_path"]
    time_values = source["time_s"].to_numpy(dtype=float)
    paths = path_assignment(time_values)
    weight_d = np.asarray([weights[path]["weights"]["w_d"] for path in paths], dtype=float)
    weight_v = np.asarray([weights[path]["weights"]["w_v"] for path in paths], dtype=float)
    weight_kappa = np.asarray([weights[path]["weights"]["w_kappa"] for path in paths], dtype=float)
    max_weight_kappa = max(float(weights[path]["weights"]["w_kappa"]) for path in ("path1", "path2", "path3"))
    active_sum = weight_d + weight_v + weight_kappa
    distance = np.maximum(source["lead_distance_m"].to_numpy(dtype=float), float(risk["distance_floor_m"]))
    speed = source["ego_speed_rear_mps"].to_numpy(dtype=float)
    lead_speed = source["lead_speed_proxy_mps"].to_numpy(dtype=float)
    raw_kappa = source["kappa_signed"].to_numpy(dtype=float)
    path_gain = np.asarray([risk["path_gains"][path] for path in paths], dtype=float)
    used_kappa = np.clip(path_gain * raw_kappa, -float(risk["kappa_clip"]), float(risk["kappa_clip"]))
    risk_d = np.clip(float(risk["d_safe_m"]) / distance, 0.0, 1.0)
    risk_v = np.clip(np.abs(lead_speed - speed) / np.maximum(np.abs(speed), float(risk["speed_floor_mps"])), 0.0, 1.0)
    risk_kappa = np.clip(np.abs(used_kappa) / float(risk["kappa_scale"]), 0.0, 1.0)
    shared_d = weight_d / active_sum
    shared_v = weight_v / active_sum
    shared_kappa = weight_kappa / active_sum
    risk_shared = shared_d * risk_d + shared_v * risk_v + shared_kappa * risk_kappa
    risk_lon = (weight_d * risk_d + weight_v * risk_v) / (weight_d + weight_v)
    g_kappa = weight_kappa / max_weight_kappa
    risk_lat_preclip = g_kappa * risk_kappa
    risk_lat = np.clip(risk_lat_preclip, 0.0, 1.0)
    alpha_shared = sigmoid(risk_shared, float(risk["k"]), float(risk["R_th"]))
    alpha_lon = sigmoid(risk_lon, float(risk["k"]), float(risk["R_th"]))
    alpha_lat = sigmoid(risk_lat, float(risk["k"]), float(risk["R_th"]))
    previous_lqr = previous_proposed = 0.0
    lqr, proposed, effective, guard = [], [], [], []
    for index, row in source.iterrows():
        lqr_raw = float(row["delta_lqr_rad"])
        residual_filtered = float(row["delta_residual_rad"])
        ey, epsi = float(row["ey_centered_m"]), float(row["epsi_rad"])
        lqr_post = steering_postprocess(lqr_raw, ey, epsi, previous_lqr, configuration["controller"]["steering_postprocess"], period)
        authority = guard_residual_authority(lqr_raw, float(alpha_lat[index]), residual_filtered, configuration["controller"]["rl"])
        proposed_post = steering_postprocess(lqr_raw + authority["residual_effective_guarded_rad"], ey, epsi,
                                              previous_proposed, configuration["controller"]["steering_postprocess"], period)
        previous_lqr, previous_proposed = lqr_post["steer_applied"], proposed_post["steer_applied"]
        lqr.append(lqr_post["delta_command_rad"])
        proposed.append(proposed_post["delta_command_rad"])
        effective.append(authority["residual_effective_guarded_rad"])
        guard.append(authority["residual_guard_active"])
    output = pd.DataFrame({
        "time_s": time_values, "relative_time_s": time_values - time_values[0], "active_path": paths,
        "ax_ctg_mps2": source["ax_ctg"].to_numpy(dtype=float), "ax_mpc_mps2": source["ax_mpc"].to_numpy(dtype=float),
        "ax_separate_alpha_mps2": (1.0 - alpha_lon) * source["ax_ctg"].to_numpy(dtype=float) + alpha_lon * source["ax_mpc"].to_numpy(dtype=float),
        "delta_lqr_postprocessed_rad": lqr, "delta_separate_alpha_postprocessed_rad": proposed,
        "residual_effective_guarded_rad": effective, "residual_guard_active": guard,
        "logged_steering_trend_zscore": standardize(source["steer_measured_aligned_rad"].to_numpy(dtype=float)),
        "R_d_norm": risk_d, "R_v_norm": risk_v, "R_kappa_norm": risk_kappa, "R_shared": risk_shared,
        "R_lon": risk_lon, "R_lat_pre_clip": risk_lat_preclip, "R_lat": risk_lat, "g_kappa": g_kappa,
        "w_kappa_path": weight_kappa, "w_kappa_path_max": max_weight_kappa, "alpha_shared": alpha_shared,
        "alpha_lon": alpha_lon, "alpha_lat": alpha_lat,
    })
    metadata = {
        "source_pdf_layout_reference": rel(REAL_SOURCE_PDF), "source_layout_script": rel(REAL_LAYOUT_SCRIPT),
        "source_controller_output_csv": rel(REAL_SOURCE_CSV), "sample_period_s": period,
        "path_assignment": {"method": "fixed logged-time bins", "starts_s": {"path1": 25.0, "path2": 75.0, "path3": 125.0}},
        "formula": "R_lon=(w_d*R_d+w_v*R_v)/(w_d+w_v); g_kappa=w_kappa/max_q(w_kappa); R_lat=clip(g_kappa*R_kappa,0,1)",
        "scope": "Recorded-state open-loop controller-output replay; logged states are not propagated through a vehicle model.",
        "steering_scope": "Logged steering is a standardized trend reference, not a physical steering-angle accuracy metric.",
    }
    return output, metadata


def build_replay_figure(frame: pd.DataFrame) -> dict:
    figure, axes = plt.subplots(3, 1, figsize=(7.16, 5.85), sharex=True, gridspec_kw={"height_ratios": [1.0, 1.0, 1.08]})
    add_path_bands(list(axes), frame)
    time_values = frame["relative_time_s"]
    axes[0].plot(time_values, frame["ax_ctg_mps2"], color=COLORS["ctg"], linewidth=1.3, label="CTG")
    axes[0].plot(time_values, frame["ax_mpc_mps2"], color=COLORS["mpc"], linewidth=1.3, label="MPC")
    axes[0].plot(time_values, frame["ax_separate_alpha_mps2"], color=COLORS["proposed"], linewidth=1.8,
                 label="Separate-$\\alpha$ CTG--MPC")
    axes[0].set_title("(a) Acceleration Outputs", loc="left", fontweight="bold", pad=7)
    axes[0].set_ylabel("acc [m/s$^2$]")
    axes[0].legend(loc="upper right", ncol=3, frameon=True, framealpha=0.95)
    axes[1].plot(time_values, frame["delta_lqr_postprocessed_rad"], color=COLORS["lqr"], linewidth=1.3, label="LQR")
    axes[1].plot(time_values, frame["delta_separate_alpha_postprocessed_rad"], color=COLORS["proposed"], linewidth=1.8,
                 label="LQR + $\\alpha_{\\mathrm{lat}}$ RL residual")
    axes[1].axhline(0.0, color="0.4", linewidth=0.7)
    trend = axes[1].twinx()
    trend.plot(time_values, frame["logged_steering_trend_zscore"], color="#242424", linewidth=0.9, linestyle="--",
               label="Logged steering trend (z-score)")
    axes[1].set_title("(b) Steering Outputs and Logged Trend", loc="left", fontweight="bold", pad=7)
    axes[1].set_ylabel("controller command [rad]")
    trend.set_ylabel("standardized trend [--]", fontsize=7.5)
    handles, labels = axes[1].get_legend_handles_labels(); right, right_labels = trend.get_legend_handles_labels()
    axes[1].legend(handles + right, labels + right_labels, loc="upper right", ncol=2, fontsize=6.8, framealpha=0.95)
    axes[2].plot(time_values, frame["R_lon"], color="#7b8794", linewidth=1.1, linestyle="-.", label="$R_{\\mathrm{lon}}$")
    axes[2].plot(time_values, frame["R_lat"], color=COLORS["risk_kappa"], linewidth=1.1, linestyle="-.", label="$R_{\\mathrm{lat}}$")
    axes[2].plot(time_values, frame["alpha_lon"], color=COLORS["alpha_lon"], linewidth=1.8, label="$\\alpha_{\\mathrm{lon}}$")
    axes[2].plot(time_values, frame["alpha_lat"], color=COLORS["alpha_lat"], linewidth=1.8, linestyle="--", label="$\\alpha_{\\mathrm{lat}}$")
    axes[2].set_title("(c) Channel-Specific Risk and Authority", loc="left", fontweight="bold", pad=7)
    axes[2].set_ylabel("risk / authority [--]"); axes[2].set_xlabel("recorded time [s]"); axes[2].set_ylim(-0.03, 1.03)
    axes[2].legend(loc="upper right", ncol=2, framealpha=0.95, fontsize=7.0)
    for axis in axes:
        axis.grid(alpha=0.22, linestyle="--", linewidth=0.55); axis.margins(x=0)
    figure.text(0.5, 0.005, r"Replay lateral gain: $g_\kappa=w_\kappa^{(p)}/\max_q w_\kappa^{(q)}$ (Path 1/2/3: 1.000/0.583/0.417).",
                ha="center", fontsize=7.2)
    figure.tight_layout(rect=(0.0, 0.035, 1.0, 1.0))
    return save_figure(figure, "fig10_recorded_state_replay_vlm_lateral_gain")


def risk_authority_panel(axis_alpha: plt.Axes, axis_risk: plt.Axes, frame: pd.DataFrame, title: str, include_shared: bool) -> None:
    time_values = frame["relative_time_s"]
    for column, label, color in (("alpha_lon", "$\\alpha_{\\mathrm{lon}}$", COLORS["alpha_lon"]),
                                 ("alpha_lat", "$\\alpha_{\\mathrm{lat}}$", COLORS["alpha_lat"])):
        axis_alpha.plot(time_values, frame[column], linewidth=1.75, linestyle="--" if column == "alpha_lat" else "-", color=color, label=label)
    if include_shared:
        axis_alpha.plot(time_values, frame["alpha_shared"], linewidth=1.45, linestyle=":", color=COLORS["shared"], label="$\\alpha_{\\mathrm{shared}}$")
    for column, label, color in (("R_d_norm", "$R_d$", COLORS["risk_d"]), ("R_v_norm", "$R_v$", COLORS["risk_v"]),
                                 ("R_kappa_norm", "$R_\\kappa$", COLORS["risk_kappa"])):
        axis_risk.plot(time_values, frame[column], linewidth=1.05, alpha=0.85, color=color, label=label)
    axis_risk.plot(time_values, frame["R_lon"], linewidth=1.15, linestyle="-.", color="#7b8794", label="$R_{\\mathrm{lon}}$")
    axis_risk.plot(time_values, frame["R_lat"], linewidth=1.15, linestyle="-.", color="#2a9d8f", label="$R_{\\mathrm{lat}}$")
    for axis, ylabel in ((axis_alpha, "authority [--]"), (axis_risk, "risk [--]")):
        axis.set_ylim(-0.03, 1.03); axis.set_ylabel(ylabel); axis.grid(True); axis.margins(x=0)
    axis_alpha.set_title(title, loc="left", pad=7)


def build_main_figures(metrics: pd.DataFrame) -> dict:
    nominal_s1 = evaluation_frame(raw_path(metrics, "nominal", "system1"))
    nominal_s2 = evaluation_frame(raw_path(metrics, "nominal", "system2"))
    nominal_separate = evaluation_frame(raw_path(metrics, "nominal", "separate"))
    emergency_separate = evaluation_frame(raw_path(metrics, "emergency", "separate"))
    high_separate = evaluation_frame(raw_path(metrics, "high_curvature", "separate"))
    figures = {}
    fig, axes = plt.subplots(4, 1, figsize=(7.16, 6.35), sharex=True)
    add_path_bands(list(axes), nominal_separate)
    for frame, label, color in ((nominal_s1, "CTG", COLORS["ctg"]), (nominal_s2, "MPC", COLORS["mpc"]),
                                (nominal_separate, "Separate-$\\alpha$ blend", COLORS["proposed"])):
        axes[0].plot(frame["relative_time_s"], frame["d_bumper_m"] - frame["dref_m"], label=label, color=color, linewidth=1.35)
        axes[1].plot(frame["relative_time_s"], frame["lead_speed_mps"] - frame["vx_mps"], label=label, color=color, linewidth=1.35)
        axes[2].plot(frame["relative_time_s"], frame["ax_command_mps2"], label=label, color=color, linewidth=1.35)
    axes[3].plot(nominal_separate["relative_time_s"], nominal_separate["alpha_lon"], color=COLORS["alpha_lon"], linewidth=1.8, label="$\\alpha_{\\mathrm{lon}}$")
    for axis, title, ylabel in zip(axes, ("Distance Tracking Error", "Relative Speed", "Commanded Acceleration", "Longitudinal Blending Weight"),
                                   ("error [m]", "m/s", "m/s$^2$", "authority [--]")):
        axis.set_title(title, loc="left", pad=7); axis.set_ylabel(ylabel); axis.grid(True); axis.margins(x=0)
    axes[3].set_ylim(-0.03, 1.03); axes[3].set_xlabel("evaluation time [s]")
    axes[0].legend(loc="upper right", ncol=3, fontsize=7.0); axes[3].legend(loc="upper right")
    fig.tight_layout(); figures["fig06_nominal_longitudinal_vlm_lateral_gain"] = save_figure(fig, "fig06_nominal_longitudinal_vlm_lateral_gain")
    fig, axes = plt.subplots(4, 1, figsize=(7.16, 6.35), sharex=True)
    add_path_bands(list(axes), nominal_separate)
    for frame, label, color in ((nominal_s1, "LQR", COLORS["lqr"]), (nominal_separate, "LQR + $\\alpha_{\\mathrm{lat}}$ RL residual", COLORS["proposed"])):
        axes[0].plot(frame["relative_time_s"], frame["ey_m"], label=label, color=color, linewidth=1.35)
        axes[1].plot(frame["relative_time_s"], frame["epsi_rad"], label=label, color=color, linewidth=1.35)
        axes[2].plot(frame["relative_time_s"], frame["delta_applied_equivalent_rad"], label=label, color=color, linewidth=1.35)
    axes[3].plot(nominal_separate["relative_time_s"], nominal_separate["alpha_lat"], color=COLORS["alpha_lat"], linewidth=1.8, linestyle="--", label="$\\alpha_{\\mathrm{lat}}$")
    for axis, title, ylabel in zip(axes, ("Lateral Position Error", "Heading Error", "Steering Command", "Lateral Blending Weight"),
                                   ("m", "rad", "rad", "authority [--]")):
        axis.set_title(title, loc="left", pad=7); axis.set_ylabel(ylabel); axis.grid(True); axis.margins(x=0)
    axes[3].set_ylim(-0.03, 1.03); axes[3].set_xlabel("evaluation time [s]")
    axes[0].legend(loc="upper right", fontsize=7.0); axes[3].legend(loc="upper right")
    fig.tight_layout(); figures["fig07_nominal_lateral_vlm_lateral_gain"] = save_figure(fig, "fig07_nominal_lateral_vlm_lateral_gain")
    fig, axes = plt.subplots(2, 2, figsize=(7.16, 5.25), sharex="col")
    risk_authority_panel(axes[0, 0], axes[1, 0], nominal_separate, "(a) Nominal Following", False)
    risk_authority_panel(axes[0, 1], axes[1, 1], emergency_separate, "(b) Emergency Stop", False)
    axes[1, 0].set_xlabel("evaluation time [s]"); axes[1, 1].set_xlabel("evaluation time [s]")
    handles, labels = axes[0, 0].get_legend_handles_labels(); rh, rl = axes[1, 0].get_legend_handles_labels()
    fig.legend(handles + rh, labels + rl, loc="upper center", ncol=5, bbox_to_anchor=(0.5, 1.02), frameon=False, fontsize=7.0)
    fig.text(0.5, 0.002, r"Lateral VLM gain: $g_\kappa=w_\kappa^{(p)}/\max_q w_\kappa^{(q)}$ (1.000, 0.583, 0.417 for Path 1--3).", ha="center", fontsize=7.2)
    fig.tight_layout(rect=(0.0, 0.035, 1.0, 0.91)); figures["fig08_channel_specific_risk_authority"] = save_figure(fig, "fig08_channel_specific_risk_authority")
    fig, axes = plt.subplots(2, 2, figsize=(7.16, 5.25), sharex="col")
    risk_authority_panel(axes[0, 0], axes[1, 0], emergency_separate, "(a) Emergency Stop", True)
    risk_authority_panel(axes[0, 1], axes[1, 1], high_separate, "(b) High Curvature / Low Longitudinal Risk", True)
    axes[1, 0].set_xlabel("evaluation time [s]"); axes[1, 1].set_xlabel("evaluation time [s]")
    handles, labels = axes[0, 0].get_legend_handles_labels(); rh, rl = axes[1, 0].get_legend_handles_labels()
    fig.legend(handles + rh, labels + rl, loc="upper center", ncol=6, bbox_to_anchor=(0.5, 1.02), frameon=False, fontsize=6.8)
    fig.text(0.5, 0.002, "Dotted shared authority is a diagnostic baseline evaluated on the same Separate-alpha trajectory.", ha="center", fontsize=7.2)
    fig.tight_layout(rect=(0.0, 0.035, 1.0, 0.91)); figures["fig09_shared_vs_separate_asymmetric_risk"] = save_figure(fig, "fig09_shared_vs_separate_asymmetric_risk")
    return figures


def rms(values: pd.Series | np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.asarray(values, dtype=float) ** 2)))


def replay_metric_frame(replay_frame: pd.DataFrame) -> pd.DataFrame:
    proposed_trend = standardize(replay_frame["delta_separate_alpha_postprocessed_rad"].to_numpy())
    lqr_trend = standardize(replay_frame["delta_lqr_postprocessed_rad"].to_numpy())
    logged = replay_frame["logged_steering_trend_zscore"].to_numpy(dtype=float)
    return pd.DataFrame([{
        "CTG output RMS [m/s^2]": rms(replay_frame["ax_ctg_mps2"]),
        "MPC output RMS [m/s^2]": rms(replay_frame["ax_mpc_mps2"]),
        "Separate blend RMS [m/s^2]": rms(replay_frame["ax_separate_alpha_mps2"]),
        "mean alpha_lon": float(replay_frame["alpha_lon"].mean()),
        "LQR command RMS [rad]": rms(replay_frame["delta_lqr_postprocessed_rad"]),
        "Proposed command RMS [rad]": rms(replay_frame["delta_separate_alpha_postprocessed_rad"]),
        "mean alpha_lat": float(replay_frame["alpha_lat"].mean()),
        "LQR standardized trend MAE": float(np.mean(np.abs(lqr_trend - logged))),
        "Proposed standardized trend MAE": float(np.mean(np.abs(proposed_trend - logged))),
        "Proposed trend Pearson r": float(np.corrcoef(proposed_trend, logged)[0, 1]),
    }])


def latex_table(frame: pd.DataFrame, destination: Path, caption: str, label: str) -> None:
    columns = list(frame.columns)
    header = " & ".join(column.replace("_", r"\_") for column in columns) + r" \\"
    lines = [r"\begin{table*}[t]", r"\centering", "\\caption{%s}" % caption, "\\label{%s}" % label,
             r"\scriptsize", r"\resizebox{\textwidth}{!}{%", r"\begin{tabular}{" + "l" * len(columns) + "}", r"\toprule", header, r"\midrule"]
    for _, row in frame.iterrows():
        values = []
        for value in row:
            if pd.isna(value): values.append("--")
            elif isinstance(value, (float, np.floating)): values.append("%.5f" % value)
            else: values.append(str(value).replace("_", r"\_"))
        lines.append(" & ".join(values) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}%", r"}", r"\end{table*}"]
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_table(table_id: str, frame: pd.DataFrame, caption: str, label: str) -> dict:
    PAPER_TABLES.mkdir(parents=True, exist_ok=True)
    csv_path = PAPER_TABLES / (table_id + ".csv")
    tex_path = PAPER_TABLES / (table_id + ".tex")
    md_path = PAPER_TABLES / (table_id + ".md")
    frame.to_csv(csv_path, index=False, na_rep="")
    latex_table(frame, tex_path, caption, label)
    display_frame = frame.where(frame.notna(), "—")
    md_path.write_text("# " + table_id + "\n\n" + display_frame.to_markdown(index=False) + "\n", encoding="utf-8")
    return {"csv": rel(csv_path), "tex": rel(tex_path), "markdown": rel(md_path)}


def performance_tables(metrics: pd.DataFrame, variation: pd.DataFrame | None, replay_frame: pd.DataFrame) -> dict:
    outputs = {}
    selected = ["architecture_label", "MAE_d_m", "RMS_d_m", "MAE_relative_speed_mps", "jerk_RMS_mps3", "min_TTC_s", "acceleration_RMS_mps2", "alpha_lon_mean"]
    nominal_lon = metrics.loc[(metrics["scenario_id"] == "nominal") & metrics["architecture_id"].isin(["system1", "system2", "separate"]), selected]
    outputs["table_nominal_longitudinal"] = write_table("table_nominal_longitudinal", nominal_lon,
        "Nominal longitudinal metrics from the archived Canonical-D v3 architecture runs.", "tab:nominal_longitudinal_v3")
    selected = ["architecture_label", "MAE_ey_m", "RMS_ey_m", "MAE_epsi_rad", "RMS_epsi_rad", "steering_applied_equivalent_RMS_rad", "steering_rate_RMS_radps", "alpha_lat_mean"]
    nominal_lat = metrics.loc[(metrics["scenario_id"] == "nominal") & metrics["architecture_id"].isin(["system1", "separate"]), selected]
    outputs["table_nominal_lateral"] = write_table("table_nominal_lateral", nominal_lat,
        "Nominal lateral metrics from the archived Canonical-D v3 architecture runs.", "tab:nominal_lateral_v3")
    selected = ["scenario_label", "architecture_label", "MAE_d_m", "jerk_RMS_mps3", "min_TTC_s", "MAE_ey_m", "MAE_epsi_rad", "steering_applied_equivalent_RMS_rad"]
    ablation = metrics.loc[metrics["architecture_id"].isin(["shared", "separate"]), selected]
    outputs["table_shared_vs_separate"] = write_table("table_shared_vs_separate", ablation,
        "Canonical-D v3 shared-alpha baseline and proposed channel-specific authority comparison. Undefined TTC is reported as --.", "tab:shared_separate_v3")
    if variation is not None:
        compact = variation.loc[variation["metric"].isin(["MAE_d_m", "jerk_RMS_mps3", "min_TTC_s", "MAE_ey_m", "steering_applied_equivalent_RMS_rad", "alpha_lon_mean", "alpha_lat_mean"])]
        outputs["table_controlled_variation"] = write_table("table_controlled_variation", compact,
            "Controlled lead-speed variation (13--17 m/s): population mean and standard deviation across deterministic conditions.", "tab:controlled_variation_v3")
    residual_rows = []
    for _, row in metrics.loc[metrics["architecture_id"] == "separate"].iterrows():
        raw = pd.read_csv(ROOT / row["run_dir"] / "raw.csv.gz")
        evaluation = raw.loc[raw["evaluation_sample"].astype(bool)]
        effective = np.abs(evaluation["residual_effective_guarded_rad"].to_numpy(dtype=float))
        filtered = np.abs(evaluation["residual_filtered_rad"].to_numpy(dtype=float))
        residual_rows.append({
            "Scenario": row["scenario_label"], "Samples": len(evaluation),
            "p95 |alpha_lat residual| [rad]": float(np.percentile(np.abs(evaluation["residual_effective_unguarded_rad"]), 95)),
            "max |alpha_lat residual| [rad]": float(np.max(np.abs(evaluation["residual_effective_unguarded_rad"]))),
            "p95 |effective residual| [rad]": float(np.percentile(effective, 95)), "max |effective residual| [rad]": float(effective.max()),
            "p95 |filtered residual| [rad]": float(np.percentile(filtered, 95)),
            "guard-active ratio": float(evaluation["residual_guard_active"].astype(bool).mean()),
        })
    outputs["table_empirical_residual_boundedness"] = write_table("table_empirical_residual_boundedness", pd.DataFrame(residual_rows),
        "Empirical boundedness statistics of the proposed residual contribution; these are not a formal stability proof.", "tab:residual_boundedness_v3")
    replay_table = replay_metric_frame(replay_frame)
    outputs["table_recorded_state_replay"] = write_table("table_recorded_state_replay", replay_table,
        "Recorded-state open-loop controller-output replay. Standardized steering trends are not physical steering-angle errors.", "tab:recorded_state_replay_v3")
    return outputs
