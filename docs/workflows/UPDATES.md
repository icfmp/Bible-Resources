# Upstream changes and resource updates

Bible Resources curates **specific verified editions**, not every latest upstream version. The [v1 catalogue update protocol](CATALOGUE_UPDATE_PROTOCOL.md) documents the public client-facing update feed. Only approved packages appear in that feed.

## Monitor

- Check upstream sources with the repository's read-only provider/inventory tools, not by downloading or mirroring their full text.
- Distinguish upstream availability, source edition revision, SWORD module version, changed content bytes, and local editorial release number.
- Compare exact archive and native-content hashes as appropriate; a `Version` string alone cannot prove that content changed (or stayed identical).
- When upstream changes, identify the new edition, license, corrections, annotation ownership and compatibility impact before considering a new import.
- Preserve the previous approved original, cleaned master, build evidence and release; do not silently repin or overwrite.

## Review and release

Create or update the edition's issue and provenance. Classify differences as source changes, packaging-only changes, upstream fixes, local corrections or ambiguous cases. Re-run the applicable full [production gates](../PRODUCTION_PIPELINE.md). Preserve local approved corrections without disguising a curated edition as original upstream stock.

An updated public module requires explicit approval, exact new package hashes, updated catalogue metadata and verification of the actual download. Do not assume that a green update monitor authorizes publication.

## Ownership

Bible Resources owns source selection, provenance, curation, builds and the published catalogue. The [Bible application](https://github.com/icfmp/Bible) owns its own client caching, update prompts, download transactions and display behavior. Report client defects in that repository instead of editing authoritative source text to accommodate a reader.

See [source identity](../policies/SOURCE_IDENTITY.md), [catalogue integration](CATALOGUE_INTEGRATION.md) and [upstream contributions](UPSTREAM.md).
