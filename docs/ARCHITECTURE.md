# Architecture

Bible Resources is a SWORD-compatible distribution service. Sources and editorial transformation recipes are distinct from compiled artifacts. GitHub Pages initially publishes `catalog/v1/catalog.json` alongside `sword/mods.d.tar.gz`, `sword/modules/` and `sword/packages/`. Bible consumes a configurable HTTPS catalogue endpoint. A future API must preserve the v1 contract or provide explicit migration.

CrossWire repositories remain upstream sources; this project is independent. Do not scrape and mirror their entire inventory without a per-edition license review.


## One canonical curated edition across upstream repositories

The five upstream SWORD catalogues are discovery sources, not five independent import queues. Only one provider may supply each **verified identical edition**, according to [SOURCE_PRIORITY.md](SOURCE_PRIORITY.md). The selector is currently read-only, with ambiguity and higher-priority outages blocking import. Approved manifests require a provider-independent canonical edition ID; the build gate rejects duplicate edition variants. The future importer must consume the reviewed selection result and must not mirror every upstream automatically.

## Compiled commentary preservation versus reviewed rebuilds — accepted decision (2026-11-16)

**Technical choice, delegated by the project owner; not authorization to merge
or publish BRMHCC 0.1.1.** Two separate, source-neutral validation routes are
kept because their claims are fundamentally different:

- `stock_reader_keys` means the upstream compiled SWORD source itself remains
  **byte-identical**. Its original archive, compression data, native content,
  link topology and unedited source proof must not be replaced or weakened.
- `reviewed_compiled_commentary_rebuild` means a commentary has been
  **reconstructed from an authenticated original** with bounded, documented,
  reversible source changes and/or navigation repairs. A full original-to-
  candidate native I/K/TOP comparison, true SWORD link identity, all approved
  source deltas, complete source provenance, independent evidence and exact
  final compressed-file hashes are mandatory.

A rebuilt edition must **never impersonate original stock identity**. The
two validators do not silently share assertions, change verse segmentation,
relax source-fidelity checks, or automatically authorize publication. New
commentaries must use the appropriate proof contract, not resource-specific
exceptions. The rebuilt module still requires human editorial and rights
review, final file/digest verification and an explicitly authorized release
plan. See [source-attested rebuild contract](evidence/mhcc-274/rebuilt-commentary-validation-contract.md)
and [publication controls](PUBLISHING.md).

This architecture has passed [1,329 regression/unit tests](https://github.com/icfmp/Bible-Resources/actions/runs/43867792317)
and a [full original and rebuilt MHCC native SWORD/Xiphos audit](https://github.com/icfmp/Bible-Resources/actions/runs/43867792111),
but those technical checks **do not** constitute independent external code
review, signed editorial permission, a final distributable package or a
publication authorization. The existing approved BRMHCC 0.1.0 and its
`SOURCE_VALIDATION.json` stay untouched.

