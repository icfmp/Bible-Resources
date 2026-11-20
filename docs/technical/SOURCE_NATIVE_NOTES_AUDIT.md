# Private original-USFX → native SWORD note-body diagnostic

Issue [#28](https://github.com/icfmp/Bible-Resources/issues/28), after the
independent indexed-main-text proof in PR #50 and authorial milestone/speaker
fixes in #51 and complete source-only group witness in #52.

The new `scripts/source_native_notes_audit.py` independently inventories
authored USFX note-bearing **numbered verses** in the explicitly reviewed
source-to-SWORD book crosswalk. It collects original `f`, `fe`, `x`,
`ef`, `ex` and `note` body text only in **private Python memory**.
It separately counts notes outside numbered verses and records excluded
editorial heading containers. Source notes in non-mapped original books
remain out of scope. It rejects ambiguous source note/verse nesting,
duplicate native keys, oversized content, DTDs and unsafe XML.

During the existing private stock-SWORD full-corpus scan,
`source_native_maintext_probe.py` passes every actually indexed native
verse's **raw bytes** to a strict, non-recovering XML note reader. It
distinguishes:

- Both source and native numbered verses without notes.
- Note-count mismatch (including source-only/native-only notes).
- Same ordered note bodies with exactly equal semantic Unicode characters.
- Same ordered note bodies after Unicode NFC/whitespace folding.
- Different ordered note bodies.
- Native raw fragments that cannot be independently parsed as complete
  XML: **unknown**, never interpreted as having zero notes.
- Original source note-bearing verse IDs with no independent native
  indexed slot.

The JSON report contains **counts, reference IDs and classifications only**.
No footnote text, source XML, native XML, or text hashes are included in
public logs or artifacts. The original archives and actual compiled
SWORD payload and inspector binaries are already SHA-bound in the parent
read-only audit. Both RawText and zText use the same generic diagnostic.

## Important editorial limitations

This first note lane **does not** prove that authorial `f`/cross-reference
`x` maps to the correct native note *type*, or that note callers,
anchors, exact within-verse positions, cross-reference targets, nested
note markup, or translation-note conventions survived conversion. Even
exactly matching body strings are not proof of these properties. Source
USFX `fr` reference labels may be embedded inside the original note
body but represented differently in OSIS; this is a diagnostic
difference, **not** automatic evidence of deleted text.

A source-only verse can have notes absorbed into a preceding SWORD
entry; this stage **does not** reassign those notes, and does not claim
source versification is preserved. Unparseable native fragments and
unmapped authorial books remain explicit. No note text is silently
normalized, removed or added to the source or published module.

A green CI job proves the diagnostic executed with correct provenance
and conservative flags; it is not an editorial sign-off or publication
gate. Follow-up work must separately audit note type/caller/anchor,
explicit reference targets, original verse position and ordered
paragraph/poetry/quotation structure. The published LSG 0.1.0 release
remains untouched.

## Initial pinned WEBP source/reader diagnostic (not editorial clearance)

The original SHA-pinned WEBP USFX and independently released zText reader
showed **1,568 authored notes** in mapped numbered source verses and
**1,571 notes** in parseable occupied native numbered entries. Among the
31,100 occupied native verse entries, 1,403 note-bearing entries had the
same ordered note-body text after Unicode/whitespace folding, four had
note-count mismatches, four had differing ordered note bodies, six raw
fragments could not be parsed strictly, and one authored note-bearing
verse had no independently addressable native key. The diagnostic is
conservative: these totals **do not** mean three authorial notes were
inserted or deleted; source-only verse-group storage, title/intro
storage, XML fragment validity and note caller/reference conventions
must be examined before editorial conclusions.

The bounded report deliberately prioritizes count/content mismatches
and unparseable fragments over routine whitespace-only differences,
without revealing the underlying note text.

## Read-only note annotation metadata lane

The same USFX source walk can optionally capture *private* note annotation
metadata in original order, separately from its text: source marker type
(`f`/`fe`/`ef` versus `x`/`ex`), `caller`, and explicit
machine-readable `ref[@tgt]` values. The native stock-SWORD raw reader
captures `note[@type]`, `note[@n]` and nested
`reference[@osisRef]` attributes. Native `reference[@type=annotateRef]`
labels indicate a note's annotation source, **not a target cross-reference**
and are excluded from the explicit-target lane.

When both sides have the same number of notes for a canonical numbered key,
the diagnostic independently classifies:

- Whether the source's dedicated cross-reference note class agrees with
  native OSIS `type="crossReference"`.
- Whether a *literal* source caller equals the native `n` string.
  USFM/USFX `caller="+"` or `"-"` (automatic or no marker) and absent
  callers are **not** treated as literal labels to compare.
- Whether ordered, explicitly machine-readable target **raw strings**
  match or are absent on either side. A matching raw attribute string is
  *not* proof of a resolved canonical target.
- Note-count mismatches: **no positional note pairing is asserted**.
  Fragments that cannot be parsed remain unknown.

Original note body text, caller strings and machine-readable reference
values are kept private. Public outputs include only classification counts
and a bounded selection of affected canonical source/native **verse IDs**.
If a source note has only a textual cross-reference label (`xt`, `xo`,
etc.) without a target attribute, the target is **not** inferred from
language-dependent prose. No source note is silently relabelled.

This lane deliberately **does not** certify note attribute equivalence,
source-to-native caller correspondence, anchor position within the verse,
resolved cross-reference navigation, preservation of original note styles,
or notes absorbed into reader-unaddressable source-only verses. It remains
an evidence-producing research check, not an automatic publication gate.
