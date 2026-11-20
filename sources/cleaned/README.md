# Cleaned/maintained source editions

The new canonical layout is
`sources/cleaned/<type>/<resource-id>/`, where `<type>` is one of
`bibles`, `commentaries`, `dictionaries`, `encyclopedias`, `other`.
Maintain **one versioned, source-faithful structured master** per edition,
preferably real OSIS or USFM (not a reconstructed pseudo-source).

Apply reviewed **generic**, deterministic, reversible structural cleanup:
consistent headings, paragraphs, introductions, poetry, references, Unicode
and nonsemantic presentation wrappers; keep actual words, punctuation, verse
numbering, deliberate omissions, notes and authored semantic structure.
Retain every translation note, variant, cross-reference, Strong/morphology tag
and its **position relative to the correct word** where present.

Each cleaned master needs original source identity/checksum, permissions for
derivatives and public redistribution, exact cleanup manifest, before/after
hashes, independent witness comparison and full SWORD round-trip results.
Do not publish or commit copyrighted source bodies without authorization.
The original bytes belong in `sources/original/` only if mirroring is allowed.

**Legacy compatibility:** `sources/cleaned/mhc/` currently contains existing
MHC provenance/cleanup documents, **not an editable OSIS source file**.
Preserve these URLs and historical receipts until a separately validated
migration. New cleaned source editions always use the type-specific layout.

See [workspace layout](../../docs/WORKSPACE_LAYOUT.md) and
[six-phase production policy](../../docs/SOURCE_FIRST_EDITORIAL_PIPELINE.md).
