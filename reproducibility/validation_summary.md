# Package validation

Status: passed (offline reproduction).

- JSON/YAML/CFF parsing and local Markdown links checked.
- Every public CSV opens; each column has a data-dictionary entry.
- V3 risks and authority reproduced at every sample in all 36 archived runs.
- C++ CTG/MPC/LQR outputs checked on all 2000 recorded states of the nominal Separate run.
- All six final tables match raw-derived metrics and replay calculations within 1e-10 tolerance.
- All five PDF/PNG figures regenerated; pixel comparison recorded per figure in validation_results.json.
- 236,504 raw vehicle numeric rows preserved exactly at token level.
- All packaged source/artifact checksums and decompressed raw simulation hashes verified.
- No new CARLA simulation, model training, VLM call or original-artifact modification performed.
- TeX files generated, but LaTeX compilation not performed (compiler unavailable).
- License/ownership and consent verification are human release gates, separate from these technical checks.
