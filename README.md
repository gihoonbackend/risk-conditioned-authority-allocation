# Risk-Conditioned Channel-Specific Orchestration with Offline Vision-Language Context Parameterization for Hybrid Autonomous Driving Control

Version **1.0.0** · Canonical-D V3 experiment artifacts · publication release candidate.

**Release status: LICENSE REVIEW REQUIRED.** The package is assembled for author review. Code ownership, vehicle-data redistribution permission, and synthetic-image redistribution terms must be confirmed before public upload. The RL checkpoint is withheld until its redistribution permission is established. See [release audit](reproducibility/public_release_audit.md) and [LICENSE](LICENSE).

## Overview

This package accompanies a hybrid autonomous-driving control study prepared for *Engineering Applications of Artificial Intelligence*.
CTG and MPC supply longitudinal commands, while LQR is augmented by a bounded RL steering residual.
Offline vision-language observations provide fixed path context parameters.
Separate longitudinal and lateral risk maps determine independent intervention coefficients.
The archived release contains 36 completed CARLA runs, recorded-state vehicle replay inputs, final result tables, and figure/table reproduction code.
All official results use the V3 lateral map with a VLM-derived gain.

## Architecture

- Longitudinal: CTG–MPC acceleration blending with `alpha_lon`.
- Lateral: LQR plus a filtered, guarded RL residual scaled by `alpha_lat`.
- Offline VLM context parameters: fixed archived `gpt-5.2` outputs; no online API call.
- Shared-alpha: an architecture comparison baseline using the same normalized components.

For normalized components `R_d, R_v, R_kappa` in `[0,1]`, the official V3 maps are:

```text
tilde_w_d = w_d / (w_d + w_v)
tilde_w_v = w_v / (w_d + w_v)
R_lon = tilde_w_d * R_d + tilde_w_v * R_v
g_kappa[p] = w_kappa[p] / max_q(w_kappa[q])
R_lat = clip(g_kappa[p] * R_kappa, 0, 1)
alpha_c = 1 / (1 + exp(-5.0 * (R_c - 0.5))), c in {lon, lat}

bar_w_i = w_i / (w_d + w_v + w_kappa)
R_shared = bar_w_d*R_d + bar_w_v*R_v + bar_w_kappa*R_kappa
Shared baseline: alpha_lon = alpha_lat = sigmoid(5.0*(R_shared-0.5))
```

Geometric path gains `40/20/1` precede curvature normalization and are distinct from the VLM-derived gains. The implemented residual guard and final steering postprocessing also matter. See [methodology](docs/methodology_summary.md).

## Repository Contents

| Directory | Contents |
|---|---|
| [configs](configs/README.md) | Portable V3 overlay and resolved configuration |
| [vlm](vlm/README.md) | Archived prompts, requests, responses, synthetic snapshots and weights |
| [controllers](controllers/README.md) | C++ CTG/MPC/LQR, residual inference, guards and orchestration |
| [scenarios](scenarios/README.md) | Archived scenario settings and spatial path reference |
| `data/simulation/` | Complete, losslessly compressed V3 trajectories and metric CSVs |
| [data/vehicle](data/vehicle/README.md) | De-identified raw sequence and V3 replay inputs/outputs |
| `data/tables/` | Six byte-preserved final V3 result CSVs |
| [checkpoints](checkpoints/README.md) | Checkpoint hash, deployment settings and documented availability |
| `scripts/` | Offline reproduction, conditional CARLA execution, validation and release audit |
| `figures/` | Original V3 vector PDFs and preview PNGs |
| `reproducibility/` | Run index, provenance, checksums, commands and validation reports |
| `docs/` | Equations, variable dictionary and limitations |
| `release/v1.0.0-paper-submission/` | Release pointer manifest |

## Environment

The archived runs used Python 3.8.10, NumPy 1.23.5, pandas 2.0.3, matplotlib 3.7.5 and PyTorch 2.4.1+cu118. Offline reproduction needs no CARLA server, checkpoint, GPU or external API.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Alternatively, `conda env create -f environment.yml`. [requirements-simulation.txt](requirements-simulation.txt) supplies optional CARLA 0.9.15 and Torch dependencies; a compatible CARLA server and a C++17 compiler are separate prerequisites. The environment files were checked against the installed environment; a fresh network installation was not performed during packaging.

## Experimental Scenarios

| Scenario | Archived protocol and interpretation |
|---|---|
| Nominal Following | 100 s simulation, evaluation `[25,100)` s; four architectures |
| Emergency Stop | Same evaluation window; archived lead deceleration/hold settings |
| Curvature + Emergency | Curved-route emergency event; archived per-scenario resolved config |
| High-Curvature Diagnostic | Evaluation `3.4–4.0` s, 13 samples; authority allocation diagnostic |
| Controlled Lead-Speed Variation | 13,14,15,16,17 m/s; Nominal/Emergency, Shared/Separate; 20 runs |

CARLA runs use Town04, synchronous 20 Hz stepping (`0.05 s`). Seeds for Python, NumPy and Torch are 42. No global CARLA physics seed was set. The five speeds represent controlled operating conditions, not five random seeds. [Run index](reproducibility/run_index.json) links each result to its exact configuration and trajectory.

## Reproducing Tables

```bash
python scripts/tables/generate_paper_tables.py
```

