# Public CSV data dictionary

Every public CSV schema is enumerated below, including compressed CSVs and the isolated development comparison. Files with the same columns share one schema. Undefined TTC and empty per-path statistics remain missing.

Notation aliases (not fabricated CSV columns): `delta_res_filtered` means `residual_filtered_rad`; `delta_res_effective` means `residual_effective_guarded_rad`. Vehicle input `delta_residual_rad` is the archived upstream residual treated as filtered by the final replay. `alpha_shared` can be diagnostic; applied coefficients are `alpha_lon` and `alpha_lat`.

## Schema 1

- `archive/development/table_old_vs_new_separate.csv`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| Scenario | text/hash | Scenario identifies the run, row variable, status or original configuration digest. | development | Copied metadata; run_dir rebased in public package. |
| Metric | text/hash | Metric identifies the run, row variable, status or original configuration digest. | development | Copied metadata; run_dir rebased in public package. |
| Old Separate v2 | row-dependent | Development-only value of metric named in same row; excluded from official results. | development | Historical comparison copied unchanged. |
| New Separate v3 | row-dependent | Development-only value of metric named in same row; excluded from official results. | development | Historical comparison copied unchanged. |
| Change (new-old) | row-dependent | Development-only value of metric named in same row; excluded from official results. | development | Historical comparison copied unchanged. |

## Schema 2

- `data/simulation/processed/cross_channel_activation.csv`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| scenario_id | text/hash | scenario id identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| scenario_label | text/hash | scenario label identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| architecture_id | text/hash | architecture id identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| architecture_label | text/hash | architecture label identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| comparison | text/hash | comparison identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| mean | row-dependent | mean of the variable named in metric/comparison column. | archived V3 logs/results | Across five condition values for variation; across evaluation samples for cross-channel differences; std uses ddof=0. |
| median | row-dependent | median of the variable named in metric/comparison column. | archived V3 logs/results | Across five condition values for variation; across evaluation samples for cross-channel differences; std uses ddof=0. |
| p95 | row-dependent | p95 of the variable named in metric/comparison column. | archived V3 logs/results | Across five condition values for variation; across evaluation samples for cross-channel differences; std uses ddof=0. |
| max | row-dependent | max of the variable named in metric/comparison column. | archived V3 logs/results | Across five condition values for variation; across evaluation samples for cross-channel differences; std uses ddof=0. |
| abs_gt_0p1_ratio | 1 | Fraction with absolute shared-minus-channel authority difference exceeding named threshold. | archived V3 logs/results | Per-run evaluation samples. |
| abs_gt_0p2_ratio | 1 | Fraction with absolute shared-minus-channel authority difference exceeding named threshold. | archived V3 logs/results | Per-run evaluation samples. |

## Schema 3

- `data/simulation/processed/formula_smoke.csv`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| path | text/hash | path identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| raw_w_kappa | 1 | Formula smoke diagnostic: raw w kappa. | archived V3 logs/results | Archived analytic/smoke input or output; not a performance metric. |
| max_raw_w_kappa | 1 | Formula smoke diagnostic: max raw w kappa. | archived V3 logs/results | Archived analytic/smoke input or output; not a performance metric. |
| expected_g_kappa | 1 | Formula smoke diagnostic: expected g kappa. | archived V3 logs/results | Archived analytic/smoke input or output; not a performance metric. |
| actual_g_kappa | 1 | Formula smoke diagnostic: actual g kappa. | archived V3 logs/results | Archived analytic/smoke input or output; not a performance metric. |
| expected_R_lat_at_R_kappa_1 | 1 | Formula smoke diagnostic: expected R lat at R kappa 1. | archived V3 logs/results | Archived analytic/smoke input or output; not a performance metric. |
| actual_R_lat_at_R_kappa_1 | 1 | Formula smoke diagnostic: actual R lat at R kappa 1. | archived V3 logs/results | Archived analytic/smoke input or output; not a performance metric. |
| expected_alpha_lat | 1 | Formula smoke diagnostic: expected alpha lat. | archived V3 logs/results | Archived analytic/smoke input or output; not a performance metric. |
| actual_alpha_lat | 1 | Formula smoke diagnostic: actual alpha lat. | archived V3 logs/results | Archived analytic/smoke input or output; not a performance metric. |
| zero_R_lat | 1 | Formula smoke diagnostic: zero R lat. | archived V3 logs/results | Archived analytic/smoke input or output; not a performance metric. |
| all_checks_passed | bool | Archived validation predicate: all checks passed. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |

## Schema 4

