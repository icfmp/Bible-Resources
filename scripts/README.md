# Executable tooling — navigation, lifecycle and maintenance

**Active entrypoints remain at the root during audited migration.** See [the historical tools directory](historical/README.md) for the first real relocation and its reproducible CI/test callers. The root is not intended as a permanent home for every experiment. The inventory covers nested paths automatically; use [issue #430](https://github.com/icfmp/Bible-Resources/issues/430) for tested migration batches.

## Responsibility map (destination categories)

| Category | Purpose | Stable examples / migration condition |
| --- | --- | --- |
| `intake/` (future) | Source edition, licence and provenance acquisition | `bible_intake.py`, `commentary_intake.py`; migrate only with validated workflow paths |
| `source/` (future) | OSIS/USFM schema, normalization, notes and references | `guard_osis.py`, `normalize_osis.py`, `source_osis_inventory.py` |
| `native/` (future) | SWORD native readback, mapping, text and link parity | `sword_native_inventory.py`, `source_native_*`; C++ compiler paths require care |
| `readers/` (future) | Xiphos, JSword and Android compatibility probes | Migrate only after integration tests and runner setup parity |
| `release/` (future) | Deterministic package, signing, catalogue and publication | `build.py`, `validate.py`, `release_preflight.py`; public entrypoints stay stable until explicitly migrated |
| [`historical/`](historical/README.md) | Exact source-pinned reproduction and superseded experiments | Begin with relocated LSG synthetic versification probe; no deletion without replay |

**These future category names are a target design, not folders claimed as already populated.** Create them incrementally when their actual callers and import contracts pass tests. A bare mass move or hundreds of compatibility wrappers would conceal, not solve, the maintenance problem.


Keep stable script paths as public interfaces until their **actual** Python
imports, tests, CI workflows, external documented commands, and historical
release consumers are all verified. Moving a script can silently break
source-bound evidence even when it looks like a minor directory tidy-up.

The generated [tool inventory](../reports/tooling/TOOL_REGISTRY.md) and its JSON
counterpart are the canonical per-script index, with documented lifecycle
categories: KEEP_GENERIC, GENERALIZE, MERGE, HISTORICAL/ARCHIVE, UNDECIDED.

**Production:** extend existing generic intake, OSIS normalization, USFM
support, source parity, reference validation, SWORD build and reader checks.
Use the single [production contract](../docs/PRODUCTION_PIPELINE.md); avoid new program-per-resource scripts.

**Research:** historical one-off readers/probes may be kept for replay, but
are not the preferred production pipeline. Relocate only after the real
workflow/caller/test/historical-tag audit and behavior-equivalence proof.

**No cosmetic mass move:** this workspace cleanup deliberately leaves
original script locations callable. Classifications alone do not prove
that a file is dead code; the nine historical/archivable flags have active
script, test or workflow references. Reorganization is not an authorization
to delete or silently change their outputs.

[Canonical workspace paths](../docs/architecture/WORKSPACE_LAYOUT.md).
