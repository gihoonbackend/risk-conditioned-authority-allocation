# Archived offline VLM context

The archived weight file identifies model `gpt-5.2` and contains one saved request/response per path. It records seven sensor quantities: distance, reference distance, ego speed, lead speed, curvature, lateral error and heading error. The user prompt also prints gap/relative-speed values. `system_prompt.txt` is copied byte-for-byte, and `requests/` preserves each entire user prompt and sensor snapshot.

The archived system prompt asks for JSON with five weights in `[0,1]` summing to one, path fields, context summary and confidence. Each response preserves `raw_response_text`, `parsed_response` and `sanitized_response`. The historical schema is preserved for provenance; V3 uses only the physically active three weights and the final maps documented in the root README.

Provider context: OpenAI. Archived model identifier: `gpt-5.2`. Exact revision: unknown. Historical temperature: unknown. `top_p`, seed, maximum output tokens and wire-level schema enforcement settings: not explicitly archived. The saved JSON request descriptions are not complete HTTP request transcripts. They do not prove strict schema-mode enforcement, API retry/fallback behavior, deterministic generation, or repeated-query consensus.

No new VLM requests were made to construct this package. Weights are fixed across the released V3 CARLA and vehicle-replay artifacts. Saved snapshots come from CARLA, not the real vehicle. Their labels are experimental path labels; the archived VLM explicitly described some entry views as visually near-straight. Pixel data were preserved, and no EXIF/GPS metadata was found.

Local image and metadata paths were rewritten to package-relative references. Prompt text and all raw/sanitized numeric weights were preserved. Per-file source/distributed hashes are in `../reproducibility/artifact_provenance.json`.
