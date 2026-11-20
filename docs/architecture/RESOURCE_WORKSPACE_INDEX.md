# Resource directories — quick reference

The detailed storage convention is maintained in [workspace layout](WORKSPACE_LAYOUT.md). This page is a compatibility pointer for existing links, not a second directory specification or a resource-status inventory.

- `sources/original/<type>/<language>/<id>/`: original acquired evidence, unmodified.
- `sources/cleaned/<type>/<language>/<id>/`: reviewed editorial master and `CLEANUP_MANIFEST.json`.
- `sources/cleaned/<type>/<language>/<id>/editorial/`: edition-specific decisions, evidence, profiles and release records.
- `work/`: generated candidates, never authoritative.
- `modules/`: compiled SWORD artifacts and validation metadata.
- `docs/`: generic architecture, policies, workflows and technical methods.
- `history/`: retained, superseded cross-project research.

The actual current edition status is determined from manifests, issues, PRs and release receipts, not from this page. `entity-index/` belongs to the independent Bible Semantic Index workstream.
