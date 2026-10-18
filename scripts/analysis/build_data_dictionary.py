import json
from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

SIGNALS = {
    'time_s': ('s', 'Original relative elapsed time in the respective sequence; simulation and replay have different origins.'),
    'relative_time_s': ('s', 'Time relative to the first retained replay/evaluation sample.'),
    'snapshot_elapsed_seconds': ('s', 'CARLA snapshot elapsed timestamp before per-run origin subtraction.'),
    'wall_elapsed_s': ('s', 'Wall-clock duration measured since this run started.'),
    'frame': ('count', 'CARLA snapshot frame index.'), 'step': ('count', 'Zero-based control step index.'),
    'evaluation_sample': ('bool', 'Archived inclusion mask for metric evaluation; do not replace it by rounded timestamps.'),
    'path1_started': ('bool', 'Whether the spatial path resolver has entered Path 1.'),
    'active_path': ('label', 'Spatial path in CARLA; fixed logged-time segment in vehicle replay.'),
    'weight_path': ('label', 'Path whose fixed VLM weights are used, including explicit warmup mapping.'),
    'path_source': ('label', 'Path resolver source/status (spatial match or explicit warmup).'),
    'path_distance_m': ('m', 'Distance from ego map position to selected/nearest reference polyline.'),
    'event_phase': ('label', 'Lead-vehicle event phase returned by the archived lead profile.'),
    'vx_mps': ('m/s', 'CARLA ego speed magnitude.'),
    'lead_speed_mps': ('m/s', 'CARLA lead speed magnitude.'),
    'lead_target_mps': ('m/s', 'Current target assigned to the CARLA lead vehicle controller.'),
    'd_center_m': ('m', 'Centerline-projected center-to-center vehicle distance with Euclidean fallback.'),
    'd_bumper_m': ('m', 'Controller distance after subtracting both vehicle half lengths.'),
    'center_to_bumper_offset_m': ('m', 'Sum of ego and lead half lengths removed from center distance.'),
    'dref_m': ('m', 'CTG reference spacing Tg*vx+d0.'), 'dref': ('m', 'C++ output alias of CTG reference spacing.'),
    'ey_m': ('m', 'Signed lane-center lateral tracking error supplied to the controller.'),
    'eydot_mps': ('m/s', 'Finite-difference lateral-error rate.'),
    'epsi_rad': ('rad', 'Signed heading error supplied to the controller; historical proxy in vehicle input.'),
    'epsidot_radps': ('rad/s', 'Finite-difference heading-error rate.'),
    'kappa_raw': ('1/m', 'Geometric curvature computed from three map centerline waypoints.'),
    'kappa_used': ('1/m', 'Geometric path gain times raw curvature clipped to [-0.3,0.3].'),
    'kappa_gain': ('1', 'Geometric path gain (40/20/1), separate from the VLM-derived lateral gain.'),
    'ax_command_mps2': ('m/s^2', 'Acceleration after longitudinal blending, before pedal conversion.'),
    'ax_measured_body_mps2': ('m/s^2', 'CARLA measured acceleration projected onto ego forward direction.'),
    'ax_ctg': ('m/s^2', 'CTG branch output; in replay an archived historical input signal.'),
    'ax_mpc': ('m/s^2', 'MPC branch output; historical replay upstream solver provenance is incomplete.'),
    'ax_ctg_mps2': ('m/s^2', 'Archived CTG replay input passed through unchanged.'),
    'ax_mpc_mps2': ('m/s^2', 'Archived MPC-labelled replay input passed through unchanged.'),
    'ax_separate_alpha_mps2': ('m/s^2', '(1-alpha_lon)*ax_ctg + alpha_lon*ax_mpc in V3 replay.'),
    'ax_measured_g': ('g (upstream label)', 'Historical logged longitudinal acceleration; raw calibration not independently confirmed.'),
    'ax_measured_mps2': ('m/s^2 (upstream)', 'Historical acceleration conversion retained without recalibration.'),
    'throttle': ('1', 'Clipped nonnegative longitudinal command divided by pedal scale.'),
    'brake': ('1', 'Clipped negative longitudinal command magnitude divided by pedal scale.'),
    'ttc_valid': ('bool', 'True only for closing speed vx-vlead > 0.001 m/s.'),
    'ttc_s': ('s', 'Bumper gap / closing speed if valid; otherwise missing.'),
    'delta_lqr': ('rad', 'Clipped C++ LQR component steering command.'),
    'delta_lqr_unlimited': ('rad', 'Unbounded -K*x LQR feedback before branch limiting.'),
    'vdot_nom': ('model-dependent', 'C++ nominal quadratic-form derivative diagnostic; not a certified stability measure.'),
    'actor_output': ('1', 'Raw actor tanh output in [-1,1].'),
    'residual_raw_rad': ('rad', 'Actor output multiplied by deployment action bound.'),
    'residual_filtered_rad': ('rad', 'Residual after saturation, slew, LPF and final saturation; before alpha scaling.'),
    'residual_effective_unguarded_rad': ('rad', 'alpha_lat times filtered residual before the authority guard.'),
    'residual_effective_guarded_rad': ('rad', 'Effective residual after alpha scaling and authority guard.'),
    'residual_guard_active': ('bool', 'Guard changed the alpha-scaled residual.'),
    'residual_guard_reason': ('label', 'Reason recorded by the residual authority guard.'),
    'delta_combined_rad': ('rad', 'LQR plus effective guarded residual before final steering processing.'),
    'delta_pre_clip_rad': ('rad', 'Steering after deadband/soft scaling, before physical steering clipping.'),
    'delta_command_rad': ('rad', 'Postprocessed physical command before CARLA normalized rate limit and LPF.'),
    'steer_applied': ('1', 'Normalized CARLA steering after rate limit, LPF and unit clipping.'),
    'delta_applied_equivalent_rad': ('rad', 'steer_applied times delta_max; an applied-equivalent command, not measured wheel angle.'),
    'steering_deadband_active': ('bool', 'Final steering deadband condition is active.'),
    'steering_clip_active': ('bool', 'Final physical command clip changed steering.'),
    'steering_soft_scale': ('1', 'Small-error steering attenuation multiplier.'),
    'alpha_source': ('label', 'Identifier of the risk/alpha implementation in the archived experiment.'),
    'alpha_architecture': ('label', 'Applied authority architecture; separate/shared sigmoid or endpoint.'),
    'alpha': ('1', 'Alias of same-state alpha_shared diagnostic, not always the applied authority.'),
    'alpha_shared': ('1', 'Sigmoid of the active-three-renormalized shared risk; diagnostic in Separate/endpoint runs.'),
    'alpha_lon': ('1', 'Actual longitudinal authority; forced 0/1 in endpoints and equal to shared coefficient in Shared runs.'),
    'alpha_lat': ('1', 'Actual lateral authority; forced 0/1 in endpoints and equal to shared coefficient in Shared runs.'),
    'R_ctrl': ('1', 'Shared risk sum of three normalized components weighted over active {d,v,kappa}.'),
    'R_shared': ('1', 'Replay alias of the shared risk calculation.'),
    'R_lon': ('1', '(w_d*R_d_norm+w_v*R_v_norm)/(w_d+w_v).'),
    'R_lat_pre_clip': ('1', 'g_kappa*R_kappa_norm before [0,1] clipping.'),
    'R_lat': ('1', 'clip(g_kappa*R_kappa_norm,0,1); V3 proposed lateral risk.'),
    'g_kappa': ('1', 'Current archived path curvature weight / maximum of all three path curvature weights.'),
    'w_kappa_path': ('1', 'Current raw path curvature weight before max normalization.'),
    'w_kappa_path_max': ('1', 'Maximum raw curvature weight across the three archived paths (0.12).'),
    'active_weight_sum_before': ('1', 'Raw w_d+w_v+w_kappa, excluding inactive weights.'),
    'active_weight_sum_after': ('1', 'Sum of shared effective active weights (one).'),
    'separate_longitudinal_weight_sum': ('1', 'Raw w_d+w_v used for longitudinal renormalization.'),
    'separate_w_d': ('1', 'w_d/(w_d+w_v).'), 'separate_w_v': ('1', 'w_v/(w_d+w_v).'),
    'separate_w_kappa': ('1', 'Alias of the V3 path-max-normalized lateral gain g_kappa.'),
    'separate_lateral_vlm_gain_policy': ('label', 'normalized_path_max for every released V3 run.'),
    'ego_speed_rear_mps': ('m/s', 'Historical ego-speed proxy from rear-wheel speeds; preserved input.'),
    'lead_distance_m': ('m', 'Historical processed lead-gap input; retained without additional interpolation.'),
    'lead_speed_proxy_mps': ('m/s', 'Historical derived lead-speed proxy; not direct lead-speed ground truth.'),
    'ey_centered_m': ('m', 'Historically centered lateral-error input; centering provenance is incomplete.'),
    'kappa_signed': ('1/m (upstream)', 'Historical signed lane-geometry curvature proxy.'),
    'dref_ctg_m': ('m', 'Historical controller reference spacing saved with replay inputs.'),
    'delta_lqr_rad': ('rad', 'Historical LQR component input reused by V3 replay.'),
    'delta_residual_rad': ('rad', 'Historical residual input treated as filtered by the V3 replay generator.'),
    'delta_lqr_postprocessed_rad': ('rad', 'Replay LQR command after V3 steering postprocessing, before normalized actuator LPF.'),
    'delta_separate_alpha_postprocessed_rad': ('rad', 'Replay LQR plus V3 guarded residual command after steering postprocessing.'),
    'steer_measured_raw_rad': ('rad (upstream)', 'Historical conversion of logged steering; calibration provenance incomplete.'),
    'steer_measured_aligned_rad': ('rad (aligned proxy)', 'Previously sign/alignment-adjusted logged steering used only for standardized trend comparison.'),
    'steer_align_k': ('upstream scaling', 'Saved multiplicative steering-alignment coefficient; not a certified steering ratio.'),
    'steer_align_b': ('upstream offset', 'Saved steering-alignment offset.'),
    'logged_steering_trend_zscore': ('1', '(aligned logged steering - mean)/population std over the replay sequence.'),
}


