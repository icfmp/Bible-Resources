# Native SWORD raw-entry witness

**Purpose:** determine whether an authorially identified verse or passage has actual data in a SWORD native module when the ordinary indexed reference lookup appears empty.

## Method

- Pin both the original edition and compiled SWORD candidate; capture exact file hashes, SWORD driver and versification.
- Compare source-native passage identities against populated native keys and, where needed, inspect native raw entry boundaries without modifying the module.
- Treat an overlapping raw byte/word sequence as *limited evidence* of content presence, not proof that it is assigned to the correct reference.
- When many source verses share one native entry, compare the **entire ordered source group** and all associated section and verse boundaries rather than matching a few words.
- Report source key, observed native key, offset/scope, raw markup, parser version and whether the match is complete or partial.
- Resolve each discrepancy as source, index/driver, compiler or reader behavior and store the full witness record with the edition's editorial evidence.

## Mandatory limitations

A raw witness does not prove original text and punctuation fidelity, note coverage, paragraph/poetry semantics, rights clearance or publication readiness. Unusual verse indexing is not permission to add missing verses. A private research probe is not a universal reader guarantee; follow [the complete native corpus audit](NATIVE_SWORD_WHOLE_CORPUS.md) and [production process](../PRODUCTION_PIPELINE.md).

Historic, edition-specific raw-entry experiments are retained in [the project research history](../../history/pilots/WEBP_NATIVE_RAW_WITNESS_2026-11-20.md).