- `data/simulation/processed/main_metrics.csv`
- `data/simulation/processed/variation_individual_metrics.csv`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| job_id | text/hash | job id identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| scenario_id | text/hash | scenario id identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| scenario_label | text/hash | scenario label identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| architecture_id | text/hash | architecture id identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| architecture_label | text/hash | architecture label identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| status | text/hash | status identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| technical_checks_passed | bool | Archived validation predicate: technical checks passed. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| warnings | text/hash | warnings identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| run_dir | text/hash | run dir identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| config_sha256 | text/hash | config sha256 identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| invariant_config_sha256 | text/hash | invariant config sha256 identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| MAE_d_m | m | MAE d m; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| RMS_d_m | m | RMS d m; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| MAE_relative_speed_mps | m/s | MAE relative speed mps; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| jerk_MAE_mps3 | m/s^3 | jerk MAE mps3; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| jerk_RMS_mps3 | m/s^3 | jerk RMS mps3; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| min_TTC_s | s | min TTC s; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| acceleration_RMS_mps2 | m/s^2 | acceleration RMS mps2; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| MAE_ey_m | m | MAE ey m; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| RMS_ey_m | m | RMS ey m; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| MAE_epsi_rad | rad | MAE epsi rad; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| RMS_epsi_rad | rad | RMS epsi rad; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| steering_applied_equivalent_RMS_rad | rad | steering applied equivalent RMS rad; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| steering_rate_RMS_radps | rad/s | steering rate RMS radps; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| alpha_shared_mean | 1 | Evaluation-sample mean of indicated authority; path suffix restricts samples to that path. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |
| alpha_lon_mean | 1 | Evaluation-sample mean of indicated authority; path suffix restricts samples to that path. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |
| alpha_lat_mean | 1 | Evaluation-sample mean of indicated authority; path suffix restricts samples to that path. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |
| alpha_shared_gt_0p5_ratio | 1 | Fraction of evaluation samples with indicated alpha strictly above named threshold. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |
| alpha_lon_gt_0p5_ratio | 1 | Fraction of evaluation samples with indicated alpha strictly above named threshold. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |
| alpha_lat_gt_0p5_ratio | 1 | Fraction of evaluation samples with indicated alpha strictly above named threshold. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |
| alpha_shared_gt_0p8_ratio | 1 | Fraction of evaluation samples with indicated alpha strictly above named threshold. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |
| alpha_lon_gt_0p8_ratio | 1 | Fraction of evaluation samples with indicated alpha strictly above named threshold. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |
| alpha_lat_gt_0p8_ratio | 1 | Fraction of evaluation samples with indicated alpha strictly above named threshold. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |
| R_lon_mean | 1 | Evaluation-sample mean of R_lon | archived V3 logs/results | Per-run mean. |
| R_lat_mean | 1 | Evaluation-sample mean of R_lat | archived V3 logs/results | Per-run mean. |
| R_kappa_mean | 1 | Evaluation-sample mean of R_kappa | archived V3 logs/results | Per-run mean. |
| g_kappa_mean | 1 | Evaluation-sample mean of g_kappa | archived V3 logs/results | Per-run mean. |
| alpha_lat_mean_path1 | 1 | Evaluation-sample mean of indicated authority; path suffix restricts samples to that path. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |
| alpha_lat_mean_path2 | 1 | Evaluation-sample mean of indicated authority; path suffix restricts samples to that path. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |
| alpha_lat_mean_path3 | 1 | Evaluation-sample mean of indicated authority; path suffix restricts samples to that path. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |

## Schema 5

- `data/simulation/processed/technical_validation.csv`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| job_id | text/hash | job id identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| scenario_id | text/hash | scenario id identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| architecture_id | text/hash | architecture id identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| run_dir | text/hash | run dir identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| manifest_status | text/hash | manifest status identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| technical_checks_passed | bool | Archived validation predicate: technical checks passed. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| completed_without_exception | bool | Archived validation predicate: completed without exception. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| numeric_finite_except_undefined_TTC | bool | Archived validation predicate: numeric finite except undefined TTC. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| TTC_validity_consistent | bool | Archived validation predicate: TTC validity consistent. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| complete_control_sample_count | bool | Archived validation predicate: complete control sample count. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| single_alpha_source | bool | Archived validation predicate: single alpha source. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| alpha_in_unit_interval | bool | Archived validation predicate: alpha in unit interval. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| risk_sum_matches_logged_contributions | bool | Archived validation predicate: risk sum matches logged contributions. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| alpha_mapping_matches_logged_risk | bool | Archived validation predicate: alpha mapping matches logged risk. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| channel_alpha_mapping_matches_logged_channel_risks | bool | Archived validation predicate: channel alpha mapping matches logged channel risks. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| normalized_risks_in_unit_interval | bool | Archived validation predicate: normalized risks in unit interval. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| lateral_vlm_gain_mapping_matches_logged_law | bool | Archived validation predicate: lateral vlm gain mapping matches logged law. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| channel_alpha_architecture | bool | Archived validation predicate: channel alpha architecture. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| evaluation_paths_resolved_spatially | bool | Archived validation predicate: evaluation paths resolved spatially. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| no_out_of_radius_path_resolution | bool | Archived validation predicate: no out of radius path resolution. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| path1_entry_when_required | bool | Archived validation predicate: path1 entry when required. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| checkpoint_loaded_and_verified | bool | Archived validation predicate: checkpoint loaded and verified. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| one_frame_per_control_step | bool | Archived validation predicate: one frame per control step. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| sampling_interval | bool | Archived validation predicate: sampling interval. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| simulation_duration | bool | Archived validation predicate: simulation duration. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| logged_sample_span | bool | Archived validation predicate: logged sample span. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| controller_output_bounds | bool | Archived validation predicate: controller output bounds. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |
| residual_authority_guard_matches_logged_law | bool | Archived validation predicate: residual authority guard matches logged law. | archived V3 logs/results | True means the named runtime/metrics.py check passed; not a control-performance score. |

