# Packaging adaptations

No source experiment artifact was changed, no vehicle trajectory was resimulated, and no weight or controller parameter was tuned.

## Source selection

The package selects 16 successful main runs from batch `20260928T055908_868958Z` and 20 successful controlled-condition runs from batch `20260928T060553_058951Z`. Source files are matched through their recorded run directories and hashes. Failed, pending, preflight-only and obsolete runs are excluded. Saturation warnings attached to valid runs are retained.

C++ sources, headers, the ctypes/control/filter implementation and the orchestration module come from the runtime snapshot of the final nominal Separate run. They are copied byte-for-byte. The engine keeps the original execution function but drops the old research-tree CLI. Geometry contains only the seven original function definitions used at runtime. `controllers/runtime/common.py` is a new portable adapter for path resolution, hashing, C++ compilation and the fixed V3 contract. The public run wrapper selects exact archived configs; it does not rebuild scenarios by guessing overrides.

## Artifact transformations

- Simulation raw CSVs are losslessly compressed, with decompressed hashes equal to the original file hashes.
- JSON local filesystem paths are removed or rebased. Source/distributed hashes are distinct; original numerical parameters and weights remain unchanged.
- The config inheritance chain is made self-contained through the final archived resolved config. No obsolete parent-config files are required.
- Vehicle raw measurement tokens are preserved, while identifying instrument preamble/schema metadata is removed. Numeric-token checksums cover all released raw rows.
- Replay source CSVs retain only the inputs needed for V3 reproduction and relevant logged measurements. Old alpha/blended-output columns are excluded. Retained numeric tokens and sample ordering are unchanged.
- The final six table CSVs and five figure PDF/PNG pairs are copied byte-for-byte.
- Figure/replay/table functions are extracted from the V3 generator with only package paths, lossless compressed-input suffixes and generated-output directories adapted. Public nominal table captions describe full architecture runs instead of claiming strict channel isolation.
- The historical VLM prompt/response texts are archived verbatim, including their original five-weight schema; the final V3 formulas are explained separately.
- The checkpoint is documented but not copied, because redistribution permission could not be established.

Per-file provenance and distributed hashes are in `../reproducibility/artifact_provenance.json`. Newly written wrappers/documentation are covered by the release inventory. Offline validation checks the entire public CSV dictionary, every run's risk law, original-state C++ output equivalence, six table values and all five plot images. This checks portability without claiming new closed-loop validation.
