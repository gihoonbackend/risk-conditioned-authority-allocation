# Controller implementation

The C++ sources in `ctg/`, `mpc/`, `lqr/` and `include/` are byte-preserved V3 source-snapshot copies. `runtime/controller_bridge.cpp` exposes their component outputs without a competing alpha source. `runtime/control.py` preserves ctypes invocation, checkpoint inference, residual filtering, authority guard and actuator postprocessing. `orchestration/risk.py` preserves the experiment risk implementation; the public config loader admits the V3 configuration only.

`runtime/geometry.py` extracts the seven exact geometry functions loaded by the experiment; `runtime/engine.py` preserves the original `execute` loop with its old CLI removed. The portable `common.py` resolves package paths and compiles the same C++ source files. The public entry point is `scripts/run/run_experiment.py`; archived per-run configurations provide its inputs.

No controller tuning, simulation execution or policy retraining took place during packaging. A numerical test replays existing states through the C++ components to check packaging equivalence; that check does not propagate a new vehicle trajectory.

Runtime guard/filter implementation: `runtime/control.py`. Checkpoint availability: `../checkpoints/README.md`. Code rights require review; see `../LICENSE`.