## Schema 6

- `data/simulation/processed/variation_mean_std.csv`
- `data/tables/table_controlled_variation.csv`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| scenario_id | text/hash | scenario id identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| scenario_label | text/hash | scenario label identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| architecture_id | text/hash | architecture id identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| architecture_label | text/hash | architecture label identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| metric | text/hash | metric identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| n_controlled_conditions | count | Sample count or number of nonmissing controlled conditions, as named. | archived V3 logs/results | Count; no imputation. |
| mean | row-dependent | mean of the variable named in metric/comparison column. | archived V3 logs/results | Across five condition values for variation; across evaluation samples for cross-channel differences; std uses ddof=0. |
| std_population | row-dependent | std_population of the variable named in metric/comparison column. | archived V3 logs/results | Across five condition values for variation; across evaluation samples for cross-channel differences; std uses ddof=0. |
| min | row-dependent | min of the variable named in metric/comparison column. | archived V3 logs/results | Across five condition values for variation; across evaluation samples for cross-channel differences; std uses ddof=0. |
| max | row-dependent | max of the variable named in metric/comparison column. | archived V3 logs/results | Across five condition values for variation; across evaluation samples for cross-channel differences; std uses ddof=0. |

## Schema 7

- `data/simulation/raw/20260928T055928_055510Z_nominal_following_f5594b/raw.csv.gz`
- `data/simulation/raw/20260928T055947_731172Z_nominal_following_490d26/raw.csv.gz`
- `data/simulation/raw/20260928T060007_606915Z_nominal_following_d27707/raw.csv.gz`
- `data/simulation/raw/20260928T060027_945211Z_nominal_following_96dfe1/raw.csv.gz`
- `data/simulation/raw/20260928T060047_813047Z_emergency_stop_2840ea/raw.csv.gz`
- `data/simulation/raw/20260928T060107_757885Z_emergency_stop_64133b/raw.csv.gz`
- `data/simulation/raw/20260928T060127_699880Z_emergency_stop_bd230e/raw.csv.gz`
- `data/simulation/raw/20260928T060147_594526Z_emergency_stop_56e95a/raw.csv.gz`
- `data/simulation/raw/20260928T060207_599517Z_curvature_emergency_822a5f/raw.csv.gz`
- `data/simulation/raw/20260928T060227_583489Z_curvature_emergency_08540a/raw.csv.gz`
- `data/simulation/raw/20260928T060247_584602Z_curvature_emergency_3cb99f/raw.csv.gz`
- `data/simulation/raw/20260928T060307_789593Z_curvature_emergency_b2f727/raw.csv.gz`
- `data/simulation/raw/20260928T060327_820293Z_high_curvature_low_longitudinal_risk_dee62b/raw.csv.gz`
- `data/simulation/raw/20260928T060345_459309Z_high_curvature_low_longitudinal_risk_b960ca/raw.csv.gz`
- `data/simulation/raw/20260928T060402_991443Z_high_curvature_low_longitudinal_risk_68ec0e/raw.csv.gz`
- `data/simulation/raw/20260928T060420_574975Z_high_curvature_low_longitudinal_risk_dc3cea/raw.csv.gz`
- `data/simulation/raw/20260928T060553_082262Z_nominal_following_0e7d56/raw.csv.gz`
- `data/simulation/raw/20260928T060615_000234Z_nominal_following_6118cc/raw.csv.gz`
- `data/simulation/raw/20260928T060634_891593Z_nominal_following_fdfea6/raw.csv.gz`
- `data/simulation/raw/20260928T060654_865704Z_nominal_following_dab818/raw.csv.gz`
- `data/simulation/raw/20260928T060715_193381Z_nominal_following_bb3c42/raw.csv.gz`
- `data/simulation/raw/20260928T060735_577598Z_nominal_following_3816e2/raw.csv.gz`
- `data/simulation/raw/20260928T060755_824531Z_nominal_following_41a99b/raw.csv.gz`
- `data/simulation/raw/20260928T060816_242764Z_nominal_following_3f5142/raw.csv.gz`
- `data/simulation/raw/20260928T060836_420074Z_nominal_following_30e94d/raw.csv.gz`
- `data/simulation/raw/20260928T060856_797178Z_nominal_following_d2e9fc/raw.csv.gz`
- `data/simulation/raw/20260928T060917_256256Z_emergency_stop_c42e81/raw.csv.gz`
- `data/simulation/raw/20260928T060937_513603Z_emergency_stop_186237/raw.csv.gz`
- `data/simulation/raw/20260928T060957_745617Z_emergency_stop_6baad3/raw.csv.gz`
- `data/simulation/raw/20260928T061017_868622Z_emergency_stop_b88b47/raw.csv.gz`
- `data/simulation/raw/20260928T061038_057148Z_emergency_stop_8ca96f/raw.csv.gz`
- `data/simulation/raw/20260928T061058_283614Z_emergency_stop_bd9578/raw.csv.gz`
- `data/simulation/raw/20260928T061118_471036Z_emergency_stop_b2b9f3/raw.csv.gz`
- `data/simulation/raw/20260928T061138_865496Z_emergency_stop_a82b30/raw.csv.gz`
- `data/simulation/raw/20260928T061158_983288Z_emergency_stop_697447/raw.csv.gz`
- `data/simulation/raw/20260928T061219_338811Z_emergency_stop_95935d/raw.csv.gz`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| frame | count | CARLA snapshot frame index. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| step | count | Zero-based control step index. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| time_s | s | Original relative elapsed time in the respective sequence; simulation and replay have different origins. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| snapshot_elapsed_seconds | s | CARLA snapshot elapsed timestamp before per-run origin subtraction. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| wall_elapsed_s | s | Wall-clock duration measured since this run started. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| evaluation_sample | bool | Archived inclusion mask for metric evaluation; do not replace it by rounded timestamps. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| path1_started | bool | Whether the spatial path resolver has entered Path 1. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| active_path | label | Spatial path in CARLA; fixed logged-time segment in vehicle replay. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| path_source | label | Path resolver source/status (spatial match or explicit warmup). | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| path_distance_m | m | Distance from ego map position to selected/nearest reference polyline. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ego_x | m | Position in CARLA synthetic map coordinates; not real GPS. | CARLA | Logged simulation position. |
| ego_y | m | Position in CARLA synthetic map coordinates; not real GPS. | CARLA | Logged simulation position. |
| ego_z | m | Position in CARLA synthetic map coordinates; not real GPS. | CARLA | Logged simulation position. |
| lead_x | m | Position in CARLA synthetic map coordinates; not real GPS. | CARLA | Logged simulation position. |
| lead_y | m | Position in CARLA synthetic map coordinates; not real GPS. | CARLA | Logged simulation position. |
| vx_mps | m/s | CARLA ego speed magnitude. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| lead_speed_mps | m/s | CARLA lead speed magnitude. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| lead_target_mps | m/s | Current target assigned to the CARLA lead vehicle controller. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| event_phase | label | Lead-vehicle event phase returned by the archived lead profile. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| d_center_m | m | Centerline-projected center-to-center vehicle distance with Euclidean fallback. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| d_bumper_m | m | Controller distance after subtracting both vehicle half lengths. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| center_to_bumper_offset_m | m | Sum of ego and lead half lengths removed from center distance. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| dref_m | m | CTG reference spacing Tg*vx+d0. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ey_m | m | Signed lane-center lateral tracking error supplied to the controller. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| eydot_mps | m/s | Finite-difference lateral-error rate. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| epsi_rad | rad | Signed heading error supplied to the controller; historical proxy in vehicle input. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| epsidot_radps | rad/s | Finite-difference heading-error rate. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| kappa_raw | 1/m | Geometric curvature computed from three map centerline waypoints. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ax_command_mps2 | m/s^2 | Acceleration after longitudinal blending, before pedal conversion. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ax_measured_body_mps2 | m/s^2 | CARLA measured acceleration projected onto ego forward direction. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| throttle | 1 | Clipped nonnegative longitudinal command divided by pedal scale. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| brake | 1 | Clipped negative longitudinal command magnitude divided by pedal scale. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ttc_valid | bool | True only for closing speed vx-vlead > 0.001 m/s. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ttc_s | s | Bumper gap / closing speed if valid; otherwise missing. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ax_ctg | m/s^2 | CTG branch output; in replay an archived historical input signal. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ax_mpc | m/s^2 | MPC branch output; historical replay upstream solver provenance is incomplete. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| dref | m | C++ output alias of CTG reference spacing. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| delta_lqr | rad | Clipped C++ LQR component steering command. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| delta_lqr_unlimited | rad | Unbounded -K*x LQR feedback before branch limiting. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| vdot_nom | model-dependent | C++ nominal quadratic-form derivative diagnostic; not a certified stability measure. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| actor_output | 1 | Raw actor tanh output in [-1,1]. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| residual_raw_rad | rad | Actor output multiplied by deployment action bound. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| residual_filtered_rad | rad | Residual after saturation, slew, LPF and final saturation; before alpha scaling. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| residual_effective_unguarded_rad | rad | alpha_lat times filtered residual before the authority guard. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| residual_effective_guarded_rad | rad | Effective residual after alpha scaling and authority guard. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| residual_guard_active | bool | Guard changed the alpha-scaled residual. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| residual_guard_reason | label | Reason recorded by the residual authority guard. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| delta_combined_rad | rad | LQR plus effective guarded residual before final steering processing. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| delta_pre_clip_rad | rad | Steering after deadband/soft scaling, before physical steering clipping. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| delta_command_rad | rad | Postprocessed physical command before CARLA normalized rate limit and LPF. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| steer_applied | 1 | Normalized CARLA steering after rate limit, LPF and unit clipping. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| delta_applied_equivalent_rad | rad | steer_applied times delta_max; an applied-equivalent command, not measured wheel angle. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| steering_deadband_active | bool | Final steering deadband condition is active. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| steering_soft_scale | 1 | Small-error steering attenuation multiplier. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| steering_clip_active | bool | Final physical command clip changed steering. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| alpha_source | label | Identifier of the risk/alpha implementation in the archived experiment. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| weight_path | label | Path whose fixed VLM weights are used, including explicit warmup mapping. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| kappa_used | 1/m | Geometric path gain times raw curvature clipped to [-0.3,0.3]. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| kappa_gain | 1 | Geometric path gain (40/20/1), separate from the VLM-derived lateral gain. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| active_weight_sum_before | 1 | Raw w_d+w_v+w_kappa, excluding inactive weights. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| R_d_original | 1 | 15/max(d_bumper,0.1); _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| R_d_raw | 1 | 15/max(d_bumper,0.1); _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| R_d_norm | 1 | clip(15/max(d_bumper,0.1),0,1); _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| R_d | 1 | clip(15/max(d_bumper,0.1),0,1); _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| w_d_original | 1 | Archived raw VLM weight. | archived V3 logs/results | Raw weights fixed per path. |
| w_d | 1 | Shared active-three-renormalized weight; not the Separate lateral gain. | archived V3 logs/results | Raw weights fixed per path. |
| weighted_R_d | 1 | Effective shared active weight times corresponding normalized risk component. | archived V3 logs/results | Shared-risk contribution. |
| R_v_original | 1 | abs(vlead-vx)/max(abs(vx),1); _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| R_v_raw | 1 | abs(vlead-vx)/max(abs(vx),1); _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| R_v_norm | 1 | clip(abs(vlead-vx)/max(abs(vx),1),0,1); _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| R_v | 1 | clip(abs(vlead-vx)/max(abs(vx),1),0,1); _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| w_v_original | 1 | Archived raw VLM weight. | archived V3 logs/results | Raw weights fixed per path. |
| w_v | 1 | Shared active-three-renormalized weight; not the Separate lateral gain. | archived V3 logs/results | Raw weights fixed per path. |
| weighted_R_v | 1 | Effective shared active weight times corresponding normalized risk component. | archived V3 logs/results | Shared-risk contribution. |
| R_kappa_original | 1 | abs(clip(path_gain*kappa_raw,-0.3,0.3))/0.05; _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| R_kappa_raw | 1 | abs(clip(path_gain*kappa_raw,-0.3,0.3))/0.05; _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| R_kappa_norm | 1 | clip(abs(clip(path_gain*kappa_raw,-0.3,0.3))/0.05,0,1); _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| R_kappa | 1 | clip(abs(clip(path_gain*kappa_raw,-0.3,0.3))/0.05,0,1); _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| w_kappa_original | 1 | Archived raw VLM weight. | archived V3 logs/results | Raw weights fixed per path. |
| w_kappa | 1 | Shared active-three-renormalized weight; not the Separate lateral gain. | archived V3 logs/results | Raw weights fixed per path. |
| weighted_R_kappa | 1 | Effective shared active weight times corresponding normalized risk component. | archived V3 logs/results | Shared-risk contribution. |
| w_s_original | 1 | Archived raw VLM weight. | archived V3 logs/results | Raw weights fixed per path. |
| w_p_original | 1 | Archived raw VLM weight. | archived V3 logs/results | Raw weights fixed per path. |
| active_weight_sum_after | 1 | Sum of shared effective active weights (one). | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| separate_longitudinal_weight_sum | 1 | Raw w_d+w_v used for longitudinal renormalization. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| separate_w_d | 1 | w_d/(w_d+w_v). | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| separate_w_v | 1 | w_v/(w_d+w_v). | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| separate_w_kappa | 1 | Alias of the V3 path-max-normalized lateral gain g_kappa. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| R_ctrl | 1 | Shared risk sum of three normalized components weighted over active {d,v,kappa}. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| R_lon | 1 | (w_d*R_d_norm+w_v*R_v_norm)/(w_d+w_v). | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| R_lat | 1 | clip(g_kappa*R_kappa_norm,0,1); V3 proposed lateral risk. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| R_lat_pre_clip | 1 | g_kappa*R_kappa_norm before [0,1] clipping. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| g_kappa | 1 | Current archived path curvature weight / maximum of all three path curvature weights. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| w_kappa_path | 1 | Current raw path curvature weight before max normalization. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| w_kappa_path_max | 1 | Maximum raw curvature weight across the three archived paths (0.12). | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| separate_lateral_vlm_gain_policy | label | normalized_path_max for every released V3 run. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| alpha | 1 | Alias of same-state alpha_shared diagnostic, not always the applied authority. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| alpha_shared | 1 | Sigmoid of the active-three-renormalized shared risk; diagnostic in Separate/endpoint runs. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| alpha_lon | 1 | Actual longitudinal authority; forced 0/1 in endpoints and equal to shared coefficient in Shared runs. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| alpha_lat | 1 | Actual lateral authority; forced 0/1 in endpoints and equal to shared coefficient in Shared runs. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| alpha_architecture | label | Applied authority architecture; separate/shared sigmoid or endpoint. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |

