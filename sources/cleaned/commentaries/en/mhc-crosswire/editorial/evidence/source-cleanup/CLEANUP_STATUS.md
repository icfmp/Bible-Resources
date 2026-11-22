# MHC original-source cleanup — historical evidence locator

**Superseded working report.** This file remains because the original, explicitly research-only [source correction plan](historical-plans/mhc-endpoints-private-preview.json) names it as its source witness. It does not describe the current publication state or authorize a new correction. The original detailed investigation is still available from this file's Git history.

## Verified source identity

- CrossWire MHC 2.2 authoring OSIS, revision `537591a94c991941877b47a06666b6a7812e05d8`.
- Original source SHA-256: `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`.
- Source and staged transformation hashes are recorded in [`CLEANUP_MANIFEST.json`](../../../CLEANUP_MANIFEST.json).

## Decisions retained

- Remove only **11 proved inert empty emphasis nodes**, never authored substantive emphasis.
- Correct **three invalid original section-range endpoints** against documented authorial and canonical reference evidence: `Prov.31.10-33` to end verse 31, `Isa.7.17-28` to end verse 25, and `Acts.26.24-44` to end verse 32.
- Distinguish overlapping authorial divisions from repeated native aliases: **six reviewed reindex groups**, without deleting or merging original commentary bodies.
- Correct **25 independently reviewed machine-reference targets**, preserving their printed labels.
- Retype the chapter preface at **2 Chronicles 1** into its genuine native introduction scope, rather than attaching it to the verse-one exposition. Do not copy that preface into verse prose to compensate for reader limitations.

## Authoritative acceptance evidence

The [final 0.1.0 release](../../releases/MHC-0.1.0.md), [source manifest](../../../CLEANUP_MANIFEST.json), and [reviewed change log](CHANGES.md) supersede interim statuses in the initial research. The original source bytes and separate authoritative SWORD binary are never silently modified. Additional reader limitations are described in [reader acceptance](../reader-acceptance-scope-2026-11-19.md).

This is a **historical pointer, not a second acceptance checklist**. Re-run exact source/native tests before accepting any future derivative or new edits.
