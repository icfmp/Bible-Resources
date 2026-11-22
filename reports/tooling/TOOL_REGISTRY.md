# Tool registry — shared and module-owned source-bound tools

This generated list covers shared scripts plus edition-owned tools under `modules/<resource-id>/tools/`. It lists callers/review recommendations, **not** a licence to delete scripts or proof that they are exercised.
Generate/check: `python scripts/tool_registry.py --write` / `python scripts/tool_registry.py --check`.
The source-bound detailed registry is [TOOL_REGISTRY.json](TOOL_REGISTRY.json). No publishing credentials or raw commentary content enter the inventory.

## Lifecycle

- **KEEP_GENERIC:** retain the stable interface and strengthen tests.
- **GENERALIZE:** extract known edition-specific logic into a reviewed manifest, preserving existing proofs.
- **MERGE:** candidate overlapping research functions; only merge after comparing outputs and historical dependencies.
- **HISTORICAL/ARCHIVE:** retain for immutable proof/replay; archive only after evidence-based replacement, never by deleting blindly.
- **MODULE_LOCAL:** pinned resource-specific maintenance/replay; not a shared entrypoint or a new publication route.
- **UNDECIDED:** source/caller audit required; no inferred deletion.

## Baseline counts

- GENERALIZE: 0
- HISTORICAL/ARCHIVE: 0
- KEEP_GENERIC: 24
- MERGE: 0
- MODULE_LOCAL: 0
- UNDECIDED: 33

## All tracked tools