## Schema 8

- `data/tables/table_empirical_residual_boundedness.csv`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| Scenario | text/hash | Scenario identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| Samples | count | Sample count or number of nonmissing controlled conditions, as named. | archived V3 logs/results | Count; no imputation. |
| p95 \|alpha_lat residual\| [rad] | rad | p95 \|alpha_lat residual\| [rad]; alpha_lat residual is before guard, effective residual is after guard, filtered residual is before alpha. | archived V3 logs/results | Absolute-magnitude statistic over Separate evaluation samples. |
| max \|alpha_lat residual\| [rad] | rad | max \|alpha_lat residual\| [rad]; alpha_lat residual is before guard, effective residual is after guard, filtered residual is before alpha. | archived V3 logs/results | Absolute-magnitude statistic over Separate evaluation samples. |
| p95 \|effective residual\| [rad] | rad | p95 \|effective residual\| [rad]; alpha_lat residual is before guard, effective residual is after guard, filtered residual is before alpha. | archived V3 logs/results | Absolute-magnitude statistic over Separate evaluation samples. |
| max \|effective residual\| [rad] | rad | max \|effective residual\| [rad]; alpha_lat residual is before guard, effective residual is after guard, filtered residual is before alpha. | archived V3 logs/results | Absolute-magnitude statistic over Separate evaluation samples. |
| p95 \|filtered residual\| [rad] | rad | p95 \|filtered residual\| [rad]; alpha_lat residual is before guard, effective residual is after guard, filtered residual is before alpha. | archived V3 logs/results | Absolute-magnitude statistic over Separate evaluation samples. |
| guard-active ratio | 1 | Fraction of Separate evaluation samples changed by the residual guard. | archived V3 logs/results | Boolean mean. |

