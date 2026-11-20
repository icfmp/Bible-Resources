# Editorial record — Matthew Henry's Concise Commentary (classic English)

**Scope:** CrossWire-derived released 0.1.1 native source, with a reconstructed OSIS master. **This is not the lost original CrossWire authoring OSIS.**

## Decisions and boundaries

- Maintain the authorial concise commentary's real chapter/verse/passage groupings, including chapter-only entries; do not fabricate verse entries.
- The reconstructed cleaned OSIS is attested against the approved 0.1.1 source-native SWORD corpus and historical editorial approvals, **not** an exact-byte XML recreation of an original unpublished authoring source.
- Existing approved changes include **24 aliases** and **two prose/reference errata already contained in the approved source**. These are historical records, not a mandate for additional correction.
- Keep introduction/top-level opaque content and the section reference index intact; the reconstructed-versus-native comparisons apply to the specified semantic and navigation guarantees, not arbitrary XML byte identity.
- Preserve authorial source divisions. Where the Bible application's presentation needs to show a chapter commentary for all verses, implement it as reader fallback when appropriate, not as source duplication.

## Evidence

- [Historical 0.1.1 editorial disposition](evidence/release-0.1.1/0.1.1-editorial-disposition.md) and [reader-oriented indexing decision](evidence/release-0.1.1/reader-oriented-indexing-decision.md). These contain earlier draft-status language and exploratory alternatives; current approved scope must be verified from the published 0.1.1 release and cleaned-source manifest, not copied blindly from preliminary proposals.

- [Reconstructed-source attestation and limitations](../CLEANUP_MANIFEST.json)
- [Approved corrections manifest](../../../../../../config/commentary-rebuilds/mhcc-crosswire.json)
- [Classic 0.1.1 release](releases/MHCC-0.1.1.md)
- [Native audit](../../../../../../modules/mhcc-crosswire/SOURCE_AUDIT.json)
- [Reader profile](profiles/en-matthew-henry-concise-crosswire-2-0.md)

**Status:** source-native attested 0.1.1; the original authoring OSIS remains unrecovered. No new edits approved.
