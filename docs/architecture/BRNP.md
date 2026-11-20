# Bible Resources Normalization Profile (BRNP) — proposal

**Status: deferred to [issue #451](https://github.com/icfmp/Bible-Resources/issues/451). This is an architectural direction, not a normative XML profile or an active release gate.**

## Purpose

Use a **shared technical representation** for all *new reviewed cleaned* Bible Resources modules so standard SWORD readers have predictable structure, independently of the upstream provider. Normalize the XML/markup representation of **existing authorial information**, without rewriting its content or making different editions appear identical.

The project uses official OSIS 2.1.1 for relevant Bible/commentary masters, official USFM/USFX as source formats where applicable, and standard SWORD/TEI profiles for other supported resource types. BRNP must **not** invent a private XML dialect or bypass the official schema.

## Non-negotiable boundaries

- Keep exact words, punctuation, verse references, versification and intentional omissions.
- Preserve authorial paragraphs, poetry, titles, introductions, commentary section/range coverage, notes, labels, cross-reference targets, lexical links and their positions.
- Normalize only source-attested equivalent representations, with reversible, source-hash-bound approved transformations.
- Block unfamiliar or ambiguous standard constructs pending review; do not silently flatten, discard, guess or move them.
- Require independent checks of official schema validity, source-to-cleaned equivalence, cleaned-to-native SWORD round-trip, and multiple readers.
- Prefer deterministic and idempotent rules; any canon change or material editorial adaptation is a **separate reviewed edition**, not an automatic normalizer operation.

## Planned specialization

| Profile | Intended scope | Status |
| --- | --- | --- |
| Common source-preservation rules | Origin, references, notes, authorial structure, metadata, provenance | Principles accepted; existing policies govern |
| OSIS Bibles | Book/chapter/verse hierarchy, milestones, paragraphs, poetry, titles, lexical alignment | Detailed choices/testing deferred |
| OSIS commentaries | Authorial units, `annotateRef` ranges, introductions and navigation | Detailed choices/testing deferred |
| TEI dictionaries / general books | Format-specific hierarchy and entry semantics | Not specified |
| Compiled SWORD | Correct driver/configuration, native key/data parity and reader interoperability | Existing production gates remain authoritative |

## How the profile becomes mandatory

[Issue #451](https://github.com/icfmp/Bible-Resources/issues/451) must document exact permitted standard structures and attributes, gold fixtures, edge cases, deterministic normalizer rules, validator behavior, corpus-wide tests on several real Bibles/commentaries, native SWORD and reader evidence, migration impact, and an explicit owner decision before enforcement.

Until then, use the [normalization policy](../policies/NORMALIZATION_POLICY.md), [commentary policy](../policies/COMMENTARY_POLICY.md) and [production contract](../PRODUCTION_PIPELINE.md). **No experimental BRNP pilot should block or certify a publication.**
