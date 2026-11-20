# MHC — independent CCEL comparison: conclusions

**Historical comparative research, not the source of the released MHC edition.** This comparison uses independent SHA-pinned CCEL electronic volumes and CrossWire's source/stock data. It is retained because it identifies **why CCEL is not safe to substitute silently** for the exact CrossWire edition. The full intermediate tables and successive diagnostics remain available in this file's Git history and [import issue #285](https://github.com/icfmp/Bible-Resources/issues/285).

## Findings that affect editorial decisions

The original six-volume comparison classified **1,606** sections with broadly different visible text:

| Class | Count | Meaning |
| --- | ---: | --- |
| Same words, different punctuation or nonword text | 1,222 | Not proof of a wrong reading |
| CCEL text embedded in longer CrossWire passage | 110 | Scope/section comparison needed |
| CrossWire text embedded in longer CCEL passage | 39 | Scope/section comparison needed |
| Different Unicode word token sequence | 235 | May reflect alternative text, order, source title or alignment |

These **are comparison classes, not 1,606 independently verified CrossWire errors**. The 235 token differences and the long-section cases require the specific source, source edition, paragraph boundaries and genuine native K/I/TOP locations to be examined before proposing a correction.

Particular caution is required with **Psalms superscriptions**, which can be source scripture titles rather than commentary prose. The original research isolated 112 Psalm opening paragraph cases with source-title alignments and a few unresolved repetitions/word-order cases. **Psalm 7** includes a distinct 136-word source paragraph whose editorial status cannot be dismissed as merely a repeated title. Do not delete or reinsert such spans on word-token matching alone.

## Resulting policy for this edition

- The approved MHC 0.1.0 is derived from the **identified CrossWire OSIS**, not reconstructed by blending in CCEL passages.
- No alternative CCEL wording, headings, lexically different fragments or extra material is automatically promoted into the compiled source.
- Suspected omitted exposition or nonmatching paragraphs require separate cited source evidence, rights review, authorial scope mapping, independent text/annotation readback and explicit editorial authorization.

See [final 0.1.0 release](../releases/MHC-0.1.0.md), [cleaned-source manifest](../../CLEANUP_MANIFEST.json), [source research question #295](https://github.com/icfmp/Bible-Resources/issues/295) and the historical [GitHub Actions source/stock comparison #44068890903](https://github.com/icfmp/Bible-Resources/actions/runs/44068890903). The original numeric evidence can be recovered from pre-cleanup commits rather than carried through every future contributor's reading path.