## Schema 9

- `data/tables/table_nominal_lateral.csv`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| architecture_label | text/hash | architecture label identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| MAE_ey_m | m | MAE ey m; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| RMS_ey_m | m | RMS ey m; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| MAE_epsi_rad | rad | MAE epsi rad; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| RMS_epsi_rad | rad | RMS epsi rad; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| steering_applied_equivalent_RMS_rad | rad | steering applied equivalent RMS rad; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| steering_rate_RMS_radps | rad/s | steering rate RMS radps; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| alpha_lat_mean | 1 | Evaluation-sample mean of indicated authority; path suffix restricts samples to that path. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |

## Schema 10

- `data/tables/table_nominal_longitudinal.csv`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| architecture_label | text/hash | architecture label identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| MAE_d_m | m | MAE d m; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| RMS_d_m | m | RMS d m; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| MAE_relative_speed_mps | m/s | MAE relative speed mps; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| jerk_RMS_mps3 | m/s^3 | jerk RMS mps3; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| min_TTC_s | s | min TTC s; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| acceleration_RMS_mps2 | m/s^2 | acceleration RMS mps2; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| alpha_lon_mean | 1 | Evaluation-sample mean of indicated authority; path suffix restricts samples to that path. | archived V3 logs/results | Per-run evaluation; empty path subsets are missing. |

