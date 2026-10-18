import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'controllers/runtime'))
from common import load_config
from metrics import performance
from aggregate_variation import aggregate_variation
import paper_pipeline as pipeline


def regenerate_metrics(filename):
    frame = pd.read_csv(ROOT / 'data/simulation/processed' / filename)
    for index, row in frame.iterrows():
        raw = pd.read_csv(ROOT / row['run_dir'] / 'raw.csv.gz')
        selected = raw.loc[raw['evaluation_sample']].copy()
        values = performance(selected)
        values.update({column + '_mean': float(selected[column].mean()) for column in ('R_lon', 'R_lat', 'R_kappa', 'g_kappa')})
        for path in ('path1', 'path2', 'path3'):
            values['alpha_lat_mean_' + path] = float(selected.loc[selected.active_path == path, 'alpha_lat'].mean())
        for field in frame.columns:
            if field in values:
                expected, actual = row[field], values[field]
                if not (pd.isna(expected) and pd.isna(actual)) and not np.isclose(expected, actual, rtol=1e-10, atol=1e-10):
                    raise ValueError('Archived metric mismatch: %s/%s' % (row['job_id'], field))
                frame.loc[index, field] = actual
    return frame


def regenerate_replay():
    result, metadata = pipeline.replay(load_config())
    expected = pd.read_csv(ROOT / 'data/vehicle/processed/recorded_state_replay_vlm_lateral_gain.csv')
    pd.testing.assert_frame_equal(result, expected, check_dtype=False, rtol=1e-10, atol=1e-10)
    destination = ROOT / 'generated/replay'
    destination.mkdir(parents=True, exist_ok=True)
    result.to_csv(destination / 'recorded_state_replay_vlm_lateral_gain.csv', index=False)
    (destination / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return result


def generate_tables():
    main = regenerate_metrics('main_metrics.csv')
    variation = regenerate_metrics('variation_individual_metrics.csv')
    aggregated = aggregate_variation(variation)
    expected = pd.read_csv(ROOT / 'data/simulation/processed/variation_mean_std.csv')
    pd.testing.assert_frame_equal(aggregated, expected, check_dtype=False, rtol=1e-10, atol=1e-10)
    replay = regenerate_replay()
    outputs = pipeline.performance_tables(main, aggregated, replay)
    for table_id, paths in outputs.items():
        actual = pd.read_csv(ROOT / paths['csv'])
        archived = pd.read_csv(ROOT / 'data/tables' / (table_id + '.csv'))
        pd.testing.assert_frame_equal(actual, archived, check_dtype=False, rtol=1e-10, atol=1e-10)
    (ROOT / 'generated/tables/reproduction_check.json').write_text(json.dumps({
        'status': 'passed', 'main_runs': len(main), 'variation_runs': len(variation),
        'matching_tables': list(outputs), 'tolerance': {'rtol': 1e-10, 'atol': 1e-10},
        'source': 'archived complete trajectories and archived replay input signals'}, indent=2) + '\n')
    print('PASS: six final tables reproduce from 36 trajectories and V3 replay inputs')


def generate_figures(number=None):
    pipeline.configure_style()
    original_save = pipeline.save_figure
    if number is not None:
        def selective_save(figure, stem):
            if not stem.startswith('fig%02d_' % number):
                pipeline.plt.close(figure)
                return {}
            return original_save(figure, stem)
        pipeline.save_figure = selective_save
    if number is None or number in {6, 7, 8, 9}:
        main = pd.read_csv(ROOT / 'data/simulation/processed/main_metrics.csv')
        pipeline.build_main_figures(main)
    if number is None or number == 10:
        pipeline.build_replay_figure(regenerate_replay())
    print('Figures generated in generated/figures/')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['tables', 'figures', 'replay', 'all'])
    args = parser.parse_args()
    if args.action in {'tables', 'all'}:
        generate_tables()
    if args.action in {'figures', 'all'}:
        generate_figures()
    if args.action == 'replay':
        regenerate_replay()


if __name__ == '__main__':
    main()
