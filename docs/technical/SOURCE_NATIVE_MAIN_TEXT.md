# OSIS-to-native Scripture text verification

**Active source path:** exact immutable original -> reviewed cleaned **OSIS** master -> SWORD compilation -> independent native readback. This procedure covers source/native text evidence, not permission, editorial sign-off or release approval. See the [production contract](../PRODUCTION_PIPELINE.md).

## Required evidence

1. Pin original and approved cleaned OSIS bytes, SHA-256, edition, rights, canon and versification. Preserve authorial omitted verses as omissions; do not create missing text from available native index slots.
2. Validate the reviewed OSIS source with the official schema and [source inventory](SOURCE_OSIS_INVENTORY.md). Inspect all authored verse keys, introductions and source-only sections without assuming the native versification matches.
3. For a native candidate, use `scripts/publisher_osis_sword_candidate.py --approved --resource-id <approved-module-id>` with pinned reviewed cleaned OSIS, instead of the old publisher-download research route, for source-to-SWORD checks, together with `scripts/sword_native_index.cpp`, `scripts/sword_native_raw_corpus.cpp`, `scripts/sword_native_raw_entry.cpp`, and the strict `scripts/research/bible/native_raw_main_text.py` parser as needed. The private source parser `scripts/research/bible/source_osis_verse_notes.py` preserves original verse text and note bodies in memory; **never log or publish those values**.
4. Compare **all** source-addressable numbered verse text against actual compiled entries, not a few reader-visible samples. Record exact character equality, Unicode normalization-only changes, whitespace-only changes, punctuation/case differences, changed prose, duplicate/missing native keys, and compiler-created unaddressable keys as separate classes.
5. Independently verify notes, callers, explicit cross-references, headings, poetry, paragraphs, book introductions, and layout anchors. The source/native structural and note checks must agree with the main-text results. Run actual SWORD and independent reader checks before any publication decision.

## Interpreting the result

- A successful OSIS XSD check or native index-key match does **not** prove source-to-native text, annotation or structural fidelity.
- A whitespace-equivalent word stream does **not** prove faithful poetry, punctuation, paragraph breaks or typography.
- A stock upstream binary is not an approved replacement for a reviewed source-derived OSIS master merely because it renders a few verses.
- A source-authored omission cannot be repaired by inserting an unrelated verse or note.

Keep textual source material private. Publish only bounded reference IDs, status categories, counts, source fingerprints and review receipts. Any non-equivalent source/native behavior requires a documented editorial disposition under `sources/cleaned/**/editorial/`. Unresolved evidence blocks acceptance.

Related procedures: [notes](SOURCE_NATIVE_NOTES_AUDIT.md), [native index](SOURCE_NATIVE_INDEX_AUDIT.md), [whole-corpus verification](NATIVE_SWORD_WHOLE_CORPUS.md), and [release gates](../PRODUCTION_PIPELINE.md).
