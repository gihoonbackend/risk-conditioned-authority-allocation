# Vehicle measurements and recorded-state replay

## Included layers

| Layer | File | Meaning |
|---|---|---|
| Raw | `raw/recorded_sequence.csv.gz` | 236,504 logger measurement rows, 24 numeric channels including original relative elapsed time |
| Processed input | `processed/replay_source_signals.csv.gz` | Historical controller-output/state sequence used by the V3 generator; all input rows retained, obsolete blended-output columns omitted |
| Processed output | `processed/recorded_state_replay_vlm_lateral_gain.csv` | Byte-preserved final V3 20 Hz replay output used for Fig. 10 and the replay table |
| Metadata | `metadata/privacy_transform.json` | Fields removed, hashes, numeric-token invariant and rights status |
| Metadata | `metadata/replay_provenance.json` | Input columns, known historical processing boundary and replay sampling rule |

## Privacy transformation

The original instrument CSV begins with a metadata block containing a user value, an absolute recording date/time, equipment descriptions, internal software/project identifiers and model hierarchy paths. The public raw file removes this entire preamble and the non-measurement first-column marker. The four duplicated `In1` signal names are disambiguated as `C0`–`C3` from the archived schema; the remaining signal names are retained.

Every numeric token, row order and relative timestamp is preserved without smoothing, interpolation, clipping, resampling or value replacement. UTF-8 encoding and deterministic lossless gzip change representation only. A numeric-token checksum independently verifies this invariant. Original absolute date/time and user/device metadata are not included. No GPS, address, VIN, plate, email, phone or device-ID measurement channel was found. No real-vehicle images, video or faces are distributed.

The original `trace_units` metadata is empty. Names or upstream proxy-column suffixes do not establish raw-sensor calibration. Unverified raw units are explicitly marked in the data dictionary.

## Reproduction boundary

V3 recomputes normalized risks, `g_kappa`, separate coefficients, blends, guard and final steering postprocessing from the archived processed inputs. It keeps the first logged row in each 0.05 s time bin. Path entries are fixed logged-time bins at 25/75/125 s, distinct from CARLA spatial matching. The same saved simulation VLM weights are used.

Earlier interpolation, centering, inferred lead-speed construction, steering sign/alignment, and base controller/residual calculations were already present in the historical processed input. Their complete raw-to-input command provenance was not archived. In particular, the `ax_mpc` column alone does not establish whether the original generator used the C++ predictive solver or an MPC-like routine. These are documented limitations, not new reconstructions.

Logged steering is compared after z-score standardization. Trend agreement is not a physical steering-angle error. The V3 replay table uses controller-command RMS, while CARLA tables use applied-equivalent steering RMS. **This replay is not a closed-loop on-road validation.**

## Release permission

**LICENSE REVIEW REQUIRED.** Numeric sanitization was completed, but institutional/project ownership, recording consent and data redistribution permission were not established by the audited files. The author/institution must approve public release and choose data terms before upload. No CC BY grant is assumed.
