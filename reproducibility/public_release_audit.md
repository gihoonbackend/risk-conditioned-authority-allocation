# Public release audit

Technical scan: passed. Public upload readiness: **NO — LICENSE REVIEW REQUIRED**.

The scan covers every release text file, decompressed CSV, PNG metadata/EXIF, and PDF metadata/extracted text. No high-confidence credential, email, private user-directory path or private key was found. Keyword occurrences in the scanner, release-rights prose and numeric-token terminology are benign and counted in public_release_audit.json. The scan does not establish legal permission or guarantee that all quasi-identifying driving patterns are anonymous.

## Vehicle sanitization

User metadata, absolute recording date/time, equipment details, internal project/software identifiers and instrument schema hierarchy were removed. All 236,504 numeric measurement rows and relative times are preserved exactly. No GPS, address, VIN, plate or account measurement columns were found. No real-vehicle images or video were included. The three VLM images are CARLA synthetic frames, visually reviewed and without EXIF/GPS tags.

## Licensing

The audited artifacts do not establish original-code ownership, institutional/project data redistribution authority, recording consent or checkpoint redistribution permission. No MIT/BSD/CC BY license was assigned. The checkpoint is withheld. The upstream CARLA MIT notice is included for attribution/review and does not license this entire package.

## Size and archival recommendation

No release file reaches the conservative 100,000,000-byte threshold.
CSV trajectories use lossless gzip. Git LFS is unnecessary for this package as assembled. After permission approval, use an ordinary GitHub repository and archive the tagged release on Zenodo. If future raw imagery/video expands the release, use a separate versioned Zenodo deposit rather than adding large media to normal Git history.

## Required human review

- Confirm original code ownership and license grant.
- Confirm institutional/project vehicle data ownership, consent and release authorization.
- Confirm redistribution terms for synthetic render/VLM artifacts.
- Approve checkpoint release or document restricted availability.
- Cross-check final typeset manuscript and table numbering; no manuscript file was supplied.
- Assign actual repository commit/tag/URL after approval.

The final manifest and checksums describe this candidate, not an already published release.
