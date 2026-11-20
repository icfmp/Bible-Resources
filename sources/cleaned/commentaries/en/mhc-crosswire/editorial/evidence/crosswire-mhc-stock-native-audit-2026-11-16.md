# MHC 2.2 — original CrossWire stock/native investigation

**Historical read-only audit.** Its source/stock discrepancy research helped justify reconstructing the reviewed MHC master. The released source and final native hashes are controlled by [`CLEANUP_MANIFEST.json`](../../CLEANUP_MANIFEST.json), [module source validation](../../../../../../../modules/mhc-crosswire/SOURCE_VALIDATION.json) and the [MHC 0.1.0 release](../releases/MHC-0.1.0.md). The detailed chronological probes remain in the file's Git history.

## Exact inputs

- CrossWire compiled module: `MHC` 2.2, `zCom4`, KJV, original ZIP SHA-256 `6bcb936873ca144e317805e5c1677940fd86e2403f7c14517752e44f25c8882b`.
- Independently pinned authoring OSIS: Git revision `537591a94c991941877b47a06666b6a7812e05d8`, source SHA-256 `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`.
- Official provider record: [CrossWire MHC 2.2](https://www.crosswire.org/sword/modules/ModInfo.jsp?modName=MHC).

## Why the upstream stock was not treated as a perfect source master

Original authorial OSIS and compiled SWORD native groups do not always have identical section boundaries or entry ownership. Research identified several source-only exposition stretches, book-end native K passages crossing chapter/book boundaries, ambiguous Psalms titles, and cross-edition differences with CCEL's independent digital text. These findings **must not** be interpreted as permission to copy CCEL content or invent commentary sections.

The final corrected MHC master was accepted through independent source-text/structure preservation and native recompile/readback, not by declaring the original stock binary or the CCEL copy universally authoritative. Actual reviewed changes are the 11 inert tags, three invalid section endpoints, 25 machine-only reference targets, six overlap groups and 2 Chronicles 1 preface reclassification in the [source manifest](../../CLEANUP_MANIFEST.json).

## Limits

A stock native key scan or checksum **does not establish exact authorial paragraph/notes or editorial rights parity**. Retain separate original-source hashes, exact source↔cleaned comparison, native readback and real-reader checks. Any future alleged authorial loss must receive an individual evidence-backed issue and reversible correction.

Historical source/native reproducibility: [issue #285](https://github.com/icfmp/Bible-Resources/issues/285), [original discrepancy issue #295](https://github.com/icfmp/Bible-Resources/issues/295), and [private full original stock scan #43945788585](https://github.com/icfmp/Bible-Resources/actions/runs/43945788585).
