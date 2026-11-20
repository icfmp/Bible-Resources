# UBS Greek v1: provenance, license boundary, and publication checklist

**Status:** the narrowly scoped, identifier-only crosswalk **was published** on 2026-11-20 as [BSI UBS Greek v0.1.0](https://github.com/icfmp/Bible-Resources/releases/tag/bsi-ubs-greek-v0.1.0), with source-checked attribution and public field allowlist. **Broader distribution of original source annotation fields, UBS definitions or a SWORD module remains unapproved.**
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


## Approved narrow distribution — identifier-only crosswalk v0.1.0

On 2026-11-20 the project owner agreed to proceed with publication of the
completed UBS Greek word index, subject to rights clearance. The selected
**narrow public candidate** is a standalone ZIP under the release tag
`bsi-ubs-greek-v0.1.0`, *not* an SWORD dictionary or Bible app integration.

Its exact exported schema is enforced by
[the public allowlist builder](build_public_identifier_release.py).
Only these original MACULA word IDs and UBS identifiers/status fields may
be exported:

| Public field | Exact semantics | Rights/source risk handling |
| --- | --- | --- |
| `by_word_id` JSON object key | Pinned MACULA original word identifier | Attribution to Biblica/MACULA; no copied Greek text |
| `entry_ids` | List of source-authentic UBS MainId identifiers | Attribution to UBS and its CC BY-SA 4.0 source |
| `provisional_lexid` | Optional source UBS LEXID | Always explicitly provisional, not an independent interpretation |
| `candidate_lexids` | Authentic source UBS sense identifiers originally consistent with source LN, not definitions | Identifiers only; original LN values/annotations omitted |
| `status` | Project's transparent editorial confidence/fallback classification | Original project editorial metadata |
| `evidence_tier` | Which of five source-checked evidence procedures supported a proposal | Original project editorial metadata |

Top-level output contains only schema/version, original upstream source
commit identifiers, the license, an explicit non-verified semantics flag,
counts, and the above mapping. **No original MACULA `ln`/`domain`
values**, no Greek biblical word text, lemma, morphology, Strong annotation,
verse passage text, English/Chinese gloss, UBS meanings/definitions, UBS
original prose, or Scripture reference lists appear in the publication.
The source data used internally for matching is not distributed.

The published index's new editorial selection/arrangement is offered
under **CC BY-SA 4.0**, with UBS's CC BY-SA 4.0 and MACULA's CC BY 4.0
source attribution, upstream original license links, authors, original
version locks, explicit change notice, and notice that MACULA contains
third-party materials **not included in this release**.

The public release builder is deterministic and is run against the
independently validated private 137,741-word source index. CI checks
all five evidence tiers, all 137,741 word IDs, checksum, ZIP contents,
file allowlists and absence of the original annotation fields. A public
GitHub Release can be generated **only from a successful source-pinned
workflow run on protected `main`**, with repository write scope isolated
to the publisher job. No PR or failed source workflow can publish.

This is a narrowly scoped owner-authorized release of an identifier-only
**derived index**, not a grant to republish MACULA's underlying UBS MARBLE
semantic annotations or UBS dictionary text. Broader public data exports,
SWORD packaging and application integration require fresh review.

## Completed narrow-release acceptance record — 2026-11-20

The owner approved proceeding with public publication. A **specific
identifier-only** output was then tested and published through protected
main, rather than assuming all MACULA/UBS fields may be redistributed.

- Source-pinned validation: [run #44711949619](https://github.com/icfmp/Bible-Resources/actions/runs/44711949619) — SUCCESS after merge of [PR #435](https://github.com/icfmp/Bible-Resources/pull/435).
- Publication validation: [run #44712276926](https://github.com/icfmp/Bible-Resources/actions/runs/44712276926) — SUCCESS, checked exact archive entry allowlist and checksums before publishing.
- Final [public release](https://github.com/icfmp/Bible-Resources/releases/tag/bsi-ubs-greek-v0.1.0) — not draft, not prerelease; published 2026-11-20.
- `BSI-UBS-Greek-0.1.0.zip`: 1,217,257 bytes, GitHub-verified SHA-256 `eeaf6f1b0dfa7335c522c52374a1d5261412819e074520a455a4822b728eddaf`.
- `BSI-UBS-Greek-0.1.0.zip.sha256`: published separately alongside the archive.
- Export scope: exact original MACULA word IDs and UBS entry/sense IDs, candidate lists, source uncertainty statuses and evidence tiers. Original third-party annotation data, verses, dictionary definitions, source prose and original Greek linguistic data fields remain **excluded**.
- This is an independent, source-attributed, CC BY-SA 4.0 **crosswalk**, not a SWORD module or application integration.

The **complete private source-evidence index** is distinct from this
published derived identifier-only crosswalk and remains unpublished.
Any new exported field, original UBS dictionary content, third-party
annotation, SWORD module or Bible application integration requires a
new explicit rights/editorial decision.

