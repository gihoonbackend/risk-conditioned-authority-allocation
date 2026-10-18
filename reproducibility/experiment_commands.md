# Command provenance and reproduction levels

## 1. Exact archived argv (normalized executable)

Each completed run's manifest records the command arguments below. The interpreter's local installation path is replaced by its basename and the private working directory is omitted. No shell environment prefix was archived with argv. Seed settings are recorded in each resolved config.

Main batch `20260928T055908_868958Z`:

```bash
python3 revision_experiments/canonical_d_vlm_lateral_gain/run_vlm_lateral_gain.py --execute-main
```

Controlled-speed batch `20260928T060553_058951Z`:

```bash
python3 revision_experiments/canonical_d_vlm_lateral_gain/run_vlm_lateral_gain.py --execute-variation
```

These are historical research-tree commands, not paths in this standalone package. Their per-run normalized argv is preserved in `data/simulation/raw/<run_id>/manifest.json`. Only completed V3 rows from these batches were selected.

## 2. Reconstructed equivalent package commands

Offline reproduction, verified during packaging:

```bash
python scripts/tables/generate_paper_tables.py
python scripts/analysis/reproduce.py figures
python scripts/analysis/reproduce.py replay
python scripts/analysis/validate_package.py
```

Individual figure scripts are `scripts/figures/generate_fig06.py` through `generate_fig10.py`. All generated files go under `generated/`.

Inspect an exact archived CARLA job configuration without executing it:

```bash
python scripts/run/run_experiment.py --list
python scripts/run/run_experiment.py --job-id main__nominal__separate
```

After obtaining permission for and installing the exact checkpoint, and starting a dedicated CARLA 0.9.15 server on the configured port (2100):

```bash
python -m pip install -r requirements-simulation.txt
PYTHONHASHSEED=42 python scripts/run/run_experiment.py --job-id main__nominal__separate --execute
```

Repeat with the 36 exact job IDs in the index to reproduce a full suite. These commands use archived resolved settings, original V3 execution logic, portable path resolution and unique `generated/runs/` output directories. They are reconstructed equivalents and were not run against CARLA during packaging. The execution loop reloads Town04 and clears vehicles; use a dedicated simulator instance.

## 3. Not available

- Exact historical residual-policy training command and all training hyperparameters.
- Full API HTTP request/options used for historical VLM generation beyond saved prompts, model identifier and response records.
- Exact upstream raw-vehicle-to-processed-controller-output command and complete calibration/centering/interpolation history.
- A guaranteed portable archived simulator launch command. CARLA binaries/maps and Unreal installation are not distributed.

These gaps are not filled with current defaults. Archived generated signals remain sufficient for the verified offline reproduction boundary.
