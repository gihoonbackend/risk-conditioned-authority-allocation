# Implemented Canonical-D V3 method

This release describes the recorded implementation, including distinctions relevant to interpreting the manuscript.

## Risk and context

For active path p, the pre-existing geometric gain h is 40, 20, 1 for Paths 1, 2, 3 (warmup: 1). Define

```text
kappa_used = clip(h[p] * kappa_raw, -0.3, 0.3)
R_d = clip(15.0 / max(d_bumper, 0.1), 0, 1)
R_v = clip(abs(v_lead - v_ego) / max(abs(v_ego), 1.0), 0, 1)
R_kappa = clip(abs(kappa_used) / 0.05, 0, 1)
tilde_w_d = w_d / (w_d + w_v)
tilde_w_v = w_v / (w_d + w_v)
R_lon = tilde_w_d * R_d + tilde_w_v * R_v
g_kappa[p] = w_kappa[p] / max_q(w_kappa[q])
R_lat = clip(g_kappa[p] * R_kappa, 0, 1)
alpha_c = 1 / (1 + exp(-5.0 * (R_c - 0.5)))
```

The gain g is 1, 7/12, 5/12. It acts after the geometric gain and normalization. VLM weights are fixed archived parameters; the VLM does not generate online alpha or commands. `w_s,w_p` are excluded from both active normalizations. There is no channel risk masking in these V3 runs.

For the Shared baseline:

```text
bar_w_i = w_i / (w_d + w_v + w_kappa)
R_shared = bar_w_d*R_d + bar_w_v*R_v + bar_w_kappa*R_kappa
alpha_shared = 1 / (1 + exp(-5.0*(R_shared-0.5)))
alpha_lon = alpha_lat = alpha_shared
```

The same-state diagnostic `alpha_shared` is also logged in Separate and endpoint runs. It is not their applied coefficient. System 1 forces both applied alphas to zero; System 2 forces both to one.

## Controllers and actuation

CTG uses `d_ref=1.6*v_ego+5` and `clip(0.65*e_d+0.45*(e_d-e_d_previous)/0.05,-4,3)`. The derivative is zero at initialization. It is a finite difference of spacing error, not a direct relative-speed feedback substitution.

The C++ MPC uses a horizon of 20 at 0.05 s, stage weights `(1,1,5)`, a constant 15 m/s speed reference, and ten finite-difference projected-gradient iterations. It has acceleration bounds but no terminal cost/set or soft constraints. See the archived resolved config for step size and finite-difference epsilon. It is not a claim of recursive feasibility or a formal MPC stability theorem.

Longitudinal acceleration is `(1-alpha_lon)*a_CTG+alpha_lon*a_MPC`. Throttle/brake use the existing 3 m/s² pedal scale. LQR model/tuning and six-dimensional residual policy settings are preserved in the config. Residual filtering is amplitude saturation → slew limit → LPF → amplitude saturation. Alpha scaling → residual-authority guard → addition to LQR → deadbands/soft scaling/clipping → CARLA normalization/rate limiting/LPF then follow. Thus the applied steering is not simply the unguarded algebraic sum.

## Metrics and evaluation

CARLA main metrics use 1500 samples at t in `[25,100)` s. MAE/RMS spacing uses logged bumper gap minus the controller reference; relative-speed MAE uses `v_lead-v_ego`. Jerk is the first difference of commanded acceleration divided by adjacent logged time intervals. Steering-rate RMS is the difference of `delta_applied_equivalent_rad` divided by those intervals. Rates have N−1 samples and do not cross run boundaries.

TTC is `d_bumper/(v_ego-v_lead)` only when closing speed exceeds 0.001 m/s. There is no maximum TTC clipping. Undefined min TTC is left missing, never zero. The high-curvature diagnostic has no valid TTC samples. Controlled-speed aggregation uses five per-run values and population standard deviation, not pooled time samples or random-seed confidence intervals.

The nominal figures/tables use System-1, System-2 and Separate architecture runs. Longitudinal and lateral state histories may both differ; these should not be described as strictly isolated, matched-state single-channel interventions. Fig. 9 overlays counterfactual shared and actual separate authority on the same Separate trajectory. The architecture table instead compares independent Shared/Separate closed-loop runs.

Recorded vehicle states are not propagated. Replay reuses archived base controller outputs/residuals, recomputes the V3 maps and postprocessing, and measures standardized steering trend differences. Its upstream raw-to-output history is incompletely archived. See the vehicle README.
