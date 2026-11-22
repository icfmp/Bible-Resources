# OSIS-to-native notes and reference fidelity

**Purpose:** verify that note bodies, note callers, note placement and explicit cross-reference destinations in a reviewed OSIS source survive SWORD compilation. Source text and annotation bodies must remain private. An individual successful diagnostic never approves an editorial modification or a release.

## Source and native witnesses

Start with the exact SHA-pinned original and reviewed cleaned OSIS master, its edition and rights evidence, and the independently built SWORD candidate. `scripts/research/bible/source_osis_verse_notes.py` reads literal numbered-verse source text, note bodies, original caller labels, source note positions and explicit OSIS destinations in memory. Do not publish its returned text.

Compare these observations against actual native `RawText` or `zText` entries, not only HTML rendered by one reader. The strict native note-position helper `scripts/research/bible/source_native_note_positions.py` can measure note anchor offsets without creating or guessing missing notes. The OSIS source link triage tool `scripts/source_osis_note_link_triage.py` inventories explicit authorial references; source-native OSIS candidate validation remains separate.

Keep these distinctions visible in review receipts:

- Numbered-verse note identities, types and ordering, including differences in note counts.
- Literal note bodies versus Unicode/whitespace-only differences and material textual differences.
- Note caller labels and their exact character positions within their authorial text, rather than an assumption of matching note order.
- Explicit reference destinations and original targets, including absent or unresolved targets. A textual label is not itself an authorized `osisRef`.
- Notes in introductions, titles, between numbered verses, and source-only or unaddressable locations. Do not discard them merely because a native verse slot is missing.
- Invalid/ambiguous native XML fragments. Classify as unknown or blocked, never as an empty annotation.

## Review and publication boundary

The active [production contract](../PRODUCTION_PIPELINE.md) requires full-corpus source/native fidelity and independent reader validation. Preserve exact source wording, punctuation, editorial notes, versification and original reference destinations. If a candidate requires a correction, record the evidence, affected references and reversible operation in the edition's `sources/cleaned/**/editorial/` materials; a diagnostic alone cannot authorize edits.

Keep reports free of copied Scripture or commentary. Report bounded reference identifiers, counts, classifications and verified hashes only. See also [main-text fidelity](SOURCE_NATIVE_MAIN_TEXT.md) and [native index checks](SOURCE_NATIVE_INDEX_AUDIT.md).
