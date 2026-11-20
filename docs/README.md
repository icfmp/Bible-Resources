# Bible Resources — contributor guide

Bible Resources maintains **source-faithful, verifiable and redistributable** Biblical resources for SWORD-compatible readers. This documentation explains *how the project works*. It does **not** record each individual edition's construction history, current approval status or one-off fixes.

## Start here

1. [How the repository is organized](architecture/README.md) — original sources, cleaned editorial masters, native SWORD modules and their metadata.
2. **[The production process](PRODUCTION_PIPELINE.md)** — edition and rights verification → immutable original → cleaning → exhaustive source fidelity → SWORD → independent readers → publication.
3. [Editorial and legal principles](policies/README.md) — what must never change silently, and what requires recorded approval.
4. [Operational workflows](workflows/README.md) — checks, commands, resumable stages, imports and publication.
5. [Technical verification](technical/README.md) — OSIS/USFM inventories, reference integrity, notes, native readback and rendering.

## How to use this documentation

**Adding a resource?** First identify the exact edition and redistribution rights, then follow [the production contract](PRODUCTION_PIPELINE.md). Separate acquisition, cleanup, validation, editorial approval and public publication; a CI run alone does not establish all five.

**Investigating a textual or structural mismatch?** Compare the immutable original, reviewed cleaned master, compiled native entries and reader display in that order. Follow [the general verification guides](technical/README.md). A workaround for a particular reader is not evidence that the author's wording needs revision.

**Editing the process?** Change the relevant generic policy/workflow, with tests and reproducible justification. Do not insert one edition's exceptions into the general pipeline.

**Reviewing an individual Bible or commentary?** Go directly to `sources/cleaned/<type>/<language>/<module-id>/editorial/`. Each module maintains its own decisions, original witnesses, audit reports, versioned release records and reader profiles. The `CLEANUP_MANIFEST.json` beside the cleaned master pins derivation and hashes.

**Looking for old experiments?** `history/` preserves superseded cross-project research. Historical observations are not production instructions.

## Documentation responsibilities

| Location | Authoritative purpose |
| --- | --- |
| [`docs/architecture/`](architecture/README.md) | Repository design, file structure, formats and reader metadata standards |
| [`docs/policies/`](policies/README.md) | Source fidelity, editorial decisions, licensing, versification and quality |
| [`docs/workflows/`](workflows/README.md) | Actions to take, required checkpoints, translation and release process |
| [`docs/technical/`](technical/README.md) | Reusable inspection and verification techniques |
| `sources/cleaned/**/editorial/` | **Per-edition** decisions, notes, QA, source evidence, profiles and release receipts |
| `history/` | Historical cross-cutting experiments and superseded research |
| `modules/` | Compiled SWORD modules, metadata and source-audit artifacts |

## Non-negotiable safeguards

- Do not silently change Biblical wording, punctuation, versification, notes, cross-references or commentary scopes.
- Preserve source identity, edition, rights, original files and their hashes; make every transformation documented and reversible.
- Distinguish source defect, editorial convention, compiler behavior and reader rendering.
- Keep the independent `entity-index/` (Bible Semantic Index) untouched by Bible Resources housekeeping.
- Never promote a draft, historical test, or successful compilation as an approved public release.

[Current priorities](ROADMAP.md) are a navigation aid; GitHub issues and approved release manifests are the status authority.
