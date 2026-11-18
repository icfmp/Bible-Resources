# Modern MHCC — final first-K book preface reconciliation (2026-11-18)

## Source inventory, not inferred from CCEL chapter order

The exact published MHCC 0.1.1 libSWORD source remains immutable
(corpus SHA-256 `2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e`).
Independent CCEL XML witness SHA-256:
`4a5509ba5064b54572397ae1a796561ff6ce4a1e18f366af0141a09c5d06fcd6`.
The CI compares the actual CCEL **direct book-preface** prose preceding the
first chapter to the *raw, first numbered original K body* after authenticating
the complete original SWORD corpus, each K SHA and original book identity.

The original modern editorial inventory contains **56** distinct prepared
book-preface manuscripts:
- **5** with an independently source-authenticated native **chapter-I** location
  (2 John, 3 John, Jude, Obadiah, Philemon), already integrated once.
- **51** that do **not** belong to a native nonempty I entry, but whose
  authorial preface **is present in the first numbered source K**.
  These are not missing CCEL-only supplemental introductions.

Real [CI #44328413437](https://github.com/icfmp/Bible-Resources/actions/runs/44328413437)
verified the original I/K inventory and found **41** direct authenticated
CCEL book `div1` first-K word-sequence matches, with **10** ambiguous
original CCEL book-code/heading cases. A conservative *exact unique 20-word
first-K lexical anchor across all source book divisions* resolved the latter
ten without guessing a Scripture book code, in [CI #44328956757](
https://github.com/icfmp/Bible-Resources/actions/runs/44328956757).
The expanded full-word-stream check in [CI #44329637601](
https://github.com/icfmp/Bible-Resources/actions/runs/44329637601)
confirmed **48 / 51 entire direct-book preface word sequences** are
contiguous in the correct original numbered K body.

The **three genuine source-witness text-sequence differences** are:
`Jer.1`, `Mic.1`, and `Song.1`. Their opening authorial prefix is
authenticated against the exact original raw K, but the entire CCEL
word stream cannot yet be equated with the original; do not silently
borrow the independently edited CCEL passage for these three.

## Concrete technical disposition

The existing 1,189 modern manuscripts, 4,049 commentary K groups,
1,016 modern in-text/outline links, 176 explicitly marked original source
reference-note links and 13 *unapproved* proposed repaired reference destinations
must remain untouched.

A new generic, fail-closed `overlay_native_first_K_book_prefaces` only
adds standalone modern `div type="introduction"` for originals with a
**complete, exact CCEL direct-book preface word sequence also present in the
pinned original first-K**. It records the original first K SHA and marks the
relocation as a modern edition decision, never a source I entry. Source K
commentary is not duplicated or overwritten.

**Expected private technical outcome (subject to actual CI validation):**
47 previously absent first-K-derived modern introductions added to chapter 1,
Genesis first-K preface already present and retained only once,
3 mismatched source-witness cases excluded pending targeted review, and
5 actual chapter-I introductions already present. This is **53/56** existing
modern book-preface manuscripts represented in the private OSIS candidate
if all the new tests pass.

The remaining three belong to the exact literary-source collation queue,
not a further corpus-wide retranslation. No introduced source-label or
title is editorially approved for public publication. Do not merge PR #272
or publish a module until later reader, rights and owner gates pass.

The source-only CI report
`mhcc-51-intro-native-vs-ccel-triage.json` provides one metadata-only
row per original first K and candidate, never copied authorial source prose.