| Script | Classification | Tests | Static callers | Stage hint |
| --- | --- | --- | ---: | --- |
| [`scripts/audit_osis.py`](../../scripts/audit_osis.py) | UNDECIDED | not established | 6 | source/native audit |
| [`scripts/bible_intake.py`](../../scripts/bible_intake.py) | KEEP_GENERIC | named test | 4 | intake |
| [`scripts/build.py`](../../scripts/build.py) | KEEP_GENERIC | not established | 11 | publication/release |
| [`scripts/catalogue_profiles.py`](../../scripts/catalogue_profiles.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/catalogue_release_coverage.py`](../../scripts/catalogue_release_coverage.py) | KEEP_GENERIC | named test | 8 | publication/release |
| [`scripts/check_provider_parity.py`](../../scripts/check_provider_parity.py) | UNDECIDED | not established | 3 | not determined |
| [`scripts/check_updates.py`](../../scripts/check_updates.py) | UNDECIDED | not established | 10 | not determined |
| [`scripts/commentary_intake.py`](../../scripts/commentary_intake.py) | KEEP_GENERIC | named test | 6 | intake |
| [`scripts/commentary_native_inventory.py`](../../scripts/commentary_native_inventory.py) | KEEP_GENERIC | not established | 4 | source/native audit |
| [`scripts/commentary_native_raw_inventory.py`](../../scripts/commentary_native_raw_inventory.py) | KEEP_GENERIC | named test | 3 | source/native audit |
| [`scripts/compiled_stock_commentary_proof.py`](../../scripts/compiled_stock_commentary_proof.py) | KEEP_GENERIC | named test | 3 | not determined |
| [`scripts/fetch_reviewed_schema.py`](../../scripts/fetch_reviewed_schema.py) | UNDECIDED | not established | 3 | not determined |
| [`scripts/guard_commentary.py`](../../scripts/guard_commentary.py) | KEEP_GENERIC | not established | 6 | not determined |
| [`scripts/guard_osis.py`](../../scripts/guard_osis.py) | KEEP_GENERIC | named test | 14 | not determined |
| [`scripts/normalize_osis.py`](../../scripts/normalize_osis.py) | KEEP_GENERIC | not established | 5 | not determined |
| [`scripts/osis_semantic_fidelity.py`](../../scripts/osis_semantic_fidelity.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/pilot_fetch.py`](../../scripts/pilot_fetch.py) | KEEP_GENERIC | not established | 6 | not determined |
| [`scripts/pilot_preflight.py`](../../scripts/pilot_preflight.py) | KEEP_GENERIC | named test | 11 | not determined |
| [`scripts/pilot_subprocess.py`](../../scripts/pilot_subprocess.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/probe_official_osis.py`](../../scripts/probe_official_osis.py) | UNDECIDED | not established | 2 | source/native audit |
| [`scripts/promote_sword_preview.py`](../../scripts/promote_sword_preview.py) | KEEP_GENERIC | named test | 4 | not determined |
| [`scripts/publish_reviewed_release.py`](../../scripts/publish_reviewed_release.py) | KEEP_GENERIC | not established | 9 | publication/release |
| [`scripts/published_reference_audit.py`](../../scripts/published_reference_audit.py) | UNDECIDED | named test | 3 | publication/release |
| [`scripts/publisher_osis_observation.py`](../../scripts/publisher_osis_observation.py) | UNDECIDED | named test | 5 | publication/release |
| [`scripts/publisher_osis_preview_package.py`](../../scripts/publisher_osis_preview_package.py) | UNDECIDED | named test | 4 | publication/release |
| [`scripts/publisher_osis_preview_readback.py`](../../scripts/publisher_osis_preview_readback.py) | UNDECIDED | not established | 2 | publication/release |
| [`scripts/publisher_osis_sword_candidate.py`](../../scripts/publisher_osis_sword_candidate.py) | UNDECIDED | named test | 5 | publication/release |
| [`scripts/reader_xiphos_headless_smoke.py`](../../scripts/reader_xiphos_headless_smoke.py) | UNDECIDED | named test | 3 | not determined |
| [`scripts/release_preflight.py`](../../scripts/release_preflight.py) | KEEP_GENERIC | named test | 3 | publication/release |
| [`scripts/research/bible/__init__.py`](../../scripts/research/bible/__init__.py) | UNDECIDED | not established | 0 | not determined |
| [`scripts/research/bible/native_milestone_pair_audit.py`](../../scripts/research/bible/native_milestone_pair_audit.py) | UNDECIDED | named test | 5 | source/native audit |
| [`scripts/research/bible/native_raw_main_text.py`](../../scripts/research/bible/native_raw_main_text.py) | UNDECIDED | named test | 6 | not determined |
| [`scripts/research/bible/native_sword_markup_census.py`](../../scripts/research/bible/native_sword_markup_census.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/research/bible/source_native_note_positions.py`](../../scripts/research/bible/source_native_note_positions.py) | UNDECIDED | named test | 3 | not determined |
| [`scripts/research/bible/source_native_ordered_body.py`](../../scripts/research/bible/source_native_ordered_body.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/research/bible/source_native_osis_boundary_positions.py`](../../scripts/research/bible/source_native_osis_boundary_positions.py) | UNDECIDED | named test | 3 | not determined |
| [`scripts/research/bible/source_native_osis_structure_screen.py`](../../scripts/research/bible/source_native_osis_structure_screen.py) | UNDECIDED | named test | 3 | not determined |
| [`scripts/research/bible/source_native_osis_target_addressability.py`](../../scripts/research/bible/source_native_osis_target_addressability.py) | UNDECIDED | named test | 5 | not determined |
| [`scripts/research/bible/source_osis_verse_notes.py`](../../scripts/research/bible/source_osis_verse_notes.py) | UNDECIDED | named test | 7 | not determined |
| [`scripts/reviewed_compiled_commentary_rebuild.py`](../../scripts/reviewed_compiled_commentary_rebuild.py) | KEEP_GENERIC | named test | 7 | publication/release |
| [`scripts/reviewed_modern_commentary_rebuild.py`](../../scripts/reviewed_modern_commentary_rebuild.py) | UNDECIDED | named test | 3 | publication/release |
| [`scripts/reviewed_osis_commentary_rebuild.py`](../../scripts/reviewed_osis_commentary_rebuild.py) | UNDECIDED | not established | 1 | publication/release |
| [`scripts/select_sources.py`](../../scripts/select_sources.py) | UNDECIDED | not established | 4 | not determined |
| [`scripts/smoke.py`](../../scripts/smoke.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/source_osis_inventory.py`](../../scripts/source_osis_inventory.py) | UNDECIDED | named test | 9 | source/native audit |
| [`scripts/source_osis_note_link_triage.py`](../../scripts/source_osis_note_link_triage.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/stable_sword_refs.py`](../../scripts/stable_sword_refs.py) | UNDECIDED | named test | 19 | not determined |
| [`scripts/sword_native_commentary_index.cpp`](../../scripts/sword_native_commentary_index.cpp) | KEEP_GENERIC | not established | 3 | not determined |
| [`scripts/sword_native_commentary_raw_corpus.cpp`](../../scripts/sword_native_commentary_raw_corpus.cpp) | KEEP_GENERIC | not established | 2 | not determined |
| [`scripts/sword_native_index.cpp`](../../scripts/sword_native_index.cpp) | KEEP_GENERIC | not established | 8 | not determined |
| [`scripts/sword_native_inventory.py`](../../scripts/sword_native_inventory.py) | KEEP_GENERIC | named test | 11 | source/native audit |
| [`scripts/sword_native_raw_corpus.cpp`](../../scripts/sword_native_raw_corpus.cpp) | UNDECIDED | not established | 4 | not determined |
| [`scripts/sword_native_raw_corpus_inventory.py`](../../scripts/sword_native_raw_corpus_inventory.py) | KEEP_GENERIC | named test | 6 | source/native audit |
| [`scripts/sword_native_raw_entry.cpp`](../../scripts/sword_native_raw_entry.cpp) | UNDECIDED | not established | 3 | not determined |
| [`scripts/tool_registry.py`](../../scripts/tool_registry.py) | KEEP_GENERIC | named test | 2 | not determined |
| [`scripts/validate.py`](../../scripts/validate.py) | KEEP_GENERIC | not established | 16 | not determined |
| [`scripts/verify_public_catalogue.py`](../../scripts/verify_public_catalogue.py) | KEEP_GENERIC | named test | 5 | not determined |

## Safeguards and next steps

Inventory every driver/rights/provenance contract before migrating an entry. Test actual compiled payload bytes and real native references in addition to any textual/static inventory.
Only promote from proposed classification after issue review and a tested replacement; historical scripts may be needed to reproduce old signed or published releases.
No registry entry authorizes editorial changes, user data changes or publication.
