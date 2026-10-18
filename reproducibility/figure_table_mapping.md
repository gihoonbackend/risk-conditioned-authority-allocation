# Figure and table mapping

The source of truth is the final V3 output set. Main batch: `20260928T055908_868958Z`; speed-variation batch: `20260928T060553_058951Z`. `run_index.json` resolves run IDs to full trajectories and configs.

| Paper artifact | Archived file | Generator | Inputs |
|---|---|---|---|
| Fig. 6 — Nominal longitudinal | `figures/fig06_nominal_longitudinal_vlm_lateral_gain.pdf` (+ PNG) | `scripts/figures/generate_fig06.py` | Main nominal System 1, System 2, Separate trajectories |
| Fig. 7 — Nominal lateral | `figures/fig07_nominal_lateral_vlm_lateral_gain.pdf` (+ PNG) | `scripts/figures/generate_fig07.py` | Main nominal System 1 and Separate trajectories |
| Fig. 8 — Channel-specific risk and authority | `figures/fig08_channel_specific_risk_authority.pdf` (+ PNG) | `scripts/figures/generate_fig08.py` | Main nominal/emergency Separate trajectories |
| Fig. 9 — Asymmetric-risk authority comparison | `figures/fig09_shared_vs_separate_asymmetric_risk.pdf` (+ PNG) | `scripts/figures/generate_fig09.py` | Main emergency/high-curvature Separate trajectories, including same-state shared diagnostic |
| Fig. 10 — Vehicle replay | `figures/fig10_recorded_state_replay_vlm_lateral_gain.pdf` (+ PNG) | `scripts/figures/generate_fig10.py` | Processed replay source signals, V3 risk config and fixed VLM weights |
| Nominal Longitudinal Control Performance | `data/tables/table_nominal_longitudinal.csv` | `scripts/tables/generate_paper_tables.py` | Fig. 6 source runs; evaluation mask |
| Nominal Lateral Control Performance | `data/tables/table_nominal_lateral.csv` | same | Fig. 7 source runs; evaluation mask |
| Shared vs Separate Architecture Comparison | `data/tables/table_shared_vs_separate.csv` | same | Main Shared/Separate runs for four scenarios |
| Controlled Lead-Speed Variation | `data/tables/table_controlled_variation.csv` | same | All 20 variation runs; per-run metrics, mean/std with ddof=0 |
| Empirical Residual Boundedness | `data/tables/table_empirical_residual_boundedness.csv` | same | All four main Separate trajectories |
| Recorded-State Replay Outputs | `data/tables/table_recorded_state_replay.csv` | same | Exact regenerated V3 replay used in Fig. 10 |

Final numeric Table I–VII assignment was not verifiable without the final manuscript file; tables are mapped by scientific title rather than invented numbering. File IDs Fig. 6–10 follow the final V3 artifact filenames supplied for this release. Plotting uses the extracted archived V3 pipeline and writes to `generated/figures/`. LaTeX/Markdown tables are emitted under `generated/tables/`.

Main run IDs required by the five figures:

| Role | Run ID |
|---|---|
| Nominal System 1 | `20260928T055928_055510Z_nominal_following_f5594b` |
| Nominal System 2 | `20260928T055947_731172Z_nominal_following_490d26` |
| Nominal Separate | `20260928T060027_945211Z_nominal_following_96dfe1` |
| Emergency Separate | `20260928T060147_594526Z_emergency_stop_56e95a` |
| High-curvature Separate | `20260928T060420_574975Z_high_curvature_low_longitudinal_risk_dc3cea` |

The archived nominal captions used the phrase channel-isolated. They are full architecture runs; the generated public table captions state that limitation without changing any numeric result. High-curvature rows must remain marked diagnostic. Undefined TTC is missing/dash, never zero. Steering units distinguish CARLA applied-equivalent radians from replay command radians and unitless standardized trend errors.
