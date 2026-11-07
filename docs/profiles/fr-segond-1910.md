# Louis Segond 1910 — resource profile (DRAFT — NOT FOR PUBLICATION)

**Status:** Source/profile verification in progress. Not approved for the published catalogue or app. This profile is not a claim that the text or package has passed its rights and fidelity gates.

## Intended reader card (provisional)

- **Title:** Bible Louis Segond 1910
- **Language:** French (`fr`)
- **Category:** Bible
- **Translator:** Louis Segond; the 1910 edition is a later revision, so translator and reviser contributions must not be conflated.
- **Historical introduction:** Protestant French Bible commonly identified as the Louis Segond 1910 edition. Exact source-versus-print edition identity remains to be demonstrated.
- **Strengths:** No item approved yet; establish each proposed characteristic with edition-specific documentary evidence.
- **Points of attention:** No item approved yet; candidate investigations are listed below, not as public findings.

## Three distinct provenance layers

| Layer | Record | Remaining verification |
|---|---|---|
| Work / edition | Louis Segond 1910; exact publisher, revision provenance and print comparator to confirm | Confirm historical identity against primary edition |
| Acquired source | eBible source `fraLSG`; SWORD module `fraLSG1910eb` | Record archived source URL, download date, hashes, original `.conf`, rights evidence, source/compiled fidelity |
| Curated release | Bible Resources version **not assigned / not published** | Record any authorized transformation with diff, review, package SHA-256, changelog and SWORD reading checks |

Upstream source: https://ebible.org/find/details.php?all=1&id=fraLSG

Do not treat CrossWire `FreSegond1910` (which includes separately licensed/enriched annotations) as automatically identical or equally redistributable: https://www.crosswire.org/sword/modules/ModInfo.jsp?modName=FreSegond1910 .

## Research candidates — not public cautions

### `segond1910-1tim316` — 1 Timothy 3:16

- **Claim category:** `textual_variant` (and potentially `translation` after verification).
- **Question:** Which exact Greek reading and French wording does the acquired 1910 revision use, and how does that compare with documented editions of the Textus Receptus and modern critical texts?
- **Method required:** Inspect the **actual** LSG1910 source text, the edition's own editorial introduction/notes, the identified Greek witnesses/apparatus and representative French translations. Attribute any historical criticism to its author and edition.
- **Status:** `candidate`. No judgement about doctrinal motivation or systematic suppression is established by this question.
- **Evidence/reviewer/date:** Pending primary sources and editorial review.

### `segond1910-verse-index` — detected source/SWORD reference discrepancy

- **Claim category:** `technical`.
- **Question:** Which verse-key mismatches arise from the original eBible SWORD module's declared NRSV versification, rather than an intentional editorial omission in the biblical work?
- **Existing technical evidence:** [pilot notes](../PILOT_SEGOND_MHC.md), [issue #12](https://github.com/icfmp/Bible-Resources/issues/12).
- **Status:** `candidate` for a reader-facing caution; the technical investigation already exists, but a final publication and potential rebuild are not validated.
- **Editorial boundary:** Do not turn a packaging/index defect into a criticism of the translator; preserve the source's own textual-critical choices.

## Publication checklist

- [ ] Exact edition and responsible editors verified
- [ ] Original package/source provenance and rights verified
- [ ] Source/compiled SWORD fidelity and versification accepted
- [ ] Strengths supported by traceable evidence
- [ ] Each proposed caution supported by passage-level documentation and reviewed
- [ ] Curated release changes attributed and independently recorded
- [ ] Reader-facing profile and detailed citations approved

**Owner:** Bible Resources editorial review; consequential claims require client approval.