## Schema 11

- `data/tables/table_recorded_state_replay.csv`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| CTG output RMS [m/s^2] | m/s^2 | CTG output RMS [m/s^2] | archived V3 logs/results | Replay sample RMS; steering is command rather than applied-equivalent. |
| MPC output RMS [m/s^2] | m/s^2 | MPC output RMS [m/s^2] | archived V3 logs/results | Replay sample RMS; steering is command rather than applied-equivalent. |
| Separate blend RMS [m/s^2] | m/s^2 | Separate blend RMS [m/s^2] | archived V3 logs/results | Replay sample RMS; steering is command rather than applied-equivalent. |
| mean alpha_lon | 1 | Replay mean of indicated authority. | archived V3 logs/results | Full retained replay window. |
| LQR command RMS [rad] | rad | LQR command RMS [rad] | archived V3 logs/results | Replay sample RMS; steering is command rather than applied-equivalent. |
| Proposed command RMS [rad] | rad | Proposed command RMS [rad] | archived V3 logs/results | Replay sample RMS; steering is command rather than applied-equivalent. |
| mean alpha_lat | 1 | Replay mean of indicated authority. | archived V3 logs/results | Full retained replay window. |
| LQR standardized trend MAE | 1 | LQR standardized trend MAE against standardized logged steering reference. | archived V3 logs/results | Z-score each sequence using population std; compare retained V3 replay rows. |
| Proposed standardized trend MAE | 1 | Proposed standardized trend MAE against standardized logged steering reference. | archived V3 logs/results | Z-score each sequence using population std; compare retained V3 replay rows. |
| Proposed trend Pearson r | 1 | Proposed trend Pearson r against standardized logged steering reference. | archived V3 logs/results | Z-score each sequence using population std; compare retained V3 replay rows. |

