# Known limitations and release decisions

- Redistribution rights for original code, vehicle data, the RL checkpoint and synthetic render artifacts remain subject to author/institution review. No permissive license is assumed.
- The checkpoint is withheld. Offline reproduction is complete from archived outputs; new closed-loop CARLA execution requires that exact authorized checkpoint and a separate simulator installation.
- Archived training statistics show a maximum 5000-step episode. The complete training command was not archived; deployment parameters and current defaults must not be substituted for historical training settings.
- All archived CARLA runs use the same random-library seed settings. Lead-speed variation is deterministic condition variation. No random-seed robustness claim is supported.
- Some passing runs contain saturation warnings. All archived warnings remain in the run manifests; passing technical checks do not imply absence of control limitations.
- High-curvature evaluation is only 13 samples spanning 0.6 s, on Path 1 where g_kappa=1. It is an authority-allocation diagnostic, not a general performance benchmark. The System-2 endpoint saturation precludes main longitudinal performance interpretation there.
- The nominal channel plots are projections of full architecture runs, not fixed longitudinal-trajectory or fixed lateral-trajectory counterfactual experiments. The package's generated table captions describe this accurately.
- The shared curve in Fig. 9 is a same-state risk-law diagnostic on the Separate trajectory. The architecture performance table uses separate actual runs.
- Vehicle raw measurements have no archived calibrated unit metadata. Raw signal units, historical input reconstruction, lead-speed proxy, lane-error centering and steering alignment need expert confirmation. The V3 replay boundary from archived processed signals is reproducible.
- Replay base `ax_mpc` is an archived signal; its upstream solver provenance is not fully verified. The replay must not be described as new execution of the identical CARLA MPC algorithm from raw sensor data.
- Replay is open loop and standardized steering-trend comparison is not physical steering accuracy. Original processed trajectories/plots were retained without improving unfavorable results.
- Main tables report applied-equivalent steering RMS; replay reports command RMS and standardized trend metrics. They are distinct quantities.
- Residual guard statistics show empirical boundedness only. They do not establish a Lipschitz bound or formal closed-loop stability.
- Historical VLM revision, temperature, top_p and seed are unavailable. Preserved outputs support replayability, not exact regeneration by a present-day API call.
- Raw lossless gzip and metadata sanitization alter file hashes. Source and distributed checksums are explicitly paired; raw numeric tokens are independently checked.
- Original source tree was dirty/untracked. The original git hash alone is insufficient provenance. The package preserves individual source hashes and lists portability adaptations.
- A current manuscript file was not supplied to this packaging task. Numeric agreement is verified against the authoritative six final V3 CSVs, not independently against typeset manuscript tables.
- CARLA and network-dependent installation were not rerun for packaging. The plotting/analysis environment matches the archived Python package versions; cross-version PDF byte identity is not promised.
