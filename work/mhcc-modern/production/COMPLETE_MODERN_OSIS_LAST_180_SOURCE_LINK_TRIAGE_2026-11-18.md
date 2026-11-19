# MHCC Modern English — exact source reference disposition and final 180-case queue

**2026-11-19 source-link triage update:** The most recent source-pinned private modules on [CI #44479185011](https://github.com/icfmp/Bible-Resources/actions/runs/44479185011) **SUCCESS** (Validate/registry green) have **156/176** previously unresolved original source links navigable (83 compact, 25 K-section headings, 5 partial verse ranges, 11 local verse tokens, 22 original outline digits, 10 in source-verified relocated book introductions), with **20 source notes** retained and **all 28,792 native K keys** intact. **The 20 now split into ten suspect native digital destinations, one printed-original Leviticus reference discrepancy, and nine valid source links whose citations are absent in modern prose.** Source-fidelity review found one substantive omitted original clause in Matthew 3:7–12 concerning the continuing graces and comforts of the Holy Spirit; do not hide this omission with unsafe automatic hyperlinks. [Detailed final triage](REMAINING_20_ORIGINAL_LINK_EDITORIAL_REVIEW_2026-11-19.md). Original source and modern accepted chapter manuscripts are unchanged. The new preface-linked candidate remains separate, private and unapproved.


## 2026-11-18 — source-native bulk reference restoration: 111/176 resolved

Latest real isolated whole-canon runs: [source SWORD / readback #44390972953](https://github.com/icfmp/Bible-Resources/actions/runs/44390972953) **SUCCESS**; [Validate #44390972988](https://github.com/icfmp/Bible-Resources/actions/runs/44390972988) **SUCCESS**; [tool registry #44390972806](https://github.com/icfmp/Bible-Resources/actions/runs/44390972806) **SUCCESS**.

**Original 1,204 source link disposition (no unapproved repairs):**

| Editorial disposition | Count |
| --- | ---: |
| Prior accepted original source links represented in modern OSIS | 1,015 |
| New links on unique, modern-printed biblical verse tokens | 81 |
| New exact original K-range links on matching modern editorial headings | 25 |
| New source-authenticated partial-range links on uniquely printed modern prose verse spans | 5 |
| **Total source links now directly navigable (excluding source notes)** | **1,126** |
| Original source-link occurrences still in K notes (some digital destinations suspect) | 65 |
| Documented spurious digital original link markers excluded | 9 |
| Four independently documented corrupt original targets withheld for review | 4 |
| **Original digital link occurrences all accounted for** | **1,204** |

The **81** modern-printed verse links and **five** partial-range links are actual in-prose hyperlinks. Their original literal source targets and source K/ordinal identities are authenticated against **MHCC 0.1.1**. The five new partial ranges are **Daniel 11:5–30, Ezekiel 1:4–14, Isaiah 10:28–34, Isaiah 12:4–6 and Isaiah 15:6–9**. Because the authored modern manuscript displays some numbers in bold, the implementation inserts the real original link on the exactly matching printed verse digits *within the existing OSIS emphasis node*, retaining all paragraph text, formatting, punctuation, and original K structure. Isaiah 12 and 15 each have a single underindexed original K body; these references are not fabricated additional commentary bodies or numbered K entries.

The **25** exact complete-K range links are carried on the matching modern **editorial section headings**: the target matches the original native SWORD K occupancy, but the editorial navigation location is **not claimed to be Henry's original inline anchor**.

Disposable private whole-canon **MHCCHEADINGS** compiled successfully and independent raw SWORD readback confirmed **30/30** new authenticated range references (25 headings + 5 in modern prose), **65/65** original source-note target/display identities and **28,792/28,792** numbered K keys. Real diatheke successfully displayed the commentary probe. Original MHCC 0.1.1, all 1,189 modern English manuscripts and previous conservative candidates are unchanged.

**Remaining editorial work:** 65 original digital link occurrences are still clearly identified as source-only notes because exact modern in-sentence placement is not proven; at least eight original digital hyperlink destinations are suspect and NOT editorially approved. Eight currently catalogued suspect original digital targets are in [the review-only error manifest](ADDITIONAL_ORIGINAL_LINK_TARGET_ERRATA_2026-11-18.json), and four earlier malformed source targets remain unapproved; none is silently corrected. Further source/editorial decisions, actual GUI reader compatibility, edition/redistribution rights, and independent approval remain explicit publication gates. **PR #272 stays draft; nothing has been merged or released.**


**2026-11-18 — complete private 1,189-chapter OSIS/SWORD transport verified; outstanding source-link treatment remains editorially constrained. No publication authorization.**

## This checkpoint

At [real source and private native SWORD CI #44307458450](https://github.com/icfmp/Bible-Resources/actions/runs/44307458450), the [Validate #44307458312](https://github.com/icfmp/Bible-Resources/actions/runs/44307458312) and [Tool registry #44307458489](https://github.com/icfmp/Bible-Resources/actions/runs/44307458489) workflows **all passed** for head `5e70b9760fd79a05221cdd22b845be9b4e8609c9`.

The latest source-verified output contains **1,016 actual inline Bible reference elements** in complete private modern OSIS / derived SWORD. The private original-SWORD source receipts attest **1,015 represented original linked occurrences out of exactly 1,204** (**84.3%**), plus the separately source-witnessed Revelation 22:2 citation that is not a linked element in the published MHCC original.

Two additional, tightly validated singleton occurrences were found when an abbreviated original visible Scripture label was present **once, verbatim** in the same source-owned modern exposition. Each requires:
- the **full original source K body SHA-256**, original exact 1-based linked-element ordinal and source literal `osisRef`/visible-label SHA-256 to match the pinned real SWORD stream;
- a canonical same-book/same-chapter/same-verse target;
- a unique, literal modern paragraph occurrence of the exact original printed label, with no other source link sharing that label in its K body;
- no documented original target correction, spurious source link, range inference, modern text change or rewriting.

The full 1,016 derived links, their displayed labels and exact literal targets were read back from a **real compiled private SWORD module**, along with **28,792/28,792 numbered SWORD addresses** (28,742 authentic original numbered K keys + 50 explicit two-chapter I-only transport aliases). The modern prose roundtrip check has **4,038/4,049 first-K groups with exact visible-text equality**; the remaining **11** contain the full authored visible text continuously within a SWORD wrapper (no missing or changed authored body), separately reported and not equated with original native editorial-layout parity.

The preceding **448** source-attested original first-K chapter-outline links remain attached to **180 modern original-outline chapter-I tables**; no source or modern prose is silently altered. This **does not certify** that all readers render those chapter-I links identically.

## A complete 1,204-item source hyperlink disposition ledger

The existing `scripts/commentary_modern_reference_gate.py` now produces a **metadata-only, SHA-256-identified individual follow-up queue**, as the `source_original_link_review_ledger` key in CI artifact `mhcc-modern-complete-bounded-linked-osis-structure.json`. The queue is **regenerated from the immutable published original SWORD**, not manually invented.

| Actual source XML link disposition | Count |
| --- | ---: |
| Original linked elements represented, copied or source-witness-corrected in the derived OSIS | **1,015** |
| Original source hyperlinks to prose list numbers, separately authenticated and deliberately not copied | **9** |
| **Original source-linked elements requiring targeted follow-up** | **180** |
| **Total source linked elements (exact)** | **1,204** |

The **180** unresolved occurrences are **145 singleton verse links**, **32 authentic same-chapter verse-range links**, and **3 composite or non-standard OSIS target forms**. Each unresolved item records the original `first_key`, authentic 1-based original reference ordinal, SHA-256 of the original literal target and visible label, and an explicit pending-status classification. **No original reference labels, original literal targets or commentary prose are exported** in this queue. The nine deliberately omitted native hyperlinks are separately enumerated with their original K/ordinal and independent correction disposition.

### What can be concluded

- The existing two-phase **modernize, then verify** manuscript workflow has been performed on all 1,189 chapters. **Do not undertake another full editorial rewriting pass merely because 180 original link placements remain**.
- A missing modern XML link is **not proof that the modern prose is incomplete**. An original citation can have changed presentation during modernization; the exact source K group/ordinal must be examined before restoring or omitting a link.
- The **3 non-standard target forms** must be examined against their exact native source markup before extending the general OSIS grammar recognizer. The **32 ranges** require explicit verse-boundary and source/modern placement evidence. The **145 singletons** merit targeted correspondence checks, not blind link creation.
- All modern OSIS/derived SWORD packages remain **private, reproducible technical candidates**; no original SWORD package is modified or public derivative released. Additional open blocks include **51 quarantined book-introduction candidates**, reader-specific rendering checks for modern chapter-I links, verified rights, and explicit publisher/owner approval.

**Next work:** use the small 180-case K/ordinal ledger as the only outstanding original-link review scope, resolve evident source-ledger cases in bounded, testable groups, preserve original literal `osisRef` where valid, and rerun original-source SHA + 28,792-key full native SWORD + all visible label/target checks after each batch. Keep [draft PR #272](https://github.com/icfmp/Bible-Resources/pull/272) and [issue #270](https://github.com/icfmp/Bible-Resources/issues/270) open.

## Exact original-context review of all 180 pending links — 2026-11-18

A bounded private K/ordinal diagnostic now supplements the existing disposition
ledger without modifying translated commentary or placing additional links.
The original published SHA-pinned SWORD module was re-read and compared with
every source-owned modern K group. The [source + complete derived native SWORD
run #44315771975](https://github.com/icfmp/Bible-Resources/actions/runs/44315771975),
[Validate #44315771916](https://github.com/icfmp/Bible-Resources/actions/runs/44315771916),
and [tool registry #44315772097](https://github.com/icfmp/Bible-Resources/actions/runs/44315772097)
all **passed** on code head `fc7bf79c32fdbe4c8eec472ab7b9c7e0f1c8841e`.

| Source-verified diagnostic (pending links only) | Count |
| --- | ---: |
| Original source links outside both titles and tables | **180** |
| Recognized single-verse canonical source targets | **145** |
| Recognized full same-book, same-chapter verse ranges | **32** |
| Other full OSIS two-endpoint ranges requiring special source-scope review | **3** |
| Original printed labels absent verbatim from corresponding modern K paragraphs | **114** |
| Too short or non-distinctive original printed labels to compare safely | **65** |
| Unique verbatim original printed label found in modern source-owned K | **1** |

The sole pending **verbatim unique** printed-label correspondence belongs to
original source `Eccl.10.11`, original reference ordinal **1**. The existing
[Ecclesiastes 10 modern manuscript](accepted/ecclesiastes-10.md) already
documents a primary-biblical-citation concern in that exact subsection;
therefore **unique text presence is not sufficient to approve its linked
destination**. Do not insert a hyperlink until its original source target,
biblical verse and any intended authorial erratum are independently assessed.
Its original target identity hash is
`8c30222385edb1d5e6b2a404e4532f6d1734d65bd6a45625ae9ebbfb02921fef`.

The three **non-standard full-endpoint original range** link identities are:
- `Jer.50.1`, original ordinal **1**: target SHA-256
  `70e54e46af7bf90a9c58a1a17cfb3cff04ba80a6fe7f608eb199361404f2b6df`.
- `Jer.50.1`, original ordinal **2**: target SHA-256
  `f6b8ecb3d15ba597fc3b17911c3a5807b2188ba12d9195623e989c57eb4f2ec5`.
- `Matt.23.1`, original ordinal **1**: target SHA-256
  `86fe8cf0c4b5b95e324c3ac6cd3b3ee84744a96eb7ae2870fba23b0a6327218a`.

All three are outside original title/table markup, their original printed
labels are absent verbatim from the corresponding modern K paragraphs, and
their full-range syntax did **not** pass the deliberately restricted same-chapter
range matcher. This establishes the **exact original elements to review**, not
safe link targets or a reason to broaden the parser globally. Their actual
OSIS grammar/verse boundaries, section ownership, translated presentation and
reader behavior require an independently verified original-native inspection.

All **1,204** original source-link dispositions remain accounted for:
**1,015 represented**, **9 authenticated spurious enumerator links omitted**,
and **180** pending review; the derivative still contains **1,016** link
elements including the separately attested originally unlinked citation.
No original prose, source label or literal original `osisRef` was exported in
the metadata log or receipt. No extra source link was approved, and
**no merge, rights clearance or publication** has been authorized.


## Major source-reference preservation batch — 2026-11-18

**Verified in one full-canon private build, not merely planned.** After the
original K/ordinal + literal source target/label SHA receipts had already passed,
we generated a *second*, unpublished complete OSIS/SWORD candidate. The base
linked modern commentary is not modified: its **1,016** original-inline-or-witness
links remain exactly as before. The separate candidate adds plainly marked
`note type="crossReference"` annotations with
`resp="BibleResourcesPrivateSourceOnlyLinkSupplement"` inside the corresponding
source-owned K commentary groups.

| Original native hyperlink disposition in the source-note alternative | Occurrences |
| --- | ---: |
| Source-linked references already present in modern inline text / original chapter-outline links | **1,015** |
| **Previously unplaced original links now separately preserved as source-only notes** | **176** |
| Original hyperlinks to prose enumerators, independently disproved and excluded | **9** |
| Original defective/unsafe targets blocked with exact native K/ordinal SHA evidence | **4** |
| **Original whole-canon SWORD linked elements** | **1,204** |

The separate notes preserve **the original literal `osisRef` unchanged**, not
a guessed destination. Their **visible note label is a normalized derived
English reference**, rather than the original source's potentially non-standalone
label (e.g. bare numeric continuation). The original printed link-label SHA-256
is still authenticated privately and remains in the source receipt. Each note
explicitly says that its linked references are *original-edition links not
placed in modern wording*. This is source provenance attached to the correct
source-owned K scope, **not a claim that the 176 hyperlinks have been restored
at their original prose positions or independently deemed semantically
accurate**. The four [proposed legacy source link errata](FOUR_NATIVE_LINK_ERRATA_REVIEW_2026-11-18.json)
remain excluded from the notes pending a separately justified correction.

### Real SWORD verification

All three workflows passed for code head `1de2896416906f0c0eede7d41f16b9125cba4ae4`:
- [Full native source / modern OSIS / private SWORD #44322196017](https://github.com/icfmp/Bible-Resources/actions/runs/44322196017):
  **102** source-owned K groups containing **176** supplemental original target
  references; exact source literal target SHA-256 **and** normalized derived
  visible-label SHA-256 verified after real `osis2mod` plus libSWORD raw readback.
  All **28,792** expected numbered SWORD addresses intact.
- [Validate #44322195862](https://github.com/icfmp/Bible-Resources/actions/runs/44322195862):
  **SUCCESS**, including synthetic fail-closed source-note/errata tests.
- [Tool registry #44322196089](https://github.com/icfmp/Bible-Resources/actions/runs/44322196089):
  **SUCCESS**, with exact script SHA-256 inventory.

The **original source and the modern manuscript prose are unchanged**, the base
1,016 inline links remain unchanged, and the second candidate is disposable CI
work product only. No source annotation text/labels were uploaded as a public
CI artifact. The reproducible generic source-note supplement and tests live
in the existing `scripts/commentary_modern_reference_gate.py`, its tests,
and `.github/workflows/commentary-modern-source-receipt.yml`.

**Next:** independently review the four demonstrably malformed or mismatched
original targets, including the two composite Jeremiah 50 verse spans,
Matthew 23's multipart Pentateuch references, and Ecclesiastes 10's wrong
Isaiah chapter. Source notes are a transparent preservation fallback; they do
not replace a safe editorial judgment about each modern inline placement.
Additionally verify Xiphos/AndBible/Bible reader display, quarantined book
introductions, and rights before any public derivative. **The baseline
editorial inline-placement queue is still 180; the number of original hyperlinks
missing from the *separate source-notes candidate* is now four, not 180.**
No premature issue close, no PR merge or publication.

## Source-witnessed proposed navigation for the final four defective original links

**Verified 2026-11-18; not editorially approved and not published.** The two
Jeremiah 50 original hyperlinks use malformed OSIS cross-chapter targets for
multiple discontinuous chapter-50 spans; Matthew 23's original hyperlink
similarly misencodes the four distinct Pentateuch passages; Ecclesiastes
10's old digital witness points the highway allusion to the wrong Isaiah
chapter. A [source-hash-pinned, reversible proposal manifest](FOUR_NATIVE_LINK_ERRATA_REVIEW_2026-11-18.json)
now stores the original literal target identity **and** the candidate
citation spans. The independent corroborating textual edition includes
[Matthew Henry's concise exposition of Matthew 23](https://ccel.org/ccel/henry/mhcc.xxxii.xxiii.html)
and the concise Jeremiah 50 outline. This is an editorial proposal, not an
assertion that the original digital source's corruption cause has been traced.

| Original K / original linked ordinal | Proposed navigable destinations in a *third* unapproved private candidate | Count |
| --- | --- | ---: |
| `Eccl.10.11` / 1 | `Isa.35.8` | 1 |
| `Jer.50.1` / 1 | `Jer.50.1–3`; `Jer.50.8–16`; `Jer.50.21–32`; `Jer.50.35–46` | 4 |
| `Jer.50.1` / 2 | `Jer.50.4–7`; `Jer.50.17–20`; `Jer.50.33`; `Jer.50.34` | 4 |
| `Matt.23.1` / 1 | `Exod.13.2–10`; `Exod.13.11–16`; `Deut.6.4–9`; `Deut.11.13–21` | 4 |
| **All original defective link occurrences** | **13 candidate navigable OSIS destinations** | **13** |

This third candidate is built from the second **176-original-link note**
candidate: the modern source text, its 1,016 existing inline links, and all
176 exact source-only note references remain unchanged. The four repairs are
represented by additional `note type="crossReference"` blocks tagged
`resp="BibleResourcesPrivateUnapprovedOriginalErrataPreview"`, explicitly
distinguished from the authorial original linked labels. The notes mark
*proposed* navigations, not links transferred from the original source.
There is no global parser normalization, source alteration, silent editorial
rewriting, or final inline hyperlink placement approval.

[Full real source + proposed repairs SWORD #44324164040](https://github.com/icfmp/Bible-Resources/actions/runs/44324164040):
**SUCCESS**. Original SHA/K/ordinal link identity checks passed; the
third private candidate compiled and exact native readback verified **13**
candidate destinations across the four known original link occurrences,
all **176** unchanged source-only notes, and **28,792/28,792** exact native
numbered SWORD addresses. [Validate #44324164508](https://github.com/icfmp/Bible-Resources/actions/runs/44324164508)
and [registry #44324164106](https://github.com/icfmp/Bible-Resources/actions/runs/44324164106)
**SUCCESS**. Proposed-repair output is disposable private CI work only,
not a published SWORD package, new accepted text, or approved OSIS edition.

**Operational checkpoint:** original source reference *provenance* is now
either inline (1,015 original source links), source-only in a private
alternative (176), explicitly excluded as spurious (9), or covered by
four privately demonstrated one-to-many/single corrected navigation
**proposals** (4). Original source elements remain **1,204**. The baseline
modern inline review ledger still identifies **180** cases without inline
authorial placement; no count is cosmetically decremented. The source
errors' four independent editorial decisions, reader behavior of the
note variants, 51 quarantined preface candidates, rights, and publication
approval are **still outstanding**.


### Real command-line reader note-visibility evidence

In addition to raw libSWORD attribute/target readback, [CI #44325214135](https://github.com/icfmp/Bible-Resources/actions/runs/44325214135)
compiled all three private candidates and queried actual `diatheke`
with Scripture cross-references and footnotes enabled (`-o fx -f OSIS`).
The implementation checked only metadata booleans and rendered length:
a representative K from the **176 source notes** rendered the explicit
original-source-notes marker; a separate **Jeremiah 50** probe rendered the
unapproved-repair marker. Both probes returned nonempty commentary, and
both markers were **present** in the actual reader output.

This is confirmed visibility in one command-line SWORD frontend for
representative cases, **not blanket Xiphos, AndBible or Bible application
reader acceptance** and not editorial signoff. The note text itself was
not exported into public workflow logs.

## Source-authenticated contextual relocation experiment — 2026-11-18

At [real full-canon CI #44347371308](https://github.com/icfmp/Bible-Resources/actions/runs/44347371308) (**SUCCESS**; Validate and tool registry also green), the separate private reference-context edition was compiled and independently read back through actual SWORD. Original SHA-pinned native K raw bodies were inspected in private to obtain 180-character text neighborhoods before/after each source link. Two strictly conservative context finders were applied only to the **176 legitimate source-only reference notes** (not the four wrong-target links):

1. A unique distinctive **5–8-word exact adjoining phrase** in the modern source-owned exposition: **0** safe relocations.
2. A unique, strongly supported **paragraph-level lexical correspondence** between the original near-link context and modern prose (at least six uncommon shared terms and 64% coverage of at least seven source terms, without competing paragraph): **1** tentative paragraph-local source-only note, **not** an authorial inline hyperlink or evidence of exact original link placement.

**Result: 1 / 176 provisionally grouped with a matching modern paragraph; 175 / 176 remain in original K-section source-only notes.** The newly associated link is retained as a visibly marked *source-provenance note*, not silently attached to a word. Private receipt records its source K, ordinal, original literal-target SHA and label SHA and match class (no source prose exported).

The additional private SWORD `MHCCCONTEXT` roundtrip verified **all 176/176** original literal source link target and display identities, plus **28,792/28,792** native numbered K keys; the underlying 1,189 modern chapter manuscripts, original 0.1.1 SWORD, conservative 176-note candidate and separate four-errata proposal edition remain unchanged. The four defective links are never eligible for context relocation. Four synthetic regression tests plus two lexical-specific tests cover duplicate target protection, source errata exclusion, ambiguity and modern prose nonmutation.

**Important limitation:** because the modernization substantially rephrased the historical English source, literal/fuzzy word-based automatic correspondence is *not* adequate for most of the 176 source references. The remaining work is **individual original-source to modern-translation semantic alignment, including the source-reference location in its sentence**, with reviewed exact inline anchor decisions where justified. No automatic nearest-text anchoring should be represented as authorial inline fidelity. No release, approval, or PR merge.