def meaning(column, context):
    if context == 'raw_vehicle' and column != 'time_s':
        return ('not archived', 'Raw logger numeric signal ' + column + '; calibration/physical unit not archived.',
                'vehicle logger', 'Metadata removal only; numeric token preserved.')
    if column in SIGNALS:
        unit, description = SIGNALS[column]
        return unit, description, context, 'Preserved archived value; definition above describes historical computation.'
    if column in {'ego_x','ego_y','ego_z','lead_x','lead_y'}:
        return 'm', 'Position in CARLA synthetic map coordinates; not real GPS.', 'CARLA', 'Logged simulation position.'
    match = re.fullmatch(r'R_(d|v|kappa)(?:_(original|raw|norm))?', column)
    if match:
        component, variant = match.groups()
        raw = {'d':'15/max(d_bumper,0.1)', 'v':'abs(vlead-vx)/max(abs(vx),1)',
               'kappa':'abs(clip(path_gain*kappa_raw,-0.3,0.3))/0.05'}[component]
        definition = raw if variant in {'raw','original'} else 'clip(' + raw + ',0,1)'
        return '1', definition + '; _original and _raw are raw-component aliases within V3, not obsolete-run data.',context,'Risk computation.'
    if column.startswith('weighted_R_'):
        return '1','Effective shared active weight times corresponding normalized risk component.',context,'Shared-risk contribution.'
    if re.fullmatch(r'w_(d|v|kappa|s|p)(?:_original)?',column):
        return '1',('Archived raw VLM weight.' if column.endswith('_original') else 'Shared active-three-renormalized weight; not the Separate lateral gain.'),context,'Raw weights fixed per path.'
    if column.startswith('alpha_') and ('_mean' in column or '_gt_' in column):
        return '1',('Fraction of evaluation samples with indicated alpha strictly above named threshold.' if '_gt_' in column else 'Evaluation-sample mean of indicated authority; path suffix restricts samples to that path.'),context,'Per-run evaluation; empty path subsets are missing.'
    metric_units = {'MAE_d_m':'m','RMS_d_m':'m','MAE_ey_m':'m','RMS_ey_m':'m','MAE_epsi_rad':'rad',
                    'RMS_epsi_rad':'rad','MAE_relative_speed_mps':'m/s','jerk_MAE_mps3':'m/s^3','jerk_RMS_mps3':'m/s^3',
                    'acceleration_RMS_mps2':'m/s^2','min_TTC_s':'s','steering_applied_equivalent_RMS_rad':'rad',
                    'steering_rate_RMS_radps':'rad/s'}
    if column in metric_units:
        return metric_units[column],column.replace('_',' ') + '; exact formula in methodology summary and runtime/metrics.py.',context,'Computed over archived evaluation_sample mask; differences use N-1 intervals.'
    if column in {'R_lon_mean','R_lat_mean','R_kappa_mean','g_kappa_mean'}:
        return '1','Evaluation-sample mean of '+column.removesuffix('_mean') if hasattr(str,'removesuffix') else 'Evaluation-sample mean of '+column[:-5],context,'Per-run mean.'
    if column in {'mean','median','p95','max','min','std_population'}:
        return 'row-dependent',column+' of the variable named in metric/comparison column.',context,'Across five condition values for variation; across evaluation samples for cross-channel differences; std uses ddof=0.'
    if column in {'abs_gt_0p1_ratio','abs_gt_0p2_ratio'}:
        return '1','Fraction with absolute shared-minus-channel authority difference exceeding named threshold.',context,'Per-run evaluation samples.'
    if column in {'Samples','n_controlled_conditions'}:
        return 'count','Sample count or number of nonmissing controlled conditions, as named.',context,'Count; no imputation.'
    if column.startswith(('p95 |','max |')):
        return 'rad',column+'; alpha_lat residual is before guard, effective residual is after guard, filtered residual is before alpha.',context,'Absolute-magnitude statistic over Separate evaluation samples.'
    if column=='guard-active ratio':
        return '1','Fraction of Separate evaluation samples changed by the residual guard.',context,'Boolean mean.'
    if column.endswith('RMS [m/s^2]') or column.endswith('RMS [rad]'):
        return ('m/s^2' if column.endswith('[m/s^2]') else 'rad'),column,context,'Replay sample RMS; steering is command rather than applied-equivalent.'
    if 'standardized trend MAE' in column or 'Pearson r' in column:
        return '1',column+' against standardized logged steering reference.',context,'Z-score each sequence using population std; compare retained V3 replay rows.'
    if column in {'mean alpha_lon','mean alpha_lat'}:
        return '1','Replay mean of indicated authority.',context,'Full retained replay window.'
    if column.startswith(('expected_','actual_','raw_w_','max_raw_')) or column=='zero_R_lat':
        return '1','Formula smoke diagnostic: '+column.replace('_',' ')+'.',context,'Archived analytic/smoke input or output; not a performance metric.'
    if column in {'Old Separate v2','New Separate v3','Change (new-old)'}:
        return 'row-dependent','Development-only value of metric named in same row; excluded from official results.',context,'Historical comparison copied unchanged.'
    metadata = {'scenario_id','scenario_label','architecture_id','architecture_label','job_id','run_dir','config_sha256',
                'invariant_config_sha256','status','manifest_status','warnings','comparison','metric','Metric','Scenario','path'}
    if column in metadata:
        return 'text/hash',column.replace('_',' ')+' identifies the run, row variable, status or original configuration digest.',context,'Copied metadata; run_dir rebased in public package.'
    checks = {'TTC_validity_consistent','all_checks_passed','alpha_in_unit_interval','alpha_mapping_matches_logged_risk',
              'channel_alpha_architecture','channel_alpha_mapping_matches_logged_channel_risks','checkpoint_loaded_and_verified',
              'complete_control_sample_count','completed_without_exception','controller_output_bounds',
              'evaluation_paths_resolved_spatially','lateral_vlm_gain_mapping_matches_logged_law','logged_sample_span',
              'no_out_of_radius_path_resolution','normalized_risks_in_unit_interval','numeric_finite_except_undefined_TTC',
              'one_frame_per_control_step','path1_entry_when_required','residual_authority_guard_matches_logged_law',
              'risk_sum_matches_logged_contributions','sampling_interval','simulation_duration','single_alpha_source','technical_checks_passed'}
    if column in checks:
        return 'bool','Archived validation predicate: '+column.replace('_',' ')+'.',context,'True means the named runtime/metrics.py check passed; not a control-performance score.'
    raise ValueError('Undocumented column: '+column)


