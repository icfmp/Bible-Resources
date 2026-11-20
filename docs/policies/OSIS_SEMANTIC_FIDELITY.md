# Generic OSIS semantic fidelity — source-side stage

This reusable OSIS source-to-candidate auditor is part of [issue #28](https://github.com/icfmp/Bible-Resources/issues/28). It is deliberately translation-, language-, book-count-, Strong- and versification-neutral.

## Run

Independently validate BOTH exact inputs against the project's pinned official OSIS schema first. Then:

    python scripts/osis_semantic_fidelity.py \
      --source-osis /private/original.osis.xml \
      --candidate-osis /private/reviewed-candidate.osis.xml \
      --report /private/new-semantic-report.json

The command never edits either input, refuses to overwrite evidence, writes a text-free report and exits 0 only when all its source/candidate semantic lanes match. It exits 1 for genuine semantic differences, and blocks malformed or ambiguous input. No source text, Scripture words or note bodies are copied to the report.

## What is compared

Every book is SHA-fingerprinted independently for all of the following:

1. **Main text including exact punctuation, whitespace, intro headings and text outside verses**, excluding note body text. XML entity references are decoded once by the parser; separate whole-original-byte SHA-256 hashes retain evidence of comment/entity-spelling differences.
2. **Notes**: ordered exact note text, all attributes including type and callout, and their positions relative to cumulative source words and main text. A shifted note or note label is detected.
3. **Lexical word elements**: ordered complete word text and all original attributes (including lemma/Strong/morphology when present). An edition without such attributes is valid.
4. **Explicit cross-reference targets**: authored target attributes, label text, placement and order. SWORD-derived reference lists are never treated as authored OSIS targets.
5. **Structure**: separate starts and ends of original verses, chapters, titles, paragraphs, poetry, quotations, notes, introductions and other presentation elements with cumulative book-word and text positions. Container boundaries and sID/eID milestones are represented separately.
6. **Other markup**: every ordered OSIS element and its attributes, plus the existing strict authorial book/chapter/verse key inventory. Missing or shifted source verse keys are never synthesized.

Reports expose only SHA-256, counts, book IDs, changed semantic lane names, and explicit proof-status limitations. They are usable as the before/after semantic layer for separately approved reversible edits in issue #3.

## Independent proof boundaries

This source-side OSIS comparator **does not** claim:

- Approved source provenance or correctness of the publisher's original USFM/USFX to OSIS conversion.
- Compiled SWORD text, punctuation, note body, footnote position, reference or Strong-value fidelity. That still needs a real native reader readback, not a second copy of the OSIS source.
- Official OSIS XSD validation (must be run separately), rights to redistribute, a working GTK/JSword/Xiphos reader or editorial publication approval.

Tests use two **different synthetic OSIS edition shapes** and intentionally mutate words, punctuation, lemma attributes, note text and caller, moved notes, explicit targets, poetry closing events, introductions, verse IDs and book order. This does NOT constitute validation against a second different, rights-cleared real Bible.

The [native SWORD index evidence](NATIVE_SWORD_INDEX_INVENTORY.md), [authorial reference evidence](SOURCE_OSIS_INVENTORY.md), and original [LSG audit research](LSG_AUDIT_RESEARCH_HANDOFF.md) remain independent sources of proof. Issue #28 stays OPEN until their full content/structure/native reader equivalents and the second real Bible are validated.

No published LSG 0.1.0 content, source file, SWORD payload or rights record changes in this work.
