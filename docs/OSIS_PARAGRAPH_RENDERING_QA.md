# OSIS → SWORD paragraph rendering: reusable QA and remediation

**Status:** operational review guidance for **all new Bible imports and updates**.
This is **not** a rule to remove leading symbols or whitespace from every
resource. The exact authorial source, its conventions, and actual reader
behaviour control every decision.

**Origin of this checklist:** the published BPC J. N. Darby 2024 rev. 2.0
`BRJND2024` 0.1.0 post-release defect, [issue #234](
https://github.com/icfmp/Bible-Resources/issues/234), corrected and
independently released as [0.1.1](
https://github.com/icfmp/Bible-Resources/releases/tag/darby-jnd-2024-0.1.1).
Detailed [source/native diagnosis](evidence/darby-2024-paragraph-postrelease-qa.md),
[final actual-reader evidence](evidence/darby-2024-0.1.1-final-reader-qa.md)
and [release note](releases/DARBY-JND-2024-0.1.1.md) provide the exact proofs.

## Two distinct failure mechanisms

### 1. Literal editorial division marks entered displayed Scripture

The official Darby OSIS source contains leading `*`, `**` and `***` at
authored topic divisions and in poetic structures. These are editorial
**layout semantics**, not arbitrary typographical debris and not additions
to Scripture. When left as literal verse characters, SWORD readers may
print them directly. The `0.1.0` binary did that.

The source also uses distinct lexical/text-critical signs. Never infer
that every leading `*` is a subject division: `*Dieu`, `*Seigneur`,
`*[` and symbols inside an annotated span require separate examination
against the **exact edition's** printed/editorial explanation. The meaning
of symbols in another Bible may be entirely different.

For Darby 2024, a complete source inventory classified **522** literal
verse-leading star sequences as **521** approved subject/stanza divisions
(477 paragraph-level, 13 major paragraph-level, 31 poetic) and **one**
genuine protected text-critical sign. The 521 were moved to reversible
typed OSIS milestones. Their original star counts and host verse IDs
remain recoverable. The protected text-critical sign remains ordinary text.

**Important interoperability trap:** putting the authorial `*` into the
OSIS `milestone@marker` attribute looked structurally sensible but
caused actual JSword/AndBible rendering to **display that glyph again**.
The accepted Darby candidate instead encodes the original count into a
non-displayed, typed `subType`, e.g.:

```xml
<milestone type="x-subject-division" subType="x-original-ascii-star-1"/>
```

This is an **audited Darby-specific representation of source semantics**,
not an instruction to invent this encoding for every future edition.
Check the correct OSIS syntax and schema, full source/native preservation
and actual independent reader rendering before selecting any encoding.
OSIS schema validity, textual fidelity and visible GUI fidelity are
three different gates.

### 2. XML formatting indentation leaked into native verse text

The original OSIS was pretty-printed. At many paragraph starts, an OSIS
verse milestone was followed by a newline and ASCII indentation spaces
intended to make the **XML** readable, not to create authorial prose
indentation. The compiler/native renderer could retain some of these as
visible spaces. In the published Darby 0.1.0, native representative
paragraphs including Gen 6:9, 6:13 and 7:17 began with two ASCII spaces.

Illustrative XML **not a quotation from the Bible**:

```xml
<p><verse osisID="Gen.1.1" sID="Gen.1.1"/>
            Example prose only<verse eID="Gen.1.1"/></p>
```

For Darby the corrective overlay removed precisely **4,690** verified
paragraph-start XML formatting spans (56,288 indentation spaces).
It did **not** globally collapse spaces, touch a verse's internal prose,
normalize poetry, remove note content, or change original publisher files.

A compiler may still insert **one** leading native space after these fixes;
one raw whitespace code point is not automatically a reader-facing defect.
The criterion is a correctly aligned actual passage, supported separately
by complete source/native checks.

## Repeatable seven-stage import checks

Use these checks **before** publication of any newly compiled Bible (and
on module updates where different rendering/compiler behaviour is possible):

1. **Stage 2/3 — acquire and understand source.** Pin exact original
   publisher bytes and SHA-256, edition rights and source conventions.
   Inventory paragraph and poetry containers, verse milestones, highlights,
   all leading symbols and exact whitespace categories. Classify potential
   presentation symbols and legitimate text-critical or lexical symbols
   separately. Preserve original files unchanged. For non-OSIS originals,
   verify the USFM/USFX → OSIS transformation first.
2. **Stage 4a–c — inspect source AND compiled raw SWORD.** Compare the
   original start-of-verse characters and their XML container context
   against the actual native `RawText`/`zText` bytes and the final
   installed-version ID. Measure leading spaces, linefeeds, NBSP,
   newline/indent patterns and any visible literal formatting tokens.
   Do not assume a clean canonical word/punctuation comparison proves
   good paragraph rendering. Check source and native verse indexes too.
3. **Stage 5 — prove semantic and structural preservation.** For each
   symbol proposed for non-displayed structural metadata, record original
   symbol, level, location and meaning; prove a reversible mapping and
   check that no protected textual symbol moves. Verify **all** verse IDs,
   main-text characters other than the explicitly attested layout edit,
   ordered paragraph/poetry/headings, all note bodies, callers, anchors
   and original cross-reference targets. Fail closed on unexpected or
   ambiguous cases. A parser should not guess merely from a regex.
4. **Stage 6 — test the exact compiled candidate visually.** Read
   representative **problematic** openings, including single/double/
   triple-level divisions, poetry, italic spans, note-heavy places,
   genuine text-critical/lexical marks, ordinary paragraphs and book/
   chapter boundaries. Use real stable independent SWORD/JSword readers
   such as Xiphos and AndBible. Verify the selected **module and passage
   visibly on screen**, not just navigation commands or image uniqueness;
   otherwise a stale screenshot can falsely pass. Bind evidence to the
   final ZIP checksum and actual SWORD module ID/version.
5. **Stage 7 — separate approval and public verification.** Do not
   equate a source repair, a passing synthetic test, a privately built
   module, a GitHub release or a deployed catalogue. Require owner
   approval, immutable original+old release, exact new ZIP hashes,
   independently downloaded public catalogue/module and preserved
   rollback. Document any limitations of GUI coverage.

## Reusable repository tools and current limits

- `scripts/inspect_paragraph_rendering.py` — read-only,
  source-pinned original-vs-real-native text/marker/whitespace **sample**
  diagnostic; it also reports source-wide leading-sign categories and
  paragraph opening shapes.
- `scripts/repair_osis_division_markers.py` — source-SHA-bound,
  byte-scoped prototype for **verified** one/two/three-star
  subject/stanza marks at recognized `p`/`l` openings. Guards
  lexical/text-critical signs and proves reversible milestone metadata.
  **Not** a general rule for other publishers, scripts or arbitrary
  symbols.
- `scripts/repair_osis_paragraph_indentation.py` — strict,
  source-SHA-bound cleanup limited to a newline + ASCII indentation
  immediately after a `p`-opening verse milestone. It verifies text,
  note identities and anchors; it must not be applied blindly to
  intentionally indented poetry or source-specific display conventions.
- Synthetic regressions:
  `tests/test_inspect_paragraph_rendering.py`,
  `tests/test_repair_osis_division_markers.py`,
  `tests/test_repair_osis_paragraph_indentation.py`.
- The Darby private full-corpus pipelines demonstrated the entire chain
  through actual CrossWire SWORD and JSword readers. Those **release
  workflows and receipt identities are Darby-specific**. There is **not
  yet a universal automatic paragraph-star/indent fixer or all-Bible
  source-to-native GUI release gate**. Extending the reusable diagnostics
  to general edition-parameterized preflight belongs to the existing
  [pipeline-generalization backlog #28](
  https://github.com/icfmp/Bible-Resources/issues/28).

If a published source/compiled module is already correct, **reuse it**.
Never apply an automatic visual cleanup merely to make all Bible editions
look alike. The objective is faithful, readable presentation of each
source's actual editorial conventions, with independently reproducible
evidence.