## Schema 12

- `data/tables/table_shared_vs_separate.csv`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| scenario_label | text/hash | scenario label identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| architecture_label | text/hash | architecture label identifies the run, row variable, status or original configuration digest. | archived V3 logs/results | Copied metadata; run_dir rebased in public package. |
| MAE_d_m | m | MAE d m; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| jerk_RMS_mps3 | m/s^3 | jerk RMS mps3; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| min_TTC_s | s | min TTC s; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| MAE_ey_m | m | MAE ey m; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| MAE_epsi_rad | rad | MAE epsi rad; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |
| steering_applied_equivalent_RMS_rad | rad | steering applied equivalent RMS rad; exact formula in methodology summary and runtime/metrics.py. | archived V3 logs/results | Computed over archived evaluation_sample mask; differences use N-1 intervals. |

## Schema 13

- `data/vehicle/processed/recorded_state_replay_vlm_lateral_gain.csv`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| time_s | s | Original relative elapsed time in the respective sequence; simulation and replay have different origins. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| relative_time_s | s | Time relative to the first retained replay/evaluation sample. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| active_path | label | Spatial path in CARLA; fixed logged-time segment in vehicle replay. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ax_ctg_mps2 | m/s^2 | Archived CTG replay input passed through unchanged. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ax_mpc_mps2 | m/s^2 | Archived MPC-labelled replay input passed through unchanged. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ax_separate_alpha_mps2 | m/s^2 | (1-alpha_lon)*ax_ctg + alpha_lon*ax_mpc in V3 replay. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| delta_lqr_postprocessed_rad | rad | Replay LQR command after V3 steering postprocessing, before normalized actuator LPF. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| delta_separate_alpha_postprocessed_rad | rad | Replay LQR plus V3 guarded residual command after steering postprocessing. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| residual_effective_guarded_rad | rad | Effective residual after alpha scaling and authority guard. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| residual_guard_active | bool | Guard changed the alpha-scaled residual. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| logged_steering_trend_zscore | 1 | (aligned logged steering - mean)/population std over the replay sequence. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| R_d_norm | 1 | clip(15/max(d_bumper,0.1),0,1); _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| R_v_norm | 1 | clip(abs(vlead-vx)/max(abs(vx),1),0,1); _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| R_kappa_norm | 1 | clip(abs(clip(path_gain*kappa_raw,-0.3,0.3))/0.05,0,1); _original and _raw are raw-component aliases within V3, not obsolete-run data. | archived V3 logs/results | Risk computation. |
| R_shared | 1 | Replay alias of the shared risk calculation. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| R_lon | 1 | (w_d*R_d_norm+w_v*R_v_norm)/(w_d+w_v). | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| R_lat_pre_clip | 1 | g_kappa*R_kappa_norm before [0,1] clipping. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| R_lat | 1 | clip(g_kappa*R_kappa_norm,0,1); V3 proposed lateral risk. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| g_kappa | 1 | Current archived path curvature weight / maximum of all three path curvature weights. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| w_kappa_path | 1 | Current raw path curvature weight before max normalization. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| w_kappa_path_max | 1 | Maximum raw curvature weight across the three archived paths (0.12). | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| alpha_shared | 1 | Sigmoid of the active-three-renormalized shared risk; diagnostic in Separate/endpoint runs. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| alpha_lon | 1 | Actual longitudinal authority; forced 0/1 in endpoints and equal to shared coefficient in Shared runs. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| alpha_lat | 1 | Actual lateral authority; forced 0/1 in endpoints and equal to shared coefficient in Shared runs. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |

