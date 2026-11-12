# Editorial rules

Preserve the exact original as immutable input with hash and attribution. Distinguish faithful technical repairs from an optional reader-optimized edition. When a commentary repeats biblical passages, produce an audit report and proposed removal, but **never delete passages automatically**. Textual quotations may be integral to the author's reasoning. Preserve cross references and meaningful emphases.

Warnings: all-caps paragraphs, oversized bold blocks, corrupted numbering, duplicated headings, broken tags, inappropriate fonts/colors, and embedded scripture blocks. Human review decides on ambiguous transformations. Changes must be documented and reversible; provide before/after examples. Do not rewrite theology or the translation during technical cleaning.

## Principle: preserve authored content; repair demonstrable technical defects

**The owner requires both faithful content and technically correct resources.**
Source-fidelity checks are a baseline, **not** a reason to ship known
non-functional or misdirected links. Conversely, technical repair is **not
permission to rewrite** Scripture, punctuation, notes, theological meaning,
textual-critical choices, authored verse numbers, or genuine editorial
structure.

Keep three separate objects in the evidence trail:

1. **Immutable publisher original:** exact edition, byte SHA-256, provenance
   and all original attributes retained for verification and rollback.
2. **Reviewed technical repair plan:** reference/host and exact old/new
   *machine-readable metadata or rendering behavior*, reason, independent
   evidence, affected source checksum, expected invariants, tests and a
   reversible rollback; an unconfirmed interpretation is not an approved fix.
3. **Reader-ready candidate:** technical repairs applied deterministically;
   verify it against both the pinned source **and** the approved delta.
   Unchanged visible note and Bible text must still pass a full-corpus
   fidelity check; independently test the repaired behavior in a real reader.

**Examples:**
- A note's *printed* “Exodus 30:10” is correct but the underlying OSIS
  `osisRef` points to a nonexistent Leviticus 30:10: correct the navigational
  attribute **only after verifying the intended target**, not the note text.
- A syntactically valid OSIS target can still point to the wrong book.
  Check semantics in addition to index addressability.
- A footnote discussing a verse intentionally absent from the publisher's
  textual edition is legitimate content. Retain its explanation and omission;
  never manufacture the verse. An unavailable destination must not masquerade
  as a working link: use an evidenced non-deceptive rendering or navigation
  decision that preserves the authorial annotation.
- Source/native whitespace differences are **diagnostic**, not automatically
  defects requiring byte-identical formatting. Repair demonstrated semantic
  line-break, paragraph, poetry, title or note-call losses and broken
  presentation; do not rewrite harmless XML serialization whitespace.

For any technical repair, record the old and new attribute/rendering and
exact tests so that it can be reverted. When publisher intent is ambiguous,
investigate and request upstream clarification instead of silently guessing.
A candidate with unresolved demonstrated material defects stays **blocked**;
a warning does not substitute for a known necessary repair. Editorial and
publication approval remain separate gates.

## Strict structure handling

Editorial cleanup must never override valid intentional Scripture formatting, including OSIS stanzas (`lg`), poetic lines and their levels (`l`), quotations (`q`), headings, translation additions, the divine name, original emphasis, notes and verse milestones. Unlike advisory typography findings, structural failures are **blocking** and report the source file and line. Never infer whether an unusual case is a mistake: follow [the reviewed OSIS normalization contract](NORMALIZATION_POLICY.md) and add an explicit tested rule before retrying.

## Commentary-specific rules

The official OSIS structure for a commentary is not merely a Bible verse with different words. Preserve the CrossWire commentary entry relationship `div[annotateType="commentary"][annotateRef]`, including book/chapter/range associations, discontinuous references and separate authorial sections. Do not flatten commentary sections, turn quotation material into a Bible passage, infer verse keys, or remove embedded Scripture excerpts merely because the same passage can be read in Bible. The separate fail-closed commentary gate is described in [COMMENTARY_POLICY.md](COMMENTARY_POLICY.md); the original source must survive unchanged.

## Printed editions as layout references — including different editions

For Bibles and commentaries, **readability matters alongside faithful content**. Prefer a verified PDF/facsimile of the identical source edition when available, but **do not leave a clearly broken or unreadable layout in place merely because the exact edition cannot be found**. A different, reliably identified printed edition can be used as an *editorial model* for paragraph boundaries, poetic line/stanza grouping, titles, indentation, quotation layout, and commentary sections.

Review candidate references in this order:
1. The exact matching edition or its faithful facsimile, if usable.
2. A related edition of the **same work** (different printing or revision, ideally the same translation/language) whose structure makes sense for the text in the SWORD module.
3. Other trustworthy editions as **examples of readable editorial layout**, never as proof of the source edition's original structure.

Document the source PDF URL, work, translator/language, publisher, edition/year and page(s), plus the affected SWORD module and verse/entry keys. Explicitly label every difference between the reference edition and our module. **Never copy or silently replace words, punctuation, scriptural references, verse boundaries, authorial arguments, or notes from a different edition.** Do not carry over editorial divisions that conflict with the actual text, alter a meaningful poetic parallelism, or change the scope of commentary entries.

If a matching edition demonstrates a structure lost during conversion, the change can be logged as a **faithful restoration**. If a different edition inspires a more readable division, log it as a **reviewed editorial adaptation** in a distinct `reader_optimized` edition, subject to verified derivative rights. Neither case authorizes unreviewed automatic rewriting. Every approved mapping must be precise, testable, reversible, and documented with before/after excerpts.

Where competing layouts remain equally plausible, prefer the simplest readable structure that preserves the actual text's logic, and require explicit editorial review before adding a deterministic normalization rule. An unavailable or conflicting PDF is a reason to **review**, not to force an ugly layout or make a silent guess. A PDF is evidence, not automatically licensed for republication; original files, copyrights and provenance remain protected. Printed page numbers are not original XML line numbers.
