# Source-to-native book and verse scope audit

**Purpose:** verify that a compiled SWORD module represents exactly the authorially intended source scope, without silently adding, omitting or inventing a book, chapter or verse.

## Inputs

Use an immutable, edition-pinned original source, its documented canon and versification, a reviewed cleaned candidate, and an independently built native SWORD candidate. Capture their hashes, module metadata, compiler version, source book identifiers and SWORD module version.

## Procedure

1. Enumerate *all* source book identities, chapter boundaries, verse numbers, omitted-verse markers and noncanonical sections. Keep source sections distinct from source verses.
2. Enumerate actual native SWORD keys and populated entries, not merely reader-visible chapter headers.
3. Compare the two inventories by an explicit, reviewed identity mapping. Do not infer equivalence from similar names or count totals.
4. Classify each difference: edition-specific canon, missing compiler key, unpopulated key, numbering convention, source omission, source defect or reader-only display behavior.
5. For every non-exact correspondence, link source evidence and editorial disposition beside the cleaned resource. Leave dubious cases blocked.

## What the audit cannot prove

Matching keys does **not** prove that wording, punctuation, notes, cross-reference targets, paragraph structure or lexical annotations survived compilation. Run the other [source/native fidelity audits](README.md) and [full production gates](../PRODUCTION_PIPELINE.md).

The read-only standard identity mapping is in `config/standard_usfm_osis_66.json` where appropriate; a translation may have an entirely different verified canon/versification. Never fabricate omitted verses simply because a stock SWORD versification contains an index slot.

**Previous edition experiment:** preserved verbatim in [historical source/native book-scope research](../../history/pilots/WEBP_SOURCE_NATIVE_BOOK_SCOPE_2026-11-20.md), separate from this general method.
