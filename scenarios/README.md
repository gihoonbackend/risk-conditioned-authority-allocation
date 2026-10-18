# Scenario definitions

The route is Town04. `path_reference.json` contains simulated map coordinates and polyline match radii; these are unrelated to vehicle-log GPS. Main runs have 2000 control samples over 100 s. Their evaluation mask selects 1500 samples from 25 s through 99.95 s. The high-curvature diagnostic retains its archived 13-sample 3.4–4.0 s window.

Each scenario folder contains the actual main Separate-alpha resolved config. All architectures' configs, including matching initialization and controller settings, are retained beside the raw trajectories. Select via `../reproducibility/run_index.json` rather than editing only a scenario label. The controlled-speed configuration enumerates all 20 exact configs.

The high-curvature case is retained solely as an asymmetric-risk diagnostic. Its fully activated System-2 longitudinal saturation is not evidence for main longitudinal performance. The speed variation uses deterministic conditions 13–17 m/s and population standard deviations; it is not a multi-random-seed evaluation.