def main():
    groups = {}
    for path in sorted(ROOT.rglob('*')):
        if 'generated' in path.relative_to(ROOT).parts or not path.is_file() or not path.name.endswith(('.csv','.csv.gz')):
            continue
        header = tuple(pd.read_csv(path,nrows=0).columns)
        context = 'raw_vehicle' if 'vehicle/raw' in path.as_posix() else ('development' if 'archive/development' in path.as_posix() else 'archived V3 logs/results')
        groups.setdefault((context,header),[]).append(str(path.relative_to(ROOT)))
    lines = ['# Public CSV data dictionary','',
             'Every public CSV schema is enumerated below, including compressed CSVs and the isolated development comparison. Files with the same columns share one schema. Undefined TTC and empty per-path statistics remain missing.', '',
             'Notation aliases (not fabricated CSV columns): `delta_res_filtered` means `residual_filtered_rad`; `delta_res_effective` means `residual_effective_guarded_rad`. Vehicle input `delta_residual_rad` is the archived upstream residual treated as filtered by the final replay. `alpha_shared` can be diagnostic; applied coefficients are `alpha_lon` and `alpha_lat`.', '']
    registry=[]
    for index,((context,columns),paths) in enumerate(groups.items(),start=1):
        lines.extend(['## Schema %d'%index,'',*['- `'+path+'`' for path in paths],'',
                      '| Variable | Unit | Description | Source | Processing |','|---|---|---|---|---|'])
        definitions={}
        for column in columns:
            unit,description,origin,processing=meaning(column,context)
            definitions[column]={'unit':unit,'description':description,'source':origin,'processing':processing}
            cells=[column,unit,description,origin,processing]
            lines.append('| '+' | '.join(cell.replace('|','\\|') for cell in cells)+' |')
        lines.append('')
        registry.append({'files':paths,'columns':definitions})
    (ROOT/'docs/data_dictionary.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'docs/data_dictionary.json').write_text(json.dumps(registry,indent=2)+'\n')
    print('Documented %d CSV schemas across %d files'%(len(groups),sum(len(paths) for paths in groups.values())))


if __name__=='__main__':
    main()
