# MHCC Modern English — pilot source-meaning comparison (2026-11-14)

> **PILOT-ONLY EDITORIAL REVIEW, NOT AUTHORITATIVE TEXT VALIDATION.**
> The language and reading rhythm were already calibrated with the owner: fluent, modern, airy paragraphs, with Matthew Henry's theology and pastoral voice intact. This review checks the *three existing pilots* against the English commentary wording. It is **not** full-source/index QA, a final translation approval, a chapter-level SWORD/native fidelity certificate, or authorization to resume the production edition. Project issue #270 remains **0 / 1,189 validated**. Original-wide audit and repair remain a separate responsibility under #274.

## Scope, witnesses and method

**Primary readable original:** STEP Bible's rendered original **CrossWire MHCC**:
- [Ruth 1](https://www.stepbible.org/?q=version%3DMHCC@reference%3DRut.1)
- [Romans 3](https://www.stepbible.org/?q=version%3DMHCC@reference%3DRom.3)
- [Hebrews 7](https://www.stepbible.org/?q=version%3DMHCC@reference%3DHeb.7)

**Secondary corroboration only:** CCEL's separately digitized [Ruth 1](https://www.ccel.org/ccel/henry/mhcc.ix.i.html) and [Romans 3](https://ccel.org/ccel/henry/mhcc/mhcc.xxxvii.iii.html). These are *not* automatically a substitute for the published CrossWire edition and must not be silently used to fix original data.

The reviewer read the **whole displayed original text** for each chapter alongside the entire latest draft, section by section: every argument, example, doctrinal assertion, contrast, degree of certainty, imagery, pastoral warning/exhortation and conclusion. Candidate divergences were corrected in the *pilot drafts* only, while keeping the agreed airy reading style. The three drafts use **13 displayed original exposition units** (Ruth 4, Romans 5, Hebrews 4). Ruth's separate book introduction is visibly present in STEP but intentionally **not included in the chapter-1 draft**: it requires an independent introduction unit in a later production edition. The pilot's outline headings are **editorial presentation**, not authenticated original OSIS headings.

This was a deliberate editorial source-to-draft comparison, **not an independent second-human review**. We could access the CrossWire *rendering* but not inspect the exact compiled `BRMHCC 0.1.0` binary and raw native SWORD keys/markup in the available environment. Therefore it is not possible to certify exact original-source text, key/range mapping, source links, references, OSIS boundaries, original introductions or end-to-end SWORD behavior. No work under source-audit issue #274 has been duplicated or claimed.

## Section-level meaning and coverage

| Pilot | Original passage block | Meaning and emphasis explicitly checked | Result against the STEP rendered text after fixes |
| --- | --- | --- | --- |
| Ruth 1 | 1:1–5 | Provision for family vs unjustified move; ruin of household; cross and place; risk of bad company and loss of public ordinances; no evidence of wives' conversion; passing worldly comforts vs enduring blessings | **No remaining material difference detected** after preserving qualified judgment and evidence wording |
| Ruth 1 | 1:6–14 | Death and reform; earth/heaven contrast; Naomi's apparent devotion; prayer in parting; whether to encourage conversion of daughters-in-law; sincerity vs friendship conversion; deliberate cost of discipleship; marital rest vs Christ's rest | **No remaining material difference detected** after restoring the heaven/earth contrast and original quoted marriage-rest expression |
| Ruth 1 | 1:15–18 | Orpah's affection is insufficient; the analogy explicitly concerns salvation through Christ; Ruth represents grace choosing the better part; resolve shuts temptation out like a bolted door | **No remaining material difference detected** after restoring the salvation conclusion |
| Ruth 1 | 1:19–22 | Sudden change; preparation for the great change (left undefined by source); Naomi/Mara names; apparent emptiness vs spiritual fullness; God's providence; affliction must be borne rightly | **No remaining material difference detected** after restoring the fullness and rightly-borne-affliction metaphors |
| Romans 3 | 3:1–8 | Jewish privileges and instruction as means of grace; entrusted Scriptures; promises **only** to believers; God's faithfulness and threatened judgment; justice; obedience not outcome; never do evil so good may follow | **No remaining material difference detected** after restoring restriction, judgment, instruction and divine-justice language |
| Romans 3 | 3:9–18 | Universal guilt as burden; bondage to sin; OT testimony; grace restrains or transforms; professing Christians without fear of God; moral consequence | **No remaining material difference detected** after restoring the burden metaphor |
| Romans 3 | 3:19–20 | Guilt before God; the law condemns the transgressor rather than justifying; corrupt nature excludes self-justification | **No material difference detected** |
| Romans 3 | 3:21–26 | God's provided righteousness; Christ as object of faith and as Prophet/Priest/King; Jew/Gentile welcome; crown/robe imagery; free mercy; paid price; Christ's blood and atonement; God's hatred of sin; accepted Surety debt not charged twice | **No material difference detected**; specialized terms retained deliberately |
| Romans 3 | 3:27–31 | All boasting excluded; faith as an active law; faith not meritorious obedience; relationship/union with Christ; unbeliever's condemnation; law for conviction and guidance in the Mediator's hand | **No remaining material difference detected** after restoring explicit lack of union and the Mediator image |
| Hebrews 7 | 7:1–3 | Melchizedek's typological names; **recorded** absence of ancestry/death contrasted with actual eternal Sonship; no priestly successor; scripture points to Jesus | **No material difference detected**; typological vs literal distinction retained |
| Hebrews 7 | 7:4–10 | Priesthood superior to Levitical; Abraham's honor in the promises; believers share it; spiritual struggle with Christ's strength and grace; being met and blessed by him | **No remaining material difference detected** after restoring the imagery of meeting |
| Hebrews 7 | 7:11–25 | Levitical law/priesthood fail to perfect and reveal mortality; eternal life in Christ; sacrifice and intercession; covenant of works **curse** vs specific comparison to Sinai; fuller liberty/privileges; one permanent High Priest; uttermost salvation; holiness proportional to greater privileges | **No remaining material difference detected** after restoring the curse, agency of the law and proportional exhortation |
| Hebrews 7 | 7:26–28 | Christ completely free from sinful habit/inclination and actual sin; difficulty avoiding complicity in others' sins; assurance through trial, prosperity, death and judgment | **No material difference detected** |

## Concrete correction record

These are corrections to **draft English**, not to the authoritative original. They were saved as one chapter-specific WIP draft commit each.

### Ruth 1 — 7 corrections
1. **Overstatement:** “was right to care” → qualified “was not wrong to provide”; do not turn absence of blame into stronger endorsement.
2. **Household loss:** “loss of his family” misleadingly suggests every member died, when Naomi survived → “ruin upon his household.”
3. **Epistemic status:** women's conversion → “no indication” rather than a categorical claim about whether it occurred.
4. **Earth/heaven providence:** restore the deliberate contrast where earth is *made* bitter so heaven may become dearer.
5. **Marriage-rest image:** restore the author's quoted phrase about “rest in the house of a husband”; do not modernize away the biblical allusion without review.
6. **Theological omission:** explicitly restore that those who leave Christ despite affection **fall short of salvation through him**.
7. **Final image/application:** restore both an **inexhaustible** fullness and that it is affliction **rightly endured**, not just the reader's own manner of suffering, that does good.

Draft commit: [`99e8b90627517028b3419dbcb88beb762a679886`](https://github.com/icfmp/Bible-Resources/commit/99e8b90627517028b3419dbcb88beb762a679886).

### Romans 3 — 6 corrections
1. Restore **instruction** in true knowledge/worship, not only possession of those benefits.
2. Restore the exclusive qualification: promises are made **only** to believers.
3. Retain the warning of actual divine **judgment** upon unbelievers, and both doubts and objections about God's justice.
4. Restore the original **burden** metaphor for universal guilt.
5. Make the believer's relationship with Christ, and the unbeliever's **absence of union with Christ**, explicit.
6. Restore the distinction that the law remains a rule **in the Mediator's hand**, rather than generically “under” him.

Draft commit: [`73b40e84d022c02e386916a3ce4a6639b07458d3`](https://github.com/icfmp/Bible-Resources/commit/73b40e84d022c02e386916a3ce4a6639b07458d3).

### Hebrews 7 — 4 corrections
1. Restore the exhortation to desire that Christ **meet and bless us**, rather than only to seek blessing.
2. Restore the point that the Levitical **law itself showed** how weak/mortal the priests were.
3. Preserve the theological distinction that transgressors are under a **curse** in the covenant of works, not merely described as “condemned.”
4. Restore the **proportional comparison**: believers should surpass OT believers in spirituality/holiness as much as their privileges exceed theirs.

Draft commit: [`ec16f300134048e86fbe9b90994847d5400b3fa3`](https://github.com/icfmp/Bible-Resources/commit/ec16f300134048e86fbe9b90994847d5400b3fa3).

## Post-correction pilot checks (executed against committed GitHub content)

| Pilot | Original exposition blocks matched by heading | Readable draft paragraphs | Words in exposition | Longest paragraph | Explicit correction-regression phrases |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ruth 1 | 4 / 4 | 24 | 598 | 51 words | 7 / 7 present |
| Romans 3 | 5 / 5 | 33 | 712 | 39 words | 6 / 6 present |
| Hebrews 7 | 4 / 4 | 26 | 600 | 38 words | 4 / 4 present |
| **Total** | **13 / 13** | **83** | **1,910** | **51 words** | **17 / 17 present** |

These are narrow **readability/coverage/wording assertions**, not machine proof of semantic identity. A source statement could still be lost or altered despite short paragraphs and phrase checks.

## Findings for the editorial specification

1. **The owner's chosen fluent, airy rhythm survives** all 17 corrections; no need to revert to heavy, compact paragraphs.
2. Compression may silently delete consequential doctrinal elements: **salvation, exclusivity, judgment, curse, union with Christ**, or the **strength** of an exhortation.
3. Keep the author's epistemic distinctions (“does not appear,” “no doubt”) and figurative contrasts (burden, inexhaustible fullness, crown/robe, paid debt, door/bolt).
4. Do not delete a biblical quotation or original rhetorical marker simply because it sounds old; distinguish modernizing the *commentary* from silently substituting Scripture wording.
5. Readability cannot justify replacing specialized terms: *Surety*, *justification*, *atonement*, *covenant*, the specific offices of Christ and the role of the Mediator.
6. The short-paragraph layout is approved as a **pilot visual/editorial style**, not as authenticated OSIS paragraph markup; the production version will need source-mapped structured paragraphs.
7. For final production, compare and account for book introductions and actual SWORD section granularity; the three current texts are *examples*, not three signed-off chapter artifacts.

## Completion, limitations and next gate

**Done for the requested pilot phase:** all 13 displayed exposition blocks reviewed, 17 concrete meaning-restoring draft corrections committed, post-correction section and phrase-coverage checks run, and lessons recorded for the future editorial specification.

**Not done, not claimed:** exact byte-attested `BRMHCC` native source comparison, an independent second reviewer, production chapter-level technical/structural validation, source-wide editorial repair, SWORD build or publication. The source-wide task **#274 remains separate**, and the actual modern translation is still **on hold** until that task leads to an accepted corrected source and the owner authorizes resumption.

**Status:** **Pilot editorial meaning comparison completed (provisional, STEP rendering)**; **0 / 1,189 production chapters validated**.
