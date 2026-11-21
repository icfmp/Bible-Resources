# Architecture

Bible Resources is a **source-first editorial and SWORD distribution repository**. It preserves exact upstream evidence, maintains explicitly reviewed editorial masters, compiles portable SWORD modules, and publishes a versioned catalogue. It is not a live Bible text API or a mirror of every upstream catalogue.

## Data ownership and boundaries

| Layer | Responsibility | Must not do |
| --- | --- | --- |
| `sources/original/` | Keep acquired publisher/source files unchanged, with edition identity and checksums | Normalize in place |
| `sources/cleaned/` | Hold the curated master and the edition's `editorial/` decisions, evidence and release notes | Conceal editorial decisions in global docs |
| `work/` | Generate disposable or reviewable candidates | Become an untracked authoritative source |
| `modules/` | Package native SWORD output and build metadata | Replace original source evidence |
| `catalog/v1/` and `sword/` | Distribute approved, versioned module artifacts | Publish draft/research outputs |
| `docs/` | Explain lasting, edition-independent architecture, policies, procedures and verification | Store individual-module histories or transient audit results |
| `history/` | Retain historical cross-resource research when preservation has real value | Serve as current operating instructions |
| `entity-index/` | Separate Bible Semantic Index project | Be altered by resource housekeeping |

Directory conventions and exact storage responsibilities are in [workspace layout](WORKSPACE_LAYOUT.md). A resource's **current** editorial state is determined from its own manifest, issue, reviewed PR and release receipt, never inferred from documentation prose.

## Publication interface

The published catalogue is `catalog/v1/catalog.json`. SWORD distribution includes module configuration/archive and packages under `sword/`. Consumers, including the [Bible application](https://github.com/icfmp/Bible), should treat that interface as versioned; any future change needs an explicit migration plan.

Multiple upstream repositories are **discovery sources**, not automatic import queues. Candidate editions must be identified by exact source and rights; only verified-equivalent editions can be deduplicated. See [source priority](../policies/SOURCE_PRIORITY.md) and [rights](../policies/RIGHTS.md).

## Two distinct proof routes for compiled commentaries

- **Unchanged upstream SWORD:** preserve the original binary and metadata, and verify archive identity and native key/content integrity.
- **Reviewed source-derived reconstruction:** pin an authenticated source, record each approved reversible transformation, compare complete source and native output, and verify section scope, references, links, and readers.

Neither route implies editorial approval or permission to publish. A rebuilt edition must never claim byte identity with its upstream compiled module. Detailed evidence and specific module decisions belong in the corresponding `sources/cleaned/**/editorial/` directory.

For the authoritative process and its checkpoints, use [production pipeline](../PRODUCTION_PIPELINE.md). For technical verification, use [technical methods](../technical/README.md).
