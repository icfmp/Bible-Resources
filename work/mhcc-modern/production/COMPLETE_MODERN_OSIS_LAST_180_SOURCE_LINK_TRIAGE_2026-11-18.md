# MHCC Modern English — exact source reference disposition and final 180-case queue

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
