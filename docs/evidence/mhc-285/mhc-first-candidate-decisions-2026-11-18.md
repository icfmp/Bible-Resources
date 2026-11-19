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
| Shorten 6 **earlier** OSIS machine ranges at shared boundary verses | Exactly 24 existing milestone attributes; 14/14 distinct group bodies recovered | Complete word sequences and 70/70 independent source snippets confirmed in related native keys | **Approved for whole-verse navigation only**: the first Romans 4 section stops at 4:16 and the second starts at 4:17. Both full source bodies remain; this is not release authorization |
| Reclassify the original 2 Chronicles 1 preface as a genuine chapter introduction | Remove only the misleading preface verse milestones, move existing OSIS `div type="introduction"` boundaries; retain the original separate 1:1–12 exposition | [Real private SWORD compile/readback #44346559230](https://github.com/icfmp/Bible-Resources/actions/runs/44346559230) **PASS** (introduction in `2Chr.1.0`, source prose intact, no unexpected other-book changes) | **Approved for structural navigation only**; GUI rendering still needs review |
| Correct all 25 anomalous inline machine Scripture targets | Original visible labels and exposition unchanged | 25/25 source SHA/line/label-attested, actual rebuilt 197 affected native K/I frames, no other XML/text modifications | Private reversible technical acceptance; user-visible link click still independent |

**2 Chronicles 1 is no longer an unresolved source-index collision.** The
original authoring file separates the first preface and the 1:1–12 exposition.
The reviewed [private chapter-introduction plan](../../../config/commentary-osis-repair-plans/mhc-chapter-introduction-private.json)
moves the *existing* OSIS introduction boundaries to enclose all preface
paragraphs and removes the misleading standalone `2Chr.1.1` milestone pair.
The full separate 1:1–12 verse exposition remains in place. This does not
invent a verse zero; `2Chr.1.0` is SWORD's existing chapter-introduction
navigation key.

The source-SHA-gated transformation preserves the entire original visible
Unicode text stream, punctuation, whitespace, note text, titles and citation
markup. The full [private build and native readback #44346559230](https://github.com/icfmp/Bible-Resources/actions/runs/44346559230)
passed the independent chapter-introduction and separate-exposition checks.
The source, corrected candidate and compiled zCom4 are not committed or
released. A real GUI still needs to prove that the newly indexed introduction
is presented separately and legibly. This treatment follows CrossWire's
[documented osis2mod chapter introduction semantics](https://wiki.crosswire.org/Osis2mod).

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

**Stop repeatedly invoking Xiphos on every source commit.** Optional corrected-candidate
GUI steps use `workflow_dispatch`; source/OSIS/native integrity remains mandatory.
At the latest tested PR head, [the source-first private build #44346559230](https://github.com/icfmp/Bible-Resources/actions/runs/44346559230)
passed including the chapter-introduction readback, while the separate
[original-alias Xiphos run #44346559060](https://github.com/icfmp/Bible-Resources/actions/runs/44346559060)
failed at dependency installation *before* any reader probe. This is an
infrastructure failure, **not** a negative judgment on the corrected source
and **not** a GUI pass. Do not continue micro-tuning the headless GUI harness
without an actual source edit or new reader-acceptance need.

## Independent editorial boundaries for the six overlapping source ranges

The [Bible Gateway *complete Matthew Henry* edition indexes](https://www.biblegateway.com/resources/matthew-henry/Romans),
read independently of the CrossWire OSIS and its existing six-range trial,
**confirm the same proposed nonoverlap boundary for five of the six
pairs**. The Romans 4 division is a deliberate **intra-verse 17a/17b**
split, which cannot be fully represented by simply assigning a single
whole-verse SWORD key to one of the two source groups.

| Original CrossWire earlier/next source ranges | Independently published Henry section boundary | Assessment of the private earlier-end trim |
| --- | --- | --- |
| `Ps.95.1-7` / `Ps.95.7-11` | **1–6 / 7–11** ([full chapter](https://www.biblegateway.com/resources/matthew-henry/Ps.95.1-Ps.95.11)) | **Matches** authored whole-verse scope |
| `Rom.4.9-17` / `Rom.4.17-22` | **9–17a / 17b–22** ([Romans index](https://www.biblegateway.com/resources/matthew-henry/Romans)) | **Exception:** trimmed **9–16 / 17–22** preserves every word but no longer associates first body's **17a** exposition with verse 17 |
| `Rom.7.7-14` / `Rom.7.14-25` | **7–13 / 14–25** ([Romans index](https://www.biblegateway.com/resources/matthew-henry/Romans)) | **Matches** authored whole-verse scope |
| `2Thess.2.1-3` / `2Thess.2.3-12` | **1–2 / 3–12** ([2 Thessalonians index](https://www.biblegateway.com/resources/matthew-henry/2Thessalonians)) | **Matches** authored whole-verse scope |
| `2Pet.2.1-3` / `2Pet.2.3-6` | **1–2 / 3–6** ([2 Peter index](https://www.biblegateway.com/resources/matthew-henry/2Peter)) | **Matches** authored whole-verse scope |
| `Rev.4.1-8` / `Rev.4.8-11` | **1–7 / 8–11** ([Revelation index](https://www.biblegateway.com/resources/matthew-henry/Revelation)) | **Matches** authored whole-verse scope |

**Decision already recorded:** five boundary trims agree with independent
published complete-commentary whole-verse sectioning. For Romans 4, the owner
selected **4:9–16 / 4:17–22** as the practical first-edition whole-verse
indexing policy, *despite* the independent edition's 17a/17b subdivision.
The original **1,720+ words in both affected Romans 4 sections** remain in
the private SWORD. This is deliberate navigation simplification, **not**
a claim that the first section's 17a subject matter ceased to exist or
that a reader selecting verse 17 can show both sections.

The independent sources establish boundaries, not exact line-by-line
historical text/punctuation equivalence. The CrossWire original source
and this reversible six-range plan are still unchanged. This analysis is
editorial evidence for the existing plan, not authorization to publish
it or to create a Romans-specific hack.

## Remaining *decision* gates (not more broad research by default)

1. **Editorial and source review:** the practical six-overlap verse navigation
   and 2 Chronicles 1 chapter-introduction remapping are now explicitly
   recorded and privately validated. Preserve the historical 17a/17b nuance
   in release notes. Independent whole-edition textual/editorial acceptance
   remains distinct from these bounded indexing decisions.
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
