# BPC French J. N. Darby 2024 rev. 2.0 — stage-5 editorial disposition (DRAFT)

**Status: technical evidence reviewed; editorial acceptance and publication NOT approved.**
This permanent review supplements import [#62](https://github.com/icfmp/Bible-Resources/issues/62)
and original-note issue [#133](https://github.com/icfmp/Bible-Resources/issues/133).
It is **not** an authorized correction manifest, a derivative edition, or a
published SWORD module.

## Exact edition and decision boundary

- Work: French *Bible — traduction J. N. Darby*, Bibles et Publications
  Chrétiennes (BPC), edition **2024 revision 2.0**, distinct from the later
  *Darby révisée / DarbyR* edition.
- Official BPC edition history: https://editeurbpc.com/telechargements/JND
  (revision 2.0 dated **2024-09-04**).
- Official original publisher OSIS:
  https://cdn.editeurbpc.com/bible/osis/JND/bible_jnd_2_0.xml
- Exact original OSIS SHA-256:
  `2204629e3efb3024dceb392780ef5e61f4296ea832c90e3dd2a5c3224179c1d3`.
- Rights: publisher lists this JND download as **public domain**, per
  https://editeurbpc.com/telechargements and
  https://editeurbpc.com/telechargements/licences.
  Rights/source verification is separate from Bible Resources owner's final
  release authorization.
- Research binary: `JND2024Research`, CrossWire SWORD **zText**,
  `Versification=Luther`, compiled with full CrossWire r3918 `osis2mod`;
  **not** the eBible stock zText binary (which loses all original note caller
  labels; issue [#95](https://github.com/icfmp/Bible-Resources/issues/95)).
- Source-faithful, **test-only** original ZIP: SHA-256
  `6f1ad63a4c0a51e052bc5aa29bed79704a0c014cf1e9bd74af66542839e48a7b`,
  from [original run #43006720611](https://github.com/icfmp/Bible-Resources/actions/runs/43006720611).
  The stable module **has not been released**.

**Proposed faithful-edition decision (NOT approved):** preserve the publisher
OSIS values **as authored**, including invalid or semantically questionable
original `osisRef` attributes, and disclose the linked-note limitations.
The alternative — fixing original links in a curated derivative — would need
a separately authorized, reversible, exact-source-SHA-bound editorial plan.
Never modify Scripture, add absent verses or hide upstream errors in a SWORD
reader adapter. Preserve all original note bodies and labels.

## What the source-to-SWORD evidence actually proves

| Editorial lane | Evidence and status | Remaining limitation |
|---|---|---|
| Numbered Scripture | **31,166/31,166** exact original source keys; all non-whitespace words, case and punctuation match compiled SWORD | This is **not** byte-identical original whitespace |
| Notes | All **6,340** note bodies, kinds, caller identities and word/character positions preserved | Rendering of callouts depends on reader |
| Note reference attributes | All **1,044** explicit `osisRef` targets preserved **literally** | Original targets are not necessarily valid or correct |
| Marked structures | **19,600** paragraph/poetry start/end positions and **1,257** heading texts/positions agree in native scan | Exact layout/indentation/typographic line breaking per GUI not exhaustively certified |
| Whitespace | **43,366** source/native whitespace-run differences recorded and explained at compiler/XML-fragment level; **4,291** unmarked original internal newline gaps separately classified | Whitespace is NOT identical; additional presentation samples and owner acceptance remain |
| Simple target addressability | **1,034/1,044** originally supplied targets are syntactically addressable against the publisher/source-checked SWORD verse index, including all **116** standard complete ranges | **Not proof** that the 1,034 original destinations are the intended ones |
| Real GUI note activation | Exact original `Gen.2.4 → Exod.6` click visually confirmed in isolated **Xiphos**, [PR #144](https://github.com/icfmp/Bible-Resources/pull/144) and [run #43092872776](https://github.com/icfmp/Bible-Resources/actions/runs/43092872776) | One sample, not a full audit of all note hyperlinks |
| Real two-Bible reader | Darby and an independently installed released Segond text separately visible in isolated Xiphos, [PR #142](https://github.com/icfmp/Bible-Resources/pull/142) | Alignment and all other application readers not exhaustively checked |
| Stable candidate driver | Exact source-faithful zText payload copied byte-for-byte to private trial ID and read in **five** actual `diatheke` passages; [PR #145](https://github.com/icfmp/Bible-Resources/pull/145), [run #43094809437](https://github.com/icfmp/Bible-Resources/actions/runs/43094809437) | Repackaging test is **not** a released/owner-approved artefact |

Publisher-source-independent metadata reviews: [run #43014891638](https://github.com/icfmp/Bible-Resources/actions/runs/43014891638),
[merged generic diagnostics #140](https://github.com/icfmp/Bible-Resources/pull/140)
and [#143](https://github.com/icfmp/Bible-Resources/pull/143),
[real pinned original run #43089960679](https://github.com/icfmp/Bible-Resources/actions/runs/43089960679).
All authorial targets remain source-to-native-identical; **no compiler-induced
loss of the referenced attributes was found**.

### Independent Xiphos screenshot identity correction (2026-11-12)

The real two-module [run #43086458383](https://github.com/icfmp/Bible-Resources/actions/runs/43086458383)
has **two different sampling phases**. Direct independent visual inspection
of its original `psalm-poetry.png` (SHA-256
`70ac0dd7e860a1ce420aa27b49b603ec0a23cff3df12608cd1e264e8333b28b2`),
`matthew-heading.png` (SHA-256
`65e149f51495f94021879c9daf5ba3cf5637cd739179bce14fd35571da4ed6ea`)
and `romans-annotation.png` (SHA-256
`eb9154fe1cef448bd55c919877f5525b26d85633cccf0d8c7ad429298e42b4ab`)
shows an explicit **`BRLSG1910` title bar in all three**: they
depict the **Segond comparison module**, auto-selected by Xiphos on initial
startup, **not Darby typography**. Do not certify Darby's Psalms poetry,
Matthew headings or Romans callout layout from these three images.

The *later* `module-tree-stage-8.png` and genuine Darby
`Gen.2.4` note-link screenshot are separate independently reviewed
evidence and remain valid for their much narrower claims.

**Correction implemented and independently reviewed:** [merged PR
#147](https://github.com/icfmp/Bible-Resources/pull/147) at
`72adbf6c4b375232809861393aeba69dd9520b64` captures the same reader
passages **after** the requested Bible is selected in the Xiphos module
tree, preserving both earlier and later samples distinctly. Exact-head
[Validate #43151365047](https://github.com/icfmp/Bible-Resources/actions/runs/43151365047)
and real isolated [Xiphos GUI #43151365056](https://github.com/icfmp/Bible-Resources/actions/runs/43151365056)
both succeeded. Artifact `xiphos-headless-smoke-43151365056`, ID
`13913572849` (short retention), contains new
`study-samples/post-module-selection/*.png` files. Each independently
inspected screenshot SHA-256 matches the metadata receipt:

| Post-selection specimen | Exact screenshot SHA-256 | Actual visual witness |
|---|---|---|
| `psalm-poetry.png` | `b98210ca9e62b675d68b9328a814c8e1e6c19f2f567531b6e90d2ab67a9c50d9` | Xiphos title shows **`JND2024Research: Psalms 23:1`** with selected Darby in the module tree, heading *Psaume 23*, French prose and visible line/paragraph breaks |
| `matthew-heading.png` | `255c283fa09428870b7b19f9a8e42f6925f6be98e33649d230cd9ea3818a558d` | **`JND2024Research: Matthew 5:1`** selected, chapter heading, French Beatitudes and inline verse numbers with note calls |
| `romans-annotation.png` | `2d93cd7068200e8abd9fa97029a7a063a3ff3b906019c7a72d280dc133b38889` | **`JND2024Research: Romans 8:28`** selected, French Scripture, verse numbers, note superscripts and paragraph separation near verse 31 |

A fourth `genesis-prose.png` file has SHA-256
`c640d087c40e251d371a846f86b92f5102edf623c3ec95e86b57d76057a3d87a`
and matches the receipt, but was **not** separately visually assessed in
this checkpoint. The three listed actual Darby screenshots establish
**representative readability and structure in one Xiphos reader session**.
They do **not** establish typographic identity to printed BPC, every
poetry/heading/callout case, all reference destinations or Bible-app
compatibility. Exact original whitespace remains unproved. The prior
whole-source native structure-position audit is unaffected.

## Ten original OSIS target limitations — manual editorial proposals only

Reference labels in the source are frequently relative to preceding prose.
The table quotes small, public-domain **reference attributes**, not full
Scripture or note text. `n` is the one-based host note index.

| Original note host | Original `osisRef` | Classification | Contextual proposal — never auto-apply |
|---|---|---|---|
| `Lev.8.15` n2 | `Lev.30.10` | Authorial target points to a non-existent Leviticus 30 | Abbreviated “30.10” follows Exodus 29.36: **likely `Exod.30.10`** |
| `2Sam.7.27` n1 | `Ruth.20.2` | Authorial target points to a non-existent Ruth 20 | Context refers to Ruth 4.4 and 1 Samuel 9.15: **likely `1Sam.20.2`** |
| `Matt.23.13` n1 | `Matt.23.14` | Destination verse key intentionally absent | Original note explicitly describes verse 14 as a Textus Receptus addition: **keep note, do not fabricate verse** |
| `Acts.3.1` n1 | `.3` | Nonstandalone relative OSIS chapter target | Displayed “Chap. 3”: **possibly `Acts.3`** |
| `Acts.8.36` n1 | `Acts.8.37` | Destination verse key intentionally absent | Original note explicitly describes verse 37 as a Textus Receptus addition: **keep note, do not fabricate verse** |
| `Acts.15.33` n1 | `Acts.15.34` | Destination verse key intentionally absent | Original note explicitly describes verse 34 as a Textus Receptus addition: **keep note, do not fabricate verse** |
| `Rom.5.12` n1 | `Rom.1.à.8` | Nonstandard French chapter-range expression | Printed meaning “chapitres 1 à 8”: **possibly `Rom.1-Rom.8`** |
| `Rom.5.13` n1 | `Rom.5.13.à.17` | Nonstandard French verse-range expression | Printed meaning “versets 13 à 17”: **possibly `Rom.5.13-Rom.5.17`** |
| `Rom.8.9` n1 | `Rom.8.1.à.11` | Nonstandard French verse-range expression | Printed meaning “versets 1 à 11”: **possibly `Rom.8.1-Rom.8.11`** |
| `Rom.16.25` n1 | `1Cor.5.32` | Source reference to non-existent 1 Corinthians 5:32 | “5.32” follows Ephesians 3.2–11: **likely `Eph.5.32`** |

### Additional semantic suspect among the 1,034 addressable attributes

At **`Rom.16.25` n1**, the original *other* `osisRef`
`1Cor.2.2-1Cor.2.3` addresses real text, but a printed “2.2–3”
follows Colossians 1.25–27. **Likely intention:
`Col.2.2-Col.2.3`**, subject to BPC's decision. This is an
**eleventh suspected problem**, not an eleventh mechanically
unaddressable target: the reported **1,034/1,044** index statistic remains
accurate, but is strictly syntactic.

**Review status of each suggested correction:** `proposed_for_publisher_confirmation`.
Do not conflate the printed label, the original destination and the proposed
one. A future authorial corrected edition must be acquired and audited as a
**distinct pinned source revision**, not silently substituted for these
original bytes.

## Publisher-facing action (no message sent)

BPC offers an official
[“Signaler une erreur” form](https://editeurbpc.com/signaler)
**expressly for non-clickable/incorrect Bible references**. Suggested
submission scope: this exact **2024 revision 2.0**, original OSIS URL,
the three absent-edition references as contextual non-actionable examples,
the probable four book/context errors (including the indexed
`Rom.16.25` case), three French `à` ranges and the relative `.3`
chapter target. Ask whether BPC wants to correct source `osisRef`
attributes while leaving displayed note prose and textual-critical
verse omissions unchanged. Do **not** imply a publisher defect was confirmed
by BPC, and **do not claim contact or publisher reply** until it happens.

## Pending acceptance (leave 5/7 unchecked)

- [x] Exact source/compiled annotation bodies, caller letters, anchors,
  original explicit target attributes and marked structural positions compared.
- [x] Ten mechanical target anomalies identified case by case; one more
  contextually suspect, syntactically indexed attribute disclosed.
- [x] A valid note cross-reference successfully opened in real Xiphos.
- [ ] **Owner editorial decision**: accept this as-is, source-faithful release
  with disclosed upstream link/typography limitations, or request a separately
  reviewed correction plan / publisher revised source.
- [ ] **Presentation decision**: acknowledge that 43,366 whitespace runs are
  not byte-identical and that real-reader typography is sample-tested, not
  a full print-facsimile certification.
- [ ] Independent Bible client test if available (track `NOT TESTED`
  rather than assert a success); decide whether its absence blocks this
  particular stable SWORD distribution.
- [ ] Stage-7 final rights/editorial approval, immutable stable release
  hash, catalogue publication and external verification.

**Current release decision: HOLD.** Stage 4 is done; stage 5 retains
**PARTIAL** status pending owner/editorial acceptance. Stage 6 has extensive
positive SWORD/Xiphos evidence but is not yet accepted as the complete gate;
stage 7 is not started. No source note, Scripture content or public catalogue
was changed by writing this report.
