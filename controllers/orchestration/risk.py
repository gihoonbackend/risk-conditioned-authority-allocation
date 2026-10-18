import json
import math

import numpy as np


class RiskModel:
    def __init__(self, config):
        self.config = config["risk"]
        if self.config["formulation"] not in ("ORIGINAL", "NORMALIZED"):
            raise ValueError("Unknown risk formulation")
        if self.config["active_weight_policy"] not in ("CURRENT", "RENORMALIZED"):
            raise ValueError("Unknown active-weight policy")
        modes = {"all": ("d", "v", "kappa"), "dv": ("d", "v"), "kappa": ("kappa",)}
        if self.config["alpha_component_mode"] not in modes:
            raise ValueError("Unknown component mask")
        self.active = modes[self.config["alpha_component_mode"]]
        self.separate_risk_definition = self.config.get("separate_risk_definition", "legacy_effective_weights")
        if self.separate_risk_definition not in ("legacy_effective_weights", "channel_normalized"):
            raise ValueError("Unknown separate-risk definition")
        self.separate_lateral_vlm_gain_policy = self.config.get("separate_lateral_vlm_gain_policy", "none")
        if self.separate_lateral_vlm_gain_policy not in ("none", "normalized_path_max"):
            raise ValueError("Unknown separate lateral VLM gain policy")
        canonical_ids = {
            "canonical_D_normalized_active_weight_renormalized_v1",
            "canonical_D_normalized_active_weight_renormalized_v2_distance_calibrated",
            "canonical_D_normalized_active_weight_renormalized_v3_vlm_lateral_gain",
        }
        if self.config.get("canonical_risk_id") in canonical_ids:
            if self.config["formulation"] != "NORMALIZED":
                raise ValueError("Canonical D requires NORMALIZED components")
            if self.config["active_weight_policy"] != "RENORMALIZED":
                raise ValueError("Canonical D requires active-weight renormalization")
            if self.active != modes["all"]:
                raise ValueError("Canonical D requires the active set {d, v, kappa}")
            if self.separate_risk_definition != "channel_normalized":
                raise ValueError("Canonical D requires channel-normalized separate risks")
        if self.config.get("canonical_risk_id") == "canonical_D_normalized_active_weight_renormalized_v3_vlm_lateral_gain":
            if self.separate_lateral_vlm_gain_policy != "normalized_path_max":
                raise ValueError("Canonical D v3 requires normalized path-maximum lateral VLM gain")
        self.architecture = config["experiment"].get("alpha_architecture", "shared_sigmoid")
        if self.architecture not in ("shared_sigmoid", "separate_sigmoid", "threshold_shared", "linear_shared",
                                     "system1", "system2"):
            raise ValueError("Unknown alpha architecture")
        with open(config["artifacts"]["vlm_weights"]["absolute_path"]) as stream:
            payload = json.load(stream)
        self.weights = payload["by_path"]
        for name in ("path1", "path2", "path3"):
            vector = self.weights[name]["weights"]
            values = [float(vector["w_" + key]) for key in ("d", "v", "kappa", "s", "p")]
            if not all(math.isfinite(value) and 0 <= value <= 1 for value in values):
                raise ValueError("Invalid VLM weights for " + name)
            if not math.isclose(sum(values), 1.0, abs_tol=1e-8):
                raise ValueError("Stored five weights do not sum to one")
            if sum(vector["w_" + key] for key in self.active) <= 0:
                raise ValueError("Selected active weights have zero total")
        self.max_path_w_kappa = max(float(self.weights[name]["weights"]["w_kappa"])
                                    for name in ("path1", "path2", "path3"))
        if self.max_path_w_kappa <= 0:
            raise ValueError("Path-wise curvature weights must contain a positive maximum")

    def compute(self, distance, speed, lead_speed, raw_kappa, path):
        if not all(math.isfinite(value) for value in (distance, speed, lead_speed, raw_kappa)):
            raise ValueError("Nonfinite risk input")
        if path not in self.config["path_gains"]:
            raise ValueError("No curvature gain for active path: " + str(path))
        weight_path = self.config["path_resolution"]["warmup_weight_path"] if path == "warmup" else path
        weights = self.weights[weight_path]["weights"]
        gain = self.config["path_gains"][path]
        used_kappa = float(np.clip(gain * raw_kappa, -self.config["kappa_clip"], self.config["kappa_clip"]))
        raw = {
            "d": self.config["d_safe_m"] / max(distance, self.config["distance_floor_m"]),
            "v": abs(lead_speed - speed) / max(abs(speed), self.config["speed_floor_mps"]),
            "kappa": abs(used_kappa) / self.config["kappa_scale"],
        }
        active_sum = sum(weights["w_" + key] for key in self.active)
        divisor = active_sum if self.config["active_weight_policy"] == "RENORMALIZED" else 1.0
        output = {"alpha_source": self.config["alpha_source"], "weight_path": weight_path,
                  "kappa_used": used_kappa, "kappa_gain": gain, "active_weight_sum_before": active_sum}
        risk = 0.0
        for key in ("d", "v", "kappa"):
            normalized_component = float(np.clip(raw[key], 0, 1))
            component = normalized_component if self.config["formulation"] == "NORMALIZED" else raw[key]
            weight = weights["w_" + key] / divisor if key in self.active else 0.0
            contribution = weight * component
            output.update({"R_" + key + "_original": raw[key], "R_" + key + "_raw": raw[key],
                           "R_" + key + "_norm": normalized_component, "R_" + key: component,
                           "w_" + key + "_original": weights["w_" + key],
                           "w_" + key: weight, "weighted_R_" + key: contribution})
            risk += contribution
        output["w_s_original"] = weights["w_s"]
        output["w_p_original"] = weights["w_p"]
        output["active_weight_sum_after"] = sum(output["w_" + key] for key in self.active)
        def sigmoid(value):
            argument = self.config["k"] * (value - self.config["R_th"])
            return 1 / (1 + math.exp(-argument)) if argument >= 0 else math.exp(argument) / (1 + math.exp(argument))

        if self.separate_risk_definition == "channel_normalized":
            longitudinal_keys = tuple(key for key in ("d", "v") if key in self.active)
            longitudinal_weight_sum = sum(weights["w_" + key] for key in longitudinal_keys)
            if longitudinal_weight_sum <= 0:
                longitudinal_risk = 0.0
            else:
                longitudinal_risk = sum(weights["w_" + key] * output["R_" + key]
                                        for key in longitudinal_keys) / longitudinal_weight_sum
            if "kappa" not in self.active:
                lateral_gain = 0.0
                lateral_risk_pre_clip = 0.0
                lateral_risk = 0.0
            elif self.separate_lateral_vlm_gain_policy == "normalized_path_max":
                lateral_gain = float(weights["w_kappa"] / self.max_path_w_kappa)
                lateral_risk_pre_clip = lateral_gain * output["R_kappa_norm"]
                lateral_risk = float(np.clip(lateral_risk_pre_clip, 0.0, 1.0))
            else:
                lateral_gain = 1.0
                lateral_risk_pre_clip = output["R_kappa"]
                lateral_risk = output["R_kappa"]
            output.update({
                "separate_longitudinal_weight_sum": longitudinal_weight_sum,
                "separate_w_d": weights["w_d"] / longitudinal_weight_sum if "d" in longitudinal_keys else 0.0,
                "separate_w_v": weights["w_v"] / longitudinal_weight_sum if "v" in longitudinal_keys else 0.0,
                "separate_w_kappa": lateral_gain,
            })
        else:
            longitudinal_risk = output["weighted_R_d"] + output["weighted_R_v"]
            lateral_risk = output["weighted_R_kappa"]
            lateral_gain = 1.0
            lateral_risk_pre_clip = lateral_risk
        alpha_shared = sigmoid(risk)
        if self.architecture == "shared_sigmoid":
            alpha_lon = alpha_lat = alpha_shared
        elif self.architecture == "separate_sigmoid":
            alpha_lon, alpha_lat = sigmoid(longitudinal_risk), sigmoid(lateral_risk)
        elif self.architecture == "threshold_shared":
            alpha_lon = alpha_lat = float(risk >= self.config["R_th"])
        elif self.architecture == "linear_shared":
            lower = float(self.config.get("linear_lower", 0.3))
            upper = float(self.config.get("linear_upper", 0.7))
            if not upper > lower:
                raise ValueError("linear_upper must exceed linear_lower")
            alpha_lon = alpha_lat = float(np.clip((risk - lower) / (upper - lower), 0, 1))
        elif self.architecture == "system1":
            alpha_lon = alpha_lat = 0.0
        else:
            alpha_lon = alpha_lat = 1.0
        output.update({"R_ctrl": risk, "R_lon": longitudinal_risk, "R_lat": lateral_risk,
                       "R_lat_pre_clip": lateral_risk_pre_clip,
                       "g_kappa": lateral_gain,
                       "w_kappa_path": weights["w_kappa"],
                       "w_kappa_path_max": self.max_path_w_kappa,
                       "separate_lateral_vlm_gain_policy": self.separate_lateral_vlm_gain_policy,
                       "alpha": alpha_shared, "alpha_shared": alpha_shared,
                       "alpha_lon": alpha_lon, "alpha_lat": alpha_lat,
                       "alpha_architecture": self.architecture})
        return output