## Schema 14

- `data/vehicle/processed/replay_source_signals.csv.gz`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| time_s | s | Original relative elapsed time in the respective sequence; simulation and replay have different origins. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ego_speed_rear_mps | m/s | Historical ego-speed proxy from rear-wheel speeds; preserved input. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| lead_distance_m | m | Historical processed lead-gap input; retained without additional interpolation. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| lead_speed_proxy_mps | m/s | Historical derived lead-speed proxy; not direct lead-speed ground truth. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ey_centered_m | m | Historically centered lateral-error input; centering provenance is incomplete. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| epsi_rad | rad | Signed heading error supplied to the controller; historical proxy in vehicle input. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| kappa_signed | 1/m (upstream) | Historical signed lane-geometry curvature proxy. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ax_ctg | m/s^2 | CTG branch output; in replay an archived historical input signal. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ax_mpc | m/s^2 | MPC branch output; historical replay upstream solver provenance is incomplete. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| dref_ctg_m | m | Historical controller reference spacing saved with replay inputs. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| delta_lqr_rad | rad | Historical LQR component input reused by V3 replay. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| delta_residual_rad | rad | Historical residual input treated as filtered by the V3 replay generator. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ax_measured_g | g (upstream label) | Historical logged longitudinal acceleration; raw calibration not independently confirmed. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| ax_measured_mps2 | m/s^2 (upstream) | Historical acceleration conversion retained without recalibration. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| steer_measured_raw_rad | rad (upstream) | Historical conversion of logged steering; calibration provenance incomplete. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| steer_measured_aligned_rad | rad (aligned proxy) | Previously sign/alignment-adjusted logged steering used only for standardized trend comparison. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| steer_align_k | upstream scaling | Saved multiplicative steering-alignment coefficient; not a certified steering ratio. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |
| steer_align_b | upstream offset | Saved steering-alignment offset. | archived V3 logs/results | Preserved archived value; definition above describes historical computation. |

## Schema 15

- `data/vehicle/raw/recorded_sequence.csv.gz`

| Variable | Unit | Description | Source | Processing |
|---|---|---|---|---|
| time_s | s | Original relative elapsed time in the respective sequence; simulation and replay have different origins. | raw_vehicle | Preserved archived value; definition above describes historical computation. |
| C0 | not archived | Raw logger numeric signal C0; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| C1 | not archived | Raw logger numeric signal C1; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| C2 | not archived | Raw logger numeric signal C2; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| C3 | not archived | Raw logger numeric signal C3; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| CIPV_RELATIVE_DISTANCE Value | not archived | Raw logger numeric signal CIPV_RELATIVE_DISTANCE Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| CIPV_RELATIVE_SPD Value | not archived | Raw logger numeric signal CIPV_RELATIVE_SPD Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| LatAccel Value | not archived | Raw logger numeric signal LatAccel Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| LongAccel Value | not archived | Raw logger numeric signal LongAccel Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| L_C0 Value | not archived | Raw logger numeric signal L_C0 Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| L_C1 Value | not archived | Raw logger numeric signal L_C1 Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| L_C2 Value | not archived | Raw logger numeric signal L_C2 Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| L_C3 Value | not archived | Raw logger numeric signal L_C3 Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| R_C0 Value | not archived | Raw logger numeric signal R_C0 Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| R_C1 Value | not archived | Raw logger numeric signal R_C1 Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| R_C2 Value | not archived | Raw logger numeric signal R_C2 Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| R_C3 Value | not archived | Raw logger numeric signal R_C3 Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| Speed Value | not archived | Raw logger numeric signal Speed Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| Angle Value | not archived | Raw logger numeric signal Angle Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| WHL_SPD_FL Value | not archived | Raw logger numeric signal WHL_SPD_FL Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| WHL_SPD_FR Value | not archived | Raw logger numeric signal WHL_SPD_FR Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| WHL_SPD_RL Value | not archived | Raw logger numeric signal WHL_SPD_RL Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| WHL_SPD_RR Value | not archived | Raw logger numeric signal WHL_SPD_RR Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |
| YawRt Value | not archived | Raw logger numeric signal YawRt Value; calibration/physical unit not archived. | vehicle logger | Metadata removal only; numeric token preserved. |

