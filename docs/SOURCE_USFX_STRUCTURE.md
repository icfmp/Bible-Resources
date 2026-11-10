# Generic source-native USFX structure inventory (stage 3)

This read-only audit is for an **original publisher USFX** archive, not a
license to convert, rewrite or publish its contents. It applies to eBible
sources such as `frajnd-2024` and the earlier WEBP research fixture, with no
edition-specific versification exceptions. Tracked under [#28](https://github.com/icfmp/Bible-Resources/issues/28),
with the second-real-source checkpoint in [#62](https://github.com/icfmp/Bible-Resources/issues/62).

## What the original-source inspector does

`scripts/source_usfx_structure.py` parses the full original XML using a
non-recovering, network-disabled XML parser. It rejects DTD/entity
declarations, duplicate book IDs, invalid roots, structurally unsafe or
oversized files, and limits total elements. It preserves immutable source
bytes and records:

- **every original book** in its original order, with chapter-marker and
  expanded numbered-verse counts;
- ordered numbered-key SHA-256 and original source XML SHA-256, alongside an
  independent inventory via `scan_usfx`;
- source XML element/attribute counts and a hash of structural-event order
  (no Bible words, note bodies, title strings or private reference targets);
- note kinds and literal-vs-automatic caller counts, plus the number of
  heading, paragraph, poetry, reference and explicit-target elements;
- duplicates, reversed verse/chapter keys, range anomalies and illegal
  note-contained verse/chapter markers, with bounded reference-only examples.

Any such structural discrepancy is **BLOCKED**, not silently normalized or
`fixed` using standard-canon assumptions. Source-only books and unusual
markup remain visible. A missing or unfamiliar element is not silently
dropped; XML Schema validation and independent editorial assessment are
separate gates.

The source archive and content never enter GitHub artifacts or logs. The
metadata receipt from stage 3 can be compared between runs and used to
investigate a source revision without distributing the authored Scripture.

## Evidence **not** certified by this inventory

- eBible's [USFX format documentation](https://ebible.org/usfx/) identifies
  the [official XSD](https://ebible.org/usfx.xsd). The exact 67,661-byte
  upstream snapshot was observed and compiled offline in
  [GitHub Actions run 42812816320](https://github.com/icfmp/Bible-Resources/actions/runs/42812816320),
  then SHA-256 pinned in `config/usfx-schema-policy.json`. Stage 3 now
  downloads and checks the pinned snapshot before validating the original
  source; changed upstream bytes **block**, never silently update the
  approved standard. An XML parser or element-counter success alone remains
  insufficient.
- Note body/caller and text-position equivalence to a compiled SWORD module
  is still part of stages 4 and 5. This stage cannot prove them.
- The publisher's exact edition/revision must be independently evidenced;
  the URL and module naming alone cannot prove equivalence.
- A faithful **reuse** of an official stock SWORD module need not invent a
  USFX→OSIS conversion. Mark conversion **N/A** only when the approved
  workflow genuinely does not convert anything and the original→compiled
  fidelity investigation supports this choice. A conversion performed for
  a rebuilt SWORD candidate demands independent source→converted parity.
- No original book, note, verse or special typography may be silently
  omitted. The 2024 JND eBible `Versification=Luther` is retained as source
  evidence and native reader registry comparison is still pending.

Even after the official XSD validates, `bible_stage_runner.py` reports
**PARTIAL** until the publisher's edition provenance and applicability of a
conversion are reviewed by the project maintainer. A successful stock-SWORD
reuse path may document `USFX→OSIS conversion: N/A (not performed)`, but
cannot infer original-to-binary text or annotation equivalence: those gates
belong to stages 4 and 5. The seven-stage checkbox stays unchecked until
the remaining authorial source review is complete.

## Reproduce offline

```sh
python -m unittest discover -s tests -p 'test_source_usfx_structure.py' -v
python -m unittest discover -s tests -p 'test_bible_stage_runner.py' -v
```

On an open `[Import]` resource issue, the repository owner runs exactly
one original-source diagnostic using:

```text
/bible-audit frajnd-2024 3
```

It produces a metadata-only report and a permanent issue comment with
the exact Actions run URL. No Scripture source ZIP is committed or uploaded.
