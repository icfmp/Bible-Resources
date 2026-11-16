# Tool registry — source-bound post-MHCC inventory

This generated list covers every tracked `scripts/*.py`, `*.cpp` and `*.sh`. It lists static callers and review recommendations, **not** a licence to delete scripts or proof that they are exercised.
Generate/check: `python scripts/tool_registry.py --write` / `python scripts/tool_registry.py --check`.
The source-bound detailed registry is [TOOL_REGISTRY.json](TOOL_REGISTRY.json). No publishing credentials or raw commentary content enter the inventory.

## Lifecycle

- **KEEP_GENERIC:** retain the stable interface and strengthen tests.
- **GENERALIZE:** extract known edition-specific logic into a reviewed manifest, preserving existing proofs.
- **MERGE:** candidate overlapping research functions; only merge after comparing outputs and historical dependencies.
- **HISTORICAL/ARCHIVE:** retain for immutable proof/replay; archive only after evidence-based replacement, never by deleting blindly.
- **UNDECIDED:** source/caller audit required; no inferred deletion.

## Baseline counts

- GENERALIZE: 5
- HISTORICAL/ARCHIVE: 8
- KEEP_GENERIC: 23
- MERGE: 10
- UNDECIDED: 114

## All tracked tools

| Script | Classification | Tests | Static callers | Stage hint |
| --- | --- | --- | ---: | --- |
| [`scripts/audit_omitted_verse_notes.py`](../scripts/audit_omitted_verse_notes.py) | UNDECIDED | named test | 4 | source/native audit |
| [`scripts/audit_osis.py`](../scripts/audit_osis.py) | UNDECIDED | not established | 6 | source/native audit |
| [`scripts/audit_real_pilot.py`](../scripts/audit_real_pilot.py) | UNDECIDED | not established | 3 | source/native audit |
| [`scripts/audit_text.py`](../scripts/audit_text.py) | UNDECIDED | not established | 1 | source/native audit |
| [`scripts/bible_intake.py`](../scripts/bible_intake.py) | KEEP_GENERIC | not established | 9 | intake |
| [`scripts/bible_stage_runner.py`](../scripts/bible_stage_runner.py) | KEEP_GENERIC | named test | 6 | not determined |
| [`scripts/build.py`](../scripts/build.py) | KEEP_GENERIC | not established | 22 | publication/release |
| [`scripts/build_place_context.py`](../scripts/build_place_context.py) | UNDECIDED | not established | 4 | publication/release |
| [`scripts/catalogue_profiles.py`](../scripts/catalogue_profiles.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/catalogue_release_coverage.py`](../scripts/catalogue_release_coverage.py) | KEEP_GENERIC | named test | 9 | publication/release |
| [`scripts/check_provider_parity.py`](../scripts/check_provider_parity.py) | UNDECIDED | not established | 4 | not determined |
| [`scripts/check_updates.py`](../scripts/check_updates.py) | UNDECIDED | not established | 12 | not determined |
| [`scripts/commentary_anchor_parity.py`](../scripts/commentary_anchor_parity.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/commentary_andbible_jsword.py`](../scripts/commentary_andbible_jsword.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/commentary_android_text_witness.py`](../scripts/commentary_android_text_witness.py) | UNDECIDED | named test | 3 | source/native audit |
| [`scripts/commentary_android_webview_debug.py`](../scripts/commentary_android_webview_debug.py) | UNDECIDED | named test | 3 | not determined |
| [`scripts/commentary_bookcode_repair_receipt_guard.py`](../scripts/commentary_bookcode_repair_receipt_guard.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/commentary_chapter_cross_slot.py`](../scripts/commentary_chapter_cross_slot.py) | MERGE | named test | 2 | not determined |
| [`scripts/commentary_chapter_neighbors.py`](../scripts/commentary_chapter_neighbors.py) | MERGE | named test | 5 | not determined |
| [`scripts/commentary_chapter_p_boundaries.py`](../scripts/commentary_chapter_p_boundaries.py) | MERGE | named test | 2 | not determined |
| [`scripts/commentary_chapter_paragraph_overlap.py`](../scripts/commentary_chapter_paragraph_overlap.py) | MERGE | named test | 4 | not determined |
| [`scripts/commentary_chapter_ref_labels.py`](../scripts/commentary_chapter_ref_labels.py) | MERGE | named test | 5 | not determined |
| [`scripts/commentary_editorial_topology.py`](../scripts/commentary_editorial_topology.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/commentary_intake.py`](../scripts/commentary_intake.py) | KEEP_GENERIC | named test | 20 | intake |
| [`scripts/commentary_intro_chapter_text_review.py`](../scripts/commentary_intro_chapter_text_review.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/commentary_layout_census.py`](../scripts/commentary_layout_census.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/commentary_literal_erratum_preflight.py`](../scripts/commentary_literal_erratum_preflight.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/commentary_native_inventory.py`](../scripts/commentary_native_inventory.py) | KEEP_GENERIC | not established | 10 | source/native audit |
| [`scripts/commentary_native_raw_inventory.py`](../scripts/commentary_native_raw_inventory.py) | KEEP_GENERIC | named test | 11 | source/native audit |
| [`scripts/commentary_navigation_link_plan.py`](../scripts/commentary_navigation_link_plan.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/commentary_near_prose_unicode_review.py`](../scripts/commentary_near_prose_unicode_review.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/commentary_nonlink_word_alignment.py`](../scripts/commentary_nonlink_word_alignment.py) | MERGE | named test | 9 | not determined |
| [`scripts/commentary_nonlink_words.py`](../scripts/commentary_nonlink_words.py) | MERGE | named test | 2 | not determined |
| [`scripts/commentary_original_bookcode_repair.py`](../scripts/commentary_original_bookcode_repair.py) | UNDECIDED | named test | 3 | not determined |
| [`scripts/commentary_original_div1_book_consistency.py`](../scripts/commentary_original_div1_book_consistency.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/commentary_osis_intro_transport_probe.py`](../scripts/commentary_osis_intro_transport_probe.py) | UNDECIDED | named test | 2 | source/native audit |
| [`scripts/commentary_osis_mixed_transport_probe.py`](../scripts/commentary_osis_mixed_transport_probe.py) | UNDECIDED | named test | 3 | source/native audit |
| [`scripts/commentary_osis_rebuild_preflight.py`](../scripts/commentary_osis_rebuild_preflight.py) | UNDECIDED | named test | 2 | publication/release |
| [`scripts/commentary_osis_transport_probe.py`](../scripts/commentary_osis_transport_probe.py) | UNDECIDED | named test | 6 | source/native audit |
| [`scripts/commentary_paragraph_witness_probe.py`](../scripts/commentary_paragraph_witness_probe.py) | UNDECIDED | named test | 3 | source/native audit |
| [`scripts/commentary_private_candidate_xiphos_gui.py`](../scripts/commentary_private_candidate_xiphos_gui.py) | GENERALIZE | named test | 2 | not determined |
| [`scripts/commentary_private_text_compare.py`](../scripts/commentary_private_text_compare.py) | UNDECIDED | named test | 19 | source/native audit |
| [`scripts/commentary_prose_cross_slot.py`](../scripts/commentary_prose_cross_slot.py) | MERGE | named test | 3 | not determined |
| [`scripts/commentary_public_metadata_preflight.py`](../scripts/commentary_public_metadata_preflight.py) | UNDECIDED | named test | 3 | not determined |
| [`scripts/commentary_rebuild_attestation_draft.py`](../scripts/commentary_rebuild_attestation_draft.py) | UNDECIDED | named test | 3 | publication/release |
| [`scripts/commentary_reference_cross_slot.py`](../scripts/commentary_reference_cross_slot.py) | MERGE | named test | 4 | not determined |
| [`scripts/commentary_reference_registry_triage.py`](../scripts/commentary_reference_registry_triage.py) | UNDECIDED | named test | 5 | not determined |
| [`scripts/commentary_section_scope_audit.py`](../scripts/commentary_section_scope_audit.py) | UNDECIDED | named test | 3 | source/native audit |
| [`scripts/commentary_shared_raw_source_units.py`](../scripts/commentary_shared_raw_source_units.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/commentary_source_english_osis_alias.py`](../scripts/commentary_source_english_osis_alias.py) | UNDECIDED | named test | 5 | not determined |
| [`scripts/commentary_source_erratum_compiled_probe.py`](../scripts/commentary_source_erratum_compiled_probe.py) | UNDECIDED | named test | 2 | source/native audit |
| [`scripts/commentary_source_identity_lexical_gate.py`](../scripts/commentary_source_identity_lexical_gate.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/commentary_source_native_boundaries.py`](../scripts/commentary_source_native_boundaries.py) | UNDECIDED | named test | 3 | not determined |
| [`scripts/commentary_stock_andbible_android.py`](../scripts/commentary_stock_andbible_android.py) | GENERALIZE | named test | 2 | not determined |
| [`scripts/commentary_stock_candidate.py`](../scripts/commentary_stock_candidate.py) | UNDECIDED | named test | 7 | not determined |
| [`scripts/commentary_stock_prefix_topology.py`](../scripts/commentary_stock_prefix_topology.py) | UNDECIDED | named test | 6 | not determined |
| [`scripts/commentary_stock_xiphos_smoke.py`](../scripts/commentary_stock_xiphos_smoke.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/commentary_sword_identity_migration.py`](../scripts/commentary_sword_identity_migration.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/commentary_text_delta.py`](../scripts/commentary_text_delta.py) | UNDECIDED | named test | 10 | not determined |
| [`scripts/commentary_unmarked_division_coverage.py`](../scripts/commentary_unmarked_division_coverage.py) | UNDECIDED | named test | 1 | not determined |
| [`scripts/commentary_unresolved_lexical_triage.py`](../scripts/commentary_unresolved_lexical_triage.py) | MERGE | named test | 6 | not determined |
| [`scripts/commentary_witness.py`](../scripts/commentary_witness.py) | UNDECIDED | not established | 2 | source/native audit |
| [`scripts/commentary_xiphos_dual_reader.py`](../scripts/commentary_xiphos_dual_reader.py) | GENERALIZE | named test | 11 | not determined |
| [`scripts/commentary_xiphos_heading_probe.py`](../scripts/commentary_xiphos_heading_probe.py) | UNDECIDED | named test | 3 | source/native audit |
| [`scripts/commentary_xml_witness.py`](../scripts/commentary_xml_witness.py) | UNDECIDED | named test | 12 | source/native audit |
| [`scripts/compiled_stock_commentary_proof.py`](../scripts/compiled_stock_commentary_proof.py) | KEEP_GENERIC | named test | 6 | not determined |
| [`scripts/diff_sword_snapshots.py`](../scripts/diff_sword_snapshots.py) | UNDECIDED | named test | 5 | not determined |
| [`scripts/fast_stock_note_probe.py`](../scripts/fast_stock_note_probe.py) | UNDECIDED | named test | 3 | source/native audit |
| [`scripts/fetch_reviewed_schema.py`](../scripts/fetch_reviewed_schema.py) | UNDECIDED | not established | 11 | not determined |
| [`scripts/guard_commentary.py`](../scripts/guard_commentary.py) | KEEP_GENERIC | not established | 6 | not determined |
| [`scripts/guard_osis.py`](../scripts/guard_osis.py) | KEEP_GENERIC | named test | 18 | not determined |
| [`scripts/inspect_paragraph_rendering.py`](../scripts/inspect_paragraph_rendering.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/lsg_source_compare.py`](../scripts/lsg_source_compare.py) | HISTORICAL/ARCHIVE | named test | 10 | source/native audit |
| [`scripts/lsg_sword_compare.py`](../scripts/lsg_sword_compare.py) | HISTORICAL/ARCHIVE | named test | 2 | source/native audit |
| [`scripts/maintext_fidelity_classification.py`](../scripts/maintext_fidelity_classification.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/maintext_whitespace_patterns.py`](../scripts/maintext_whitespace_patterns.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/materialize_attested_lsg_release.py`](../scripts/materialize_attested_lsg_release.py) | HISTORICAL/ARCHIVE | named test | 1 | publication/release |
| [`scripts/materialize_attested_ztext_release.py`](../scripts/materialize_attested_ztext_release.py) | GENERALIZE | named test | 2 | publication/release |
| [`scripts/native_absorbed_verse_groups.py`](../scripts/native_absorbed_verse_groups.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/native_book_intro_screen.py`](../scripts/native_book_intro_screen.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/native_milestone_pair_audit.py`](../scripts/native_milestone_pair_audit.py) | UNDECIDED | named test | 12 | source/native audit |
| [`scripts/native_sword_markup_census.py`](../scripts/native_sword_markup_census.py) | UNDECIDED | named test | 5 | not determined |
| [`scripts/normalize_osis.py`](../scripts/normalize_osis.py) | KEEP_GENERIC | not established | 9 | not determined |
| [`scripts/note_whitespace_diagnostics.py`](../scripts/note_whitespace_diagnostics.py) | UNDECIDED | named test | 5 | not determined |
| [`scripts/osis_semantic_fidelity.py`](../scripts/osis_semantic_fidelity.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/pilot_fetch.py`](../scripts/pilot_fetch.py) | KEEP_GENERIC | not established | 23 | not determined |
| [`scripts/pilot_preflight.py`](../scripts/pilot_preflight.py) | KEEP_GENERIC | named test | 92 | not determined |
| [`scripts/pilot_runtime.py`](../scripts/pilot_runtime.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/pilot_subprocess.py`](../scripts/pilot_subprocess.py) | UNDECIDED | named test | 13 | not determined |
| [`scripts/prepare_darby_011_private_release_candidate.py`](../scripts/prepare_darby_011_private_release_candidate.py) | HISTORICAL/ARCHIVE | named test | 3 | publication/release |
| [`scripts/prepare_place_manifest.py`](../scripts/prepare_place_manifest.py) | UNDECIDED | not established | 1 | not determined |
| [`scripts/private_sword_bundle.py`](../scripts/private_sword_bundle.py) | UNDECIDED | named test | 3 | not determined |
| [`scripts/probe_andbible_android_emulator.py`](../scripts/probe_andbible_android_emulator.py) | UNDECIDED | not established | 6 | source/native audit |
| [`scripts/probe_andbible_android_private_import.py`](../scripts/probe_andbible_android_private_import.py) | UNDECIDED | named test | 5 | source/native audit |
| [`scripts/probe_andbible_jsword.py`](../scripts/probe_andbible_jsword.py) | UNDECIDED | not established | 3 | source/native audit |
| [`scripts/probe_darby_011_final_android.py`](../scripts/probe_darby_011_final_android.py) | HISTORICAL/ARCHIVE | named test | 2 | source/native audit |
| [`scripts/probe_lsg_v11n.py`](../scripts/probe_lsg_v11n.py) | HISTORICAL/ARCHIVE | not established | 2 | source/native audit |
| [`scripts/probe_official_osis.py`](../scripts/probe_official_osis.py) | UNDECIDED | not established | 3 | source/native audit |
| [`scripts/probe_private_repaired_darby_sword.py`](../scripts/probe_private_repaired_darby_sword.py) | HISTORICAL/ARCHIVE | not established | 6 | source/native audit |
| [`scripts/promote_sword_preview.py`](../scripts/promote_sword_preview.py) | UNDECIDED | named test | 8 | not determined |
| [`scripts/propose_upstream_edit.py`](../scripts/propose_upstream_edit.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/publish_reviewed_release.py`](../scripts/publish_reviewed_release.py) | KEEP_GENERIC | not established | 8 | publication/release |
| [`scripts/published_reference_audit.py`](../scripts/published_reference_audit.py) | UNDECIDED | named test | 3 | publication/release |
| [`scripts/publisher_osis_observation.py`](../scripts/publisher_osis_observation.py) | UNDECIDED | named test | 13 | publication/release |
| [`scripts/publisher_osis_preview_package.py`](../scripts/publisher_osis_preview_package.py) | UNDECIDED | named test | 6 | publication/release |
| [`scripts/publisher_osis_preview_readback.py`](../scripts/publisher_osis_preview_readback.py) | UNDECIDED | not established | 2 | publication/release |
| [`scripts/publisher_osis_sword_candidate.py`](../scripts/publisher_osis_sword_candidate.py) | UNDECIDED | named test | 4 | publication/release |
| [`scripts/publisher_osis_usfx_parity.py`](../scripts/publisher_osis_usfx_parity.py) | UNDECIDED | named test | 12 | publication/release |
| [`scripts/reader_xiphos_headless_smoke.py`](../scripts/reader_xiphos_headless_smoke.py) | UNDECIDED | named test | 9 | not determined |
| [`scripts/real_second_bible_probe.py`](../scripts/real_second_bible_probe.py) | UNDECIDED | named test | 6 | source/native audit |
| [`scripts/release_preflight.py`](../scripts/release_preflight.py) | KEEP_GENERIC | named test | 4 | publication/release |
| [`scripts/repair_osis_division_markers.py`](../scripts/repair_osis_division_markers.py) | UNDECIDED | named test | 6 | not determined |
| [`scripts/repair_osis_inline_markup.py`](../scripts/repair_osis_inline_markup.py) | UNDECIDED | named test | 6 | not determined |
| [`scripts/repair_osis_note_links.py`](../scripts/repair_osis_note_links.py) | UNDECIDED | named test | 12 | not determined |
| [`scripts/repair_osis_paragraph_indentation.py`](../scripts/repair_osis_paragraph_indentation.py) | UNDECIDED | named test | 6 | not determined |
| [`scripts/repair_osis_source_bytes.py`](../scripts/repair_osis_source_bytes.py) | UNDECIDED | named test | 9 | not determined |
| [`scripts/repair_osis_unlinked_reference_labels.py`](../scripts/repair_osis_unlinked_reference_labels.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/reviewed_compiled_commentary_rebuild.py`](../scripts/reviewed_compiled_commentary_rebuild.py) | KEEP_GENERIC | named test | 12 | publication/release |
| [`scripts/select_sources.py`](../scripts/select_sources.py) | UNDECIDED | not established | 5 | not determined |
| [`scripts/smoke.py`](../scripts/smoke.py) | UNDECIDED | named test | 10 | not determined |
| [`scripts/source_native_division_markers.py`](../scripts/source_native_division_markers.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/source_native_index_audit.py`](../scripts/source_native_index_audit.py) | UNDECIDED | named test | 3 | source/native audit |
| [`scripts/source_native_layout_anchors.py`](../scripts/source_native_layout_anchors.py) | UNDECIDED | named test | 3 | not determined |
| [`scripts/source_native_maintext_probe.py`](../scripts/source_native_maintext_probe.py) | UNDECIDED | named test | 17 | source/native audit |
| [`scripts/source_native_nonspace_boundaries.py`](../scripts/source_native_nonspace_boundaries.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/source_native_note_positions.py`](../scripts/source_native_note_positions.py) | UNDECIDED | named test | 5 | not determined |
| [`scripts/source_native_notes_audit.py`](../scripts/source_native_notes_audit.py) | UNDECIDED | named test | 7 | source/native audit |
| [`scripts/source_native_ordered_body.py`](../scripts/source_native_ordered_body.py) | UNDECIDED | named test | 6 | not determined |
| [`scripts/source_native_osis_boundary_positions.py`](../scripts/source_native_osis_boundary_positions.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/source_native_osis_structure_screen.py`](../scripts/source_native_osis_structure_screen.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/source_native_osis_target_addressability.py`](../scripts/source_native_osis_target_addressability.py) | UNDECIDED | named test | 6 | not determined |
| [`scripts/source_native_paragraph_counts.py`](../scripts/source_native_paragraph_counts.py) | UNDECIDED | named test | 8 | not determined |
| [`scripts/source_native_record_scope_triage.py`](../scripts/source_native_record_scope_triage.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/source_native_scope.py`](../scripts/source_native_scope.py) | UNDECIDED | named test | 8 | not determined |
| [`scripts/source_native_structural_whitespace.py`](../scripts/source_native_structural_whitespace.py) | UNDECIDED | named test | 5 | not determined |
| [`scripts/source_native_structure_topology.py`](../scripts/source_native_structure_topology.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/source_native_word_boundaries.py`](../scripts/source_native_word_boundaries.py) | UNDECIDED | named test | 9 | not determined |
| [`scripts/source_osis_inventory.py`](../scripts/source_osis_inventory.py) | UNDECIDED | named test | 31 | source/native audit |
| [`scripts/source_osis_note_link_triage.py`](../scripts/source_osis_note_link_triage.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/source_osis_note_markup_shape.py`](../scripts/source_osis_note_markup_shape.py) | UNDECIDED | named test | 2 | not determined |
| [`scripts/source_usfx_newline_provenance.py`](../scripts/source_usfx_newline_provenance.py) | UNDECIDED | named test | 6 | not determined |
| [`scripts/source_usfx_structure.py`](../scripts/source_usfx_structure.py) | UNDECIDED | named test | 9 | not determined |
| [`scripts/stable_sword_refs.py`](../scripts/stable_sword_refs.py) | UNDECIDED | named test | 39 | not determined |
| [`scripts/stage4_subcheck_receipts.py`](../scripts/stage4_subcheck_receipts.py) | UNDECIDED | named test | 4 | not determined |
| [`scripts/stage_darby_011_release.py`](../scripts/stage_darby_011_release.py) | HISTORICAL/ARCHIVE | not established | 1 | publication/release |
| [`scripts/stage_verified_stock_commentary.py`](../scripts/stage_verified_stock_commentary.py) | UNDECIDED | not established | 2 | not determined |
| [`scripts/stock_reuse_preflight.py`](../scripts/stock_reuse_preflight.py) | UNDECIDED | named test | 3 | not determined |
| [`scripts/sword_commentary_raw_key.cpp`](../scripts/sword_commentary_raw_key.cpp) | UNDECIDED | not established | 4 | not determined |
| [`scripts/sword_missing_verse_witness.py`](../scripts/sword_missing_verse_witness.py) | UNDECIDED | named test | 4 | source/native audit |
| [`scripts/sword_native_commentary_index.cpp`](../scripts/sword_native_commentary_index.cpp) | KEEP_GENERIC | not established | 8 | not determined |
| [`scripts/sword_native_commentary_raw_corpus.cpp`](../scripts/sword_native_commentary_raw_corpus.cpp) | KEEP_GENERIC | not established | 10 | not determined |
| [`scripts/sword_native_index.cpp`](../scripts/sword_native_index.cpp) | KEEP_GENERIC | not established | 17 | not determined |
| [`scripts/sword_native_inventory.py`](../scripts/sword_native_inventory.py) | KEEP_GENERIC | named test | 20 | source/native audit |
| [`scripts/sword_native_raw_corpus.cpp`](../scripts/sword_native_raw_corpus.cpp) | UNDECIDED | not established | 12 | not determined |
| [`scripts/sword_native_raw_corpus_inventory.py`](../scripts/sword_native_raw_corpus_inventory.py) | KEEP_GENERIC | named test | 24 | source/native audit |
| [`scripts/sword_native_raw_entry.cpp`](../scripts/sword_native_raw_entry.cpp) | UNDECIDED | not established | 7 | not determined |
| [`scripts/tool_registry.py`](../scripts/tool_registry.py) | GENERALIZE | named test | 2 | not determined |
| [`scripts/usfx_schema_gate.py`](../scripts/usfx_schema_gate.py) | UNDECIDED | named test | 3 | not determined |
| [`scripts/validate.py`](../scripts/validate.py) | KEEP_GENERIC | not established | 25 | not determined |
| [`scripts/verify_public_catalogue.py`](../scripts/verify_public_catalogue.py) | KEEP_GENERIC | named test | 5 | not determined |

## Safeguards and next steps

Inventory every driver/rights/provenance contract before migrating an entry. Test actual compiled payload bytes and real native references in addition to any textual/static inventory.
Only promote from proposed classification after issue review and a tested replacement; historical scripts may be needed to reproduce old signed or published releases.
No registry entry authorizes editorial changes, user data changes or publication.
