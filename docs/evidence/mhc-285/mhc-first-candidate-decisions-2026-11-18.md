# MHC 2.2 — first private candidate: decisions, not another research loop

**Checkpoint:** 2026-11-18, [import #285](https://github.com/icfmp/Bible-Resources/issues/285), [draft PR #286](https://github.com/icfmp/Bible-Resources/pull/286).
**Audience:** technical/editorial release review. **No corrected source/module is published or approved by this document.**

## Edition choice and meaning of completeness

The first candidate is **faithful to the specific CrossWire MHC 2.2 authoring OSIS**, SHA-256
`3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`,
not a conjectural harmonization of every digital Matthew Henry transcription.
The separately pinned six-volume **CCEL** text is an editorial comparison
witness, **not** permission to add its words to a CrossWire derivative or
claim that CrossWire is identical to a particular historical printed edition.

That scope makes the 569 extra nonlinked CCEL Psalm 7 words, 235 CCEL
Acts 17 words, and independently observed Psalm 8 edition variants
**documented edition differences for targeted follow-up**, not automatic
proof that the CrossWire-derived first candidate has lost authored source
material. Do not import them or silently rewrite CrossWire's text.

## Exact source transformations in the private candidate

| Candidate decision | Scope | Technical verification | Editorial status |
| --- | --- | --- | --- |
| Keep exact pinned authoring source, all 4,256 distinct commentary bodies | 7,073,234 source word tokens | Full source-group→native verification and same 31,098 K / 1,255 I / 2 TOP occupied records | Faithful edition baseline |
| Remove 11 **empty** source superscript leaves | Zero authored words; original byte spans locally guarded | Full text hash and independent recompiled native comparison | Mechanical-only; reversible |
| Repair 3 source OSIS verse-range endpoints | 17 out-of-KJV machine addresses, no invented verses | Real KJV native registry and paired source milestones | Source-address-only research preview; exact old/new values retained |
| Shorten 6 **earlier** OSIS machine ranges at shared boundary verses | Exactly 24 existing milestone attributes; 14/14 distinct group bodies recovered | Complete word sequences and 70/70 independent source snippets confirmed in related native keys | **Release decision still required**: narrows earlier group's machine scope by one boundary verse, preserves every word |
| Preserve two original 2 Chronicles 1:1-covering divisions | Both `2Chr.1.1` and `2Chr.1.1-12` are genuine source blocks | Both complete source word streams located in compiled native K readback | **Do not delete or silently merge prose**; exact visual/section separation not proven |
| Correct all 25 anomalous inline machine Scripture targets | Original visible labels and exposition unchanged | 25/25 source SHA/line/label-attested, actual rebuilt 197 affected native K/I frames, no other XML/text modifications | Private reversible technical acceptance; user-visible link click still independent |

**Important:** the 2 Chronicles 1:1 source overlap is not an authorial-text
omission. Both prose bodies are present in the compiled result. The
independent complete commentary witnesses present chapter introductory
prose followed by the 1–12 exposition; they do **not** justify deleting the
separate source block or assigning its words to an invented numbered verse:
- [CCEL / independent Matthew Henry text: 2 Chronicles 1](https://www.christianstudy.com/data/sermons/matthewhenry/2chronicles1.htm).
- [BibleGateway full commentary: chapter introduction](https://www.biblegateway.com/resources/matthew-henry/2Chr.1.1-2Chr.1.17) and [verses 1–12](https://www.biblegateway.com/resources/matthew-henry/2Chr.1.1-2Chr.1.12).
- [Original source-overlap experiment and complete body preservation](../../../sources/cleaned/mhc/CLEANUP_STATUS.md).

This is a **reader/section-presentation** acceptance question, not a
reason to invent a textual correction. If a reader cannot display distinct
source sections, record that exact limitation against the application.

## Reader proof and deliberate stop condition

[Full private corrected-SWORD + real Xiphos experiment #44319850822](https://github.com/icfmp/Bible-Resources/actions/runs/44319850822):
- All 25 corrected source targets and all 32,355 native entries verified.
- Xiphos displayed **3/3** independently verified substantive commentary entries.
- Real GUI copied rich HTML containing **all 9/9** components of the
  Proverbs 31 compound citation and **all 3/3** components of the Isaiah 63
  citation including the Psalm 60 **chapter root**. The whole, unbroken
  original string did not match one source href; this is not evidence of
  missing component destinations.
- Matthew 28 was verified as visible commentary text; no rich-HTML clipboard
  capture. Actual clicked hyperlinks and the precise Psalm 60 superscription
  landing were **not tested**.

**Stop repeatedly invoking Xiphos on every source commit.** Its optional
real GUI steps are explicitly manual-only (workflow_dispatch) as of
[`c39c8b7`](https://github.com/icfmp/Bible-Resources/commit/c39c8b7508de091442c7939dc573a7061ddce54e).
The source/OSIS/native integrity tests remain mandatory on relevant PR
changes. Do not continue micro-tuning the headless GUI harness unless an
actual source edit or new reader defect justifies it.

## Remaining *decision* gates (not more broad research by default)

1. **Editorial accept / revise:** machine scopes of the six shared boundary
   verses, and explicit handling of two distinct authored 2Chr 1:1 sections
   in the reader. A published version must state its addressing policy.
2. **Legal/source accept / reject:** CrossWire's **MHC 2.2** public-domain
   distribution claim, contribution/provenance context and any actual
   derivative digital/editorial restrictions. The six CCEL volumes are not
   part of the candidate.
3. **Reader release acceptance:** real clicked-link routing/preview (especially
   Psalm 60 superscription), introductions, long sections and notes, plus
   Android AndBible GUI if supported. Existing diatheke, pinned JSword engine
   and partial Xiphos checks are not that final signoff.
4. **Release approval:** build a deterministic standard SWORD package from
   the approved candidate, independently verify ZIP/catalogue, then ask the
   owner before any published release or merge.

**Current status: technically evidenced first private candidate, not an
approved edition or published package.** Do not restart first-phase source
intake, do not transplant CCEL material to force artificial full-source
parity, and do not commission repeated generic Xiphos GUI tuning.
