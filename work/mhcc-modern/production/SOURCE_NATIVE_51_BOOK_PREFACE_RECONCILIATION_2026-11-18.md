# Modern MHCC — final first-K book preface reconciliation (2026-11-18)

## Final verified whole-canon result

**Two distinct final private reader candidates are now compiled and fully
tested**, rather than allowing unapproved corrections into the conservative
OSIS candidate:

| Candidate | Original/source-preserving and proposed hyperlinks in full OSIS | K-level links | First-K text and link parity |
| --- | ---: | ---: | --- |
| `MHCCPREFACES` — conservative 56-intro edition, 176 source-only provenance notes, no unapproved source-target repairs | **1,192** | **744** | **4,049 / 4,049 exact** |
| `MHCCPREFACEREPAIR` — separately labelled **UNAPPROVED** 56-intro review candidate with 13 additional independently witnessed proposed navigations for four defective original links | **1,205** | **757** | **4,049 / 4,049 exact** |

The **1,192 conservative links** comprise **1,015** original native source
links already represented in modern inline text/outline, **176** original
literal source-linked references separately stored as transparent provenance
notes, and **one** independently authenticated originally-unlinked authorial
citation. **Nine** source markup errors and **four** unsafe original link
destinations are intentionally excluded (the latter have a distinct 13-link
review-only alternative). The conservative preface module **does not
incorporate** these 13 unapproved editorial fixes.

[Independent native SWORD dual-variant gate #44338583819](
https://github.com/icfmp/Bible-Resources/actions/runs/44338583819)
**SUCCESS**: both variants built through `osis2mod`, then all
**4,049 / 4,049 original source-owned first-K modern text bodies and their
ordered embedded cross-reference target/label identities** matched the
respective prior linked version, with all **28,792** numbered SWORD keys
preserved. The 50 new introductions did not change existing commentary.
No compiled payload or unpublished authored prose was distributed.

**All 56/56 prepared modern book introductions have now been placed once
in a separate, still-unpublished private OSIS/SWORD candidate.** The pinned
original SWORD source, all 1,189 modern manuscripts and all previous
cross-references remain unchanged.

- **Five** introductions come from verified original chapter-I data.
- **One** first-K-origin introduction (Genesis) was already in the
  modern manuscript and was not duplicated.
- The remaining **50** first-K-origin introductions were added only as
  derivative `div type="introduction"` chapter-I readings. **47** have
  exact whole-word correspondence between the pinned original SWORD
  first-K text and the distinct original CCEL book preface. The remaining
  **three** have exactly one conventional biblical book-name abbreviation
  substituted, directly before a numerical chapter reference:
  `Jer` ↔ `Jr` in Jeremiah and Song of Solomon; `Mic` ↔ `Mi`
  in Micah. No actual prose or scriptural referent differs.
- These short abbreviations are independently documented in the
  [SWORD locales file](https://sources.debian.org/src/sword/1.7.3%2Bdfsg-2/locales.d/fr_abbrev.conf/)
  and other Bible book abbreviation lists. The generic gate accepts them
  **only for one otherwise-identical word stream with a uniquely verified
  original first-K SHA, a following numeric chapter, and a single
  unambiguous canonical book identity**. It rejects arbitrary changes.
- Original authorial K content was neither deleted nor moved. The
  preface's original K identity is recorded in each private receipt.

**Actual OSIS → SWORD → libSWORD validation:** [#44337517917](
https://github.com/icfmp/Bible-Resources/actions/runs/44337517917)
**SUCCESS**. It verified all **50** newly inserted introductions in
their compiled real chapter-I entries; the existing Genesis was not
duplicated. Crucially, independent full-SWORD comparison proved that **4,049 /
4,049 source-owned commentary K bodies have identical complete visible
Unicode text and identical original link-target/display ordering** in
both separately compiled variants: **744** K-level Scripture links in
the conservative candidate and **757** in the separately flagged 13-link
correction proposal candidate. All **28,792 SWORD indexed verse
addresses** are preserved. [General Validate
#44337517632](https://github.com/icfmp/Bible-Resources/actions/runs/44337517632)
and [tool registry #44337517743](
https://github.com/icfmp/Bible-Resources/actions/runs/44337517743)
also **SUCCESS** on that code head.

**Gate closed:** 51 unplaced introduction source-location cases; no
remaining modern-preface candidate is excluded for a source-location
or source-abbreviation issue. **Still pending:** final editorial
signoff, the separate 176 reference-note placement policy and four
unapproved source-link corrections, independent Xiphos/AndBible/Bible
reader compatibility, rights and owner-authorized publication. This
private technical preview **is not a publicly released or approved
modern MHCC edition**.

---

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

**Interim three-case lexical diagnostic (now resolved):** initially
`Jer.1`, `Mic.1` and `Song.1` failed literal whole-word identity.
Independent SHA-pinned comparison later proved they differ **only**
in one conventional book abbreviation before a chapter number:
`Jr`/`Jer` or `Mi`/`Mic`. The strict canonical reference-name
check now reconciles them without altering a single manuscript word.
See the final checkpoint above.

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

**Implemented and verified:** the accepted generic procedure now inserts
50 first-K-origin modern introductions (47 byte-identical witness word streams
and three authenticated source book-reference abbreviation variants); Genesis
and the five native-I introductions remain in place. **56/56** introductory
units are represented exactly once in the private OSIS candidate.
No introduced source label or modern book title is thereby approved for
public publication. Do not merge PR #272
or publish a module until later reader, rights and owner gates pass.

The source-only CI report
`mhcc-51-intro-native-vs-ccel-triage.json` provides one metadata-only
row per original first K and candidate, never copied authorial source prose.