This recomputes metrics from all 36 full trajectories, rebuilds the V3 replay, aggregates the five speeds with population standard deviation (`ddof=0`), and compares every generated final table to its archived CSV. CSV, Markdown and LaTeX outputs are written under `generated/tables/`. [Figure/table mapping](reproducibility/figure_table_mapping.md) gives the publication roles.

## Reproducing Figures

```bash
python scripts/figures/generate_fig06.py
python scripts/figures/generate_fig07.py
python scripts/figures/generate_fig08.py
python scripts/figures/generate_fig09.py
python scripts/figures/generate_fig10.py
```

These generate vector PDF and preview PNG files under `generated/figures/`, preserving the archived plot style. To reproduce all tables and figures in one invocation:

```bash
python scripts/analysis/reproduce.py all
python scripts/analysis/validate_package.py
```

Original results under `data/` and `figures/` are never overwritten. Reproduction uses repository-relative inputs and works from any working directory when scripts are addressed by their full filesystem path.

## Vehicle-Log Replay

[Vehicle data documentation](data/vehicle/README.md) distinguishes the de-identified raw logger sequence from the historical controller/state signals and final V3 replay. `python scripts/analysis/reproduce.py replay` reproduces the final V3 output from the archived replay inputs. The previous raw-to-controller-output transformation is not fully reconstructable from the saved provenance and is explicitly outside this verified reproduction boundary.

The logged steering reference is standardized. Its trend MAE/correlation does not measure physical steering-angle accuracy, and the recorded states do not evolve in response to recomputed controls. **This replay is not a closed-loop on-road validation.**

## VLM Context Parameters

| Path | `w_d` | `w_v` | `w_kappa` | `tilde_w_d` | `tilde_w_v` | `g_kappa` |
|---|---:|---:|---:|---:|---:|---:|
| Path 1 — Tight Curve | 0.360 | 0.340 | 0.120 | 0.514286 | 0.485714 | 1.000000 |
| Path 2 — Mild Curve | 0.370 | 0.340 | 0.070 | 0.521127 | 0.478873 | 0.583333 |
| Path 3 — Straight | 0.380 | 0.340 | 0.050 | 0.527778 | 0.472222 | 0.416667 |

Model identifier: `gpt-5.2`. Exact model revision and historical temperature: **unknown**. `top_p`, seed and other generation settings: **not explicitly archived**. Current generator defaults are not evidence of historical settings. The complete saved system/user prompts and response text are included. `w_s,w_p` are retained in the original five-weight response but excluded from active online risk. The final V3 simulation and replay use this same weight artifact. No VLM re-query is required.

## Reproducibility

| Source artifact | Archived SHA256 |
|---|---|
| V3 overlay config | `ffa5c585bbcf4e100b23e6725466e713d1b7a135606272bed9e39c2927b5446f` |
| VLM weights | `cf694e526e0b02dd0814c3bab7090bc9a5e2c9df0f5594a8360a867be1aa5464` |
| RL checkpoint | `91f9634d7e5f5ed27c27ce82944ae339737ba1a7f906d13c2aa16e80aec5de16` |
| Spatial path reference | `583ce47326225e502d4c48128cfd6aaba14fb0d73faaf573553bddd5ebe31e22` |

Public JSON path sanitization changes file hashes but preserves weights/settings; source and distributed hashes are separately recorded in [artifact provenance](reproducibility/artifact_provenance.json). Each scenario and run config has its own hash in [release manifest](reproducibility/release_manifest_v1.0.0.json). The source git revision does not fully identify the dirty/untracked experiment tree; file hashes and runtime source snapshots provide the stronger provenance.

```bash
sha256sum -c reproducibility/checksums.sha256
python scripts/run/run_experiment.py --list
```

Conditional simulator commands and historical command confidence levels appear in [experiment commands](reproducibility/experiment_commands.md). Packaging did not rerun or tune an experiment.

## Data Availability

Included: all 16 main and 20 controlled-variation V3 trajectories, final CSV metrics, replay outputs and inputs, de-identified numeric raw vehicle sequence, VLM records and synthetic snapshots. Files use lossless gzip where helpful. No raw real-road imagery, CARLA binary, optimizer cache or failed run is included. The checkpoint is withheld pending redistribution approval; its absence does not block offline figure/table reproduction.

## Citation

Authors: Gihoon Song, Hyeongjun Park, Guntae Kim, Minchang Kim and Changmook Kang. Cite the title shown above, reproducibility package version 1.0.0. [CITATION.cff](CITATION.cff) records the associated manuscript and intended journal. A DOI, acceptance status and repository URL have not been invented.

## License

**LICENSE REVIEW REQUIRED.** [LICENSE](LICENSE) distinguishes pending code and data terms; [NOTICE](NOTICE) records third-party provenance. MIT/BSD-3-Clause for original code and CC BY 4.0 for data are proposed options only. They are not granted by this draft. Owners/institution must approve redistribution before publication.

## Limitations

The high-curvature run is a short diagnostic. Nominal channel figures reuse complete architecture runs rather than matched-state channel-only reruns. Shared authority in Fig. 9 is evaluated on the Separate trajectory, while the main ablation table uses distinct closed-loop runs. Residual statistics support empirical boundedness only. Replay inputs include historical proxies and aligned steering; their upstream provenance is incomplete. See [known limitations](docs/known_limitations.md) for these and release constraints.
