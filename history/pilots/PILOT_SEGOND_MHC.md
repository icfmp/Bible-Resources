# First LSG / MHC pilot — useful historical findings

**Archived November 2026 proof-of-concept.** The pilot preceded the current reviewed source masters and releases; statements such as "not yet fetched" or "not published" in the original work log are **not current status**. Original dated commands, hashes and provisional decisions remain accessible through Git history at `d17d41088eea269e879cbfe46f37a17779ea0ef9` and [pilot issue #12](https://github.com/icfmp/Bible-Resources/issues/12).

## Edition distinctions

- **LSG 1910:** source witness eBible `fraLSG`, not another similarly named Segond digital translation. Rights/versification and exact imported source needed separate review. Accepted source, corrections and known limits are in the [LSG 0.1.0 editorial record](../../sources/cleaned/bibles/fr/lsg-1910/editorial/README.md).
- **Matthew Henry Complete:** original provider CrossWire `MHC` 2.2 (`zCom4`), not concise `MHCC` or the independently modernized derivative. Rights and original authored section structure require distinct checks. [MHC 0.1.0 editorial record](../../sources/cleaned/commentaries/en/mhc-crosswire/editorial/README.md).

## Generalizable lesson: versification cannot be assumed

The early **synthetic, seven-key SWORD 1.9.0 probe** compared standard `NRSV` and `Segond` registries. Under NRSV, the inspected Exod 7.26–29 keys were mapped to Exod 8.1–4 and the Psalm 3.9 query was mapped to Psalm 4.1; the `Segond` registry preserved the examined source identifiers. This demonstrated **addressable canonical slots only**. It was not a source-text/notes or independent-reader parity test.

Therefore, do not introduce missing verses, change the source's intentional omissions or claim that an index probe certifies punctuation, notes or paragraph layout. A source-to-native full-corpus comparison remains mandatory for any new or updated edition.

## Evidence boundary

The old experiments were metadata-only and never granted general editorial permission. Publication requires the actual original source identity, reviewed transformations, independently inspected native data, rights and user authorization, followed by public-download checks. Follow the [single production contract](../../docs/PRODUCTION_PIPELINE.md), not this archived pilot plan.
