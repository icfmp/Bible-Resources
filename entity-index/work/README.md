# BSI work — our derived resource

This directory is reserved for **our** editorial work, audits and versioned corrections, rather than immutable original upstream sources.

## Current v0.1 compatibility layout

The existing, validated implementation and its declarative files remain **temporarily at the parent `entity-index/` root**, because CI, reproducible builds, review receipts and the published v0.1 source contract refer to their stable paths:

- `../compile_index.py`, `../resolve.py`, `../distribution_profile.py`, `../minimal_labels.py`, `../package_candidate.py`
- `../editorial-decisions.json`, `../reviewed-person-word-overlaps.json`
- `../source-unattested-words.json`, `../source-unattested-verses.json`, `../source-reference-qualifications.json`
- `../test_*.py` and existing `../V0_1_*.md` evidence

These are **our BSI working files**, not original ACAI source files. Future working reports and independent editorial batches should be created in this `work/` directory. Moving the pre-existing engine and test data requires a separately tested atomic migration of import paths, workflow references and release reproducibility, never an untested mass move.

Every correction should identify the exact original word, source edition, evidence, and reversible decision. No silent edits to `sources/checkouts/`.
