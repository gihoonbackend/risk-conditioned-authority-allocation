# Configuration provenance

`canonical_d_v3/resolved_config.json` is the archived main Nominal/Separate V3 config with only repository paths rebased. The named overlay points to this self-contained resolved config instead of requiring obsolete inherited config files. Its numerical overrides are already resolved in that base.

Every main and controlled-speed run has its actual resolved config under `data/simulation/raw/<run_id>/resolved_config.json`. Use those files to recover scenario-specific spawn, lead event, architecture and window settings. `scenarios/*/config.json` provides the main Separate config for each scenario; the controlled-speed index lists all 20 configurations.

`experiment.alpha_architecture` is the runtime authority selector. The inherited `controller.mode` label in archived configs is not the selector used by the canonical execution loop. Source `sha256` and sanitized public `sha256` values are distinguished in each artifact entry. Original local `absolute_path` fields are omitted and resolved dynamically. Original numerical parameters, actual-duration values and diagnostic overrides are retained.

The package runner accepts only the fixed V3 risk contract. No cache or implicit route override is used.