class PathResolver:
    def __init__(self, config):
        with open(config["artifacts"]["path_reference"]["absolute_path"]) as stream:
            reference = json.load(stream)
        if reference.get("position_source") != "ego":
            raise ValueError("Path reference is not built from ego positions")
        self.paths = []
        self.entered_path1 = False
        self.warmup_end = config["simulation"]["evaluation_start_s"]
        self.out_of_radius_policy = config["risk"]["path_resolution"].get("out_of_radius_policy", "fail")
        if self.out_of_radius_policy not in ("fail", "nearest_with_violation_log"):
            raise ValueError("Unknown out-of-radius path policy")
        for path in reference["paths"]:
            segments = path.get("segments") or [path["points"]]
            arrays = [np.asarray(points, dtype=float)[:, :2] for points in segments if len(points) >= 2]
            if not arrays or not all(np.isfinite(points).all() for points in arrays):
                raise ValueError("Invalid path geometry")
            starts = np.concatenate([points[:-1] for points in arrays])
            ends = np.concatenate([points[1:] for points in arrays])
            radius = path.get("match_radius", reference["global_match_radius"])
            self.paths.append((path["name"], starts, ends, float(radius)))

    def resolve(self, position, time_s=0.0):
        point = np.asarray(position, dtype=float)
        best_name = None
        best_distance = float("inf")
        nearest_distance = float("inf")
        nearest_name = None
        for name, starts, ends, radius in self.paths:
            vectors = ends - starts
            denominators = np.sum(vectors * vectors, axis=1)
            projection = np.clip(np.sum((point - starts) * vectors, axis=1) / np.maximum(denominators, 1e-12), 0, 1)
            distance = float(np.min(np.linalg.norm(point - (starts + projection[:, None] * vectors), axis=1)))
            nearest_distance = min(nearest_distance, distance)
            if distance == nearest_distance:
                nearest_name = name
            if distance <= radius and distance < best_distance:
                best_name, best_distance = name, distance
        if best_name is not None:
            self.entered_path1 = self.entered_path1 or best_name == "path1"
            return best_name, "spatial", best_distance
        if self.out_of_radius_policy == "nearest_with_violation_log" and (self.entered_path1 or time_s >= self.warmup_end):
            self.entered_path1 = self.entered_path1 or nearest_name == "path1"
            return nearest_name, "spatial_out_of_radius", nearest_distance
        if self.entered_path1 or time_s >= self.warmup_end:
            raise RuntimeError("Spatial path resolution failed outside allowed warmup; nearest distance %.3f m" % nearest_distance)
        return "warmup", "explicit_pre_path1_warmup", nearest_distance
