# Commentary production — source-first execution

This guide describes **what to do for any commentary**, independently of language, original source provider, author's theological tradition, or SWORD module implementation. The [canonical production contract](../PRODUCTION_PIPELINE.md) sets the mandatory gates; the [seven-stage commentary checklist](COMMENTARY_7_STAGE_WORKFLOW.md) records progress. Neither a successful SWORD compilation nor the output of a research script constitutes editorial approval.

## 1. Identify the exact source

Record its edition, author and editorial attributions, source owner, URL, acquisition time, original hashes and distribution rights (including notes and illustrations). Preserve the original unchanged under `sources/original/commentaries/<language>/<module-id>/`. Prefer original OSIS/USFM, and document any necessary conversion from native SWORD or publisher XML. **Do not represent a reconstructed source as the publisher's original authoring XML.**

## 2. Inventory authorial structure

Inventory every commentary entry and scope before changing it: book, chapter, passage range, verse, introduction, paragraph, heading, link label, target, note, and any unanchored material. Keep chapter-wide entries distinct from verse-specific entries. Capture counts and unresolved anomalies at source locations.

## 3. Create the reviewed cleaned master

Produce a deterministic and reversible candidate, then the accepted `sources/cleaned/commentaries/<language>/<module-id>/<module-id>.osis.xml` (use the existing actual filename where different). Preserve wording, punctuation, theology, commentary boundaries, cross-reference labels and destinations unless source-backed corrections are explicitly approved. Store transformation evidence in the adjacent `CLEANUP_MANIFEST.json` and **human editorial decisions** in `editorial/README.md`. If a reader wants to display a chapter-level commentary at every verse, solve that at the reader layer instead of duplicating authored entries.

## 4. Check the entire source against the cleaned master

Validate OSIS structure and compare all original keys, text, paragraphs, references and notes. Record any reindexing explicitly. Separately verify claimed source defects against an independently identified witness to the **same edition**, not a convenient modern retelling. Uncertain references remain unresolved, not guessed.

## 5. Build and read back SWORD

Use existing tested SWORD tools and versioned input hashes. Run complete native key/text/markup inventories and compare against the approved source; record compiler versions, native file hashes, reproducibility results and exceptions. For source-native reconstruction, the old SWORD module is an attested witness, not automatically proof of original authorial XML.

## 6. Test readers, decide and publish

Verify chapter introductions, passage overlaps, paragraph spacing, note destinations, real links and scope in an independent SWORD reader. Record candidate hash, reader/version and screenshots. Distinguish a source issue from a compiler or UI issue. Rights, editorial review, native parity, reader acceptance and publication are distinct decisions. Publish only via the [release protocol](PUBLISHING.md) and check the public download after publication.

## Optional: translation or modernization

A new-language or modernized edition is **a distinct editorial product**, not a structural cleanup. Only begin from an approved cleaned source, follow [the translation workflow](COMMENTARY_TRANSLATION_FROM_CLEAN_SOURCE.md), and retain separate edition identity, provenance, review and release authorization.

## Where evidence belongs

- Global process, schemas and validation rules: `docs/`.
- Source-specific readings, correction decisions, ambiguous scopes and link decisions: `sources/cleaned/commentaries/<language>/<module-id>/editorial/`.
- Versioned release receipts and source-bound audit reports: the same module's `editorial/releases/` and `editorial/evidence/`.
- Dated, superseded research **not** defining current workflow is recoverable at its immutable Git revision. The previous mixed commentary research/procedure is preserved in [historical records](https://github.com/icfmp/Bible-Resources/blob/2271b6c4473dda6dedf321463e4ffc6b250fd701/history/pipeline/COMMENTARY_PIPELINE_LEGACY_2026-11-20.md).

Do not introduce provider-specific or book-specific fixes into the generic toolchain to make a single module pass.
