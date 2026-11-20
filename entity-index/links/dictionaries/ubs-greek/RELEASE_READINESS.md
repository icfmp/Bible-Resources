# UBS Greek v1: provenance, license boundary, and publication checklist

**Status:** research index fully tested; **public redistribution not approved**.
This document records the rights evidence available at the original **pinned
source revisions**, distinguishes upstream datasets from their components,
and makes no assumption that a passing CI job authorizes publication.

## Frozen, inspectable upstream evidence

| Material | Exact source revision | Source notice | Source URL |
| --- | --- | --- | --- |
| UBS Dictionary of the Greek New Testament, English/French edition 1.0 | `a15a96cfaa4ca18a6c0339016645ba1e534db3c8` | Project and Greek-dictionary README: **CC BY-SA 4.0**; UBS Dictionary of New Testament Greek **© United Bible Societies, 2023**; adapted from *Semantic Dictionary of Biblical Greek* © UBS 2018–2023 and Louw & Nida © UBS 1988/1989. The Greek README specifically credits the exhaustive Scripture reference work to SIL. | https://github.com/ubsicap/ubs-open-license/tree/a15a96cfaa4ca18a6c0339016645ba1e534db3c8/dictionaries/greek |
| MACULA Greek Linguistic Datasets, SBLGNT original word inventory | `8423afe47b9e8f24b7772e808af45c7159a6fe7e` | MACULA Greek Linguistic Datasets **© 2022–2024 Biblica, Inc.**, **CC BY 4.0**; the source's own attribution text names “MACULA Greek Linguistic Datasets, available at https://github.com/Clear-Bible/macula-greek/”. | https://github.com/Clear-Bible/macula-greek/blob/8423afe47b9e8f24b7772e808af45c7159a6fe7e/LICENSE.md |
| Underlying SBL Greek New Testament textual edition | The edition cited by pinned MACULA source | MACULA records SBLGNT as material sourced from Logos Bible Software, and its SBLGNT source README says the underlying SBLGNT license was updated to **CC BY 4.0**. | https://github.com/Clear-Bible/macula-greek/blob/8423afe47b9e8f24b7772e808af45c7159a6fe7e/SBLGNT/README.md |

The pinned MACULA `LICENSE.md` **explicitly lists separately originated
components**. These include Nestle1904 transcriptions and morphology,
SBLGNT from Logos, UBS MARBLE word-sense annotations (`@ln`, `@domain`)
**“Used with permission”**, Berean Interlinear Bible glosses, and Cherith
English/Chinese glosses under CC BY 4.0. Consequently, **do not describe
every source field in MACULA as independently clear for sublicensing under
the dataset-level CC BY 4.0**. Before public redistribution, examine the
particular fields actually included in the distributed output and how the
relevant upstream permissions apply.

UBS' pinned `LICENSE.md` is the text of the Creative Commons BY-SA 4.0
license; the *Greek dictionary's own pinned README* explicitly declares
that license for the dictionary. A derived public resource might trigger
attribution, change-notice, license-link, and ShareAlike requirements.
This document is a provenance finding, **not a legal determination about
whether a particular identifier-only mapping constitutes Adapted Material**.

## What was actually completed

The v1 research alignment was merged as PR #428. Reproducible source-pinned
GitHub Actions CI checked the complete **137,741-word MACULA SBLGNT**
inventory. Its private generated lookup contains original word IDs, source
lemma, reference, Strong and original LN witness, UBS headword/sense
identifiers, explicit candidate alternatives, evidence levels, and a
conservative fallback status. It does **not** bundle UBS dictionary
definitions or the biblical Greek verse text.

- **137,694** source-supported lexical headwords (99.966%).
- **123,195** word-specific **provisional** UBS LEXID recommendations
  (89.44%); **zero** independently context-verified sense assertions.
- **12,288** entry-only; **2,207** multiple authentic sense candidates;
  **4** multiple headwords; **47** with no sufficiently supported UBS
  headword.
- All original dictionary/verse/Strong/LN evidence preserved, with
  immutable original `index.json` and separate review reports.
- Generated consolidated lookup is currently an **expiring private
  GitHub Actions artifact (14-day retention)**. Committed source-pinned
  scripts and regression checks are permanent; **the generated output
  itself is not permanently archived**.

## Conservative consumer contract — proposed, NOT authorized for release

| Lookup status | Safe reading/study behavior |
| --- | --- |
| `provisional_ubs_lexid` | Display UBS lexical entry and label proposed sense as provisional; preserve its evidence tier |
| `ubs_entry_only` | Display authentic lexical entry; no asserted contextual sense |
| `ambiguous_ubs_senses` | Preserve and offer genuine source candidate senses without choosing one |
| `ambiguous_ubs_headwords` | Preserve the authentic entry alternatives |
| `missing_ubs_headword` | Explicitly say this pinned UBS edition lacks a verified match |
| `unknown_original_word_id` | Fail safely: no invented word, lemma, headword, or sense |

This does **not** authorize changing `icfmp/Bible`, writing a SWORD
module, committing a public indexed dataset, adding a release, or
republishing UBS definitions.

## Remaining gates (do not mark complete before a real release candidate)

- [x] Source-revision pinned provenance for UBS and MACULA located in
  the original upstream notices, including MACULA's distinct
  third-party/permitted components.
- [x] Research alignment merged and tested, with deliberate source gaps.
- [x] Private reconstruction and no-source-mutation CI checks.
- [ ] Decide public format and version label (identifier-only index,
  downloadable package, SWORD module or another format) and identify the
  exact source fields to be shipped.
- [ ] Apply a field-by-field rights check to the **exact** proposed
  output. Do not infer from the dataset-level license that UBS MARBLE
  annotations embedded in MACULA are freely sublicensable.
- [ ] Prepare complete authorship, source URL, version, license links,
  attribution, and adaptation/change notices for each shipped component;
  resolve CC BY-SA 4.0 obligations where applicable.
- [ ] Make the provisional/evidence-tier and ambiguity labels
  unmistakable for readers, and test representative real passages.
- [ ] Validate the exact public release candidate against original
  source identifiers, word counts, metadata, and licenses.
- [ ] Obtain explicit owner approval **before** publishing or asking
  the Bible application to integrate the public resource.

Follow-up decision: [issue #431](https://github.com/icfmp/Bible-Resources/issues/431).
If the project chooses to retain an internal research resource indefinitely,
rebuild the ephemeral output from the pinned source revisions and archive it
in a private controlled location through a separately reviewed workflow.
Do not silently make private GitHub Actions artifacts public.
