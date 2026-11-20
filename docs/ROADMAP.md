# Roadmap — active priorities and evidence boundaries

**Updated 2026-11-20.** The issue tracker and approved resource manifests are the authority for work status. This page is a compact priority map, **not** a second import procedure or a statement that experimental gates are fully implemented.

## Immediate priorities

1. **Source-first, reversible production** — for every selected edition, preserve the immutable original; create reviewed cleaned OSIS/USFM; verify entire source versus cleaned and authoritative witnesses; compile stock-compatible SWORD; perform full native readback, independent reader testing, and publication checks. Follow the [canonical production contract](PRODUCTION_PIPELINE.md). Incomplete generalization is tracked by [#3](https://github.com/icfmp/Bible-Resources/issues/3), [#28](https://github.com/icfmp/Bible-Resources/issues/28), and [#83](https://github.com/icfmp/Bible-Resources/issues/83).
2. **Edition-specific editorial records** — keep approved decisions, exceptions, unresolved source questions and cited evidence beside each cleaned master, in `sources/cleaned/<type>/<language>/<resource-id>/editorial/`. Maintain separate immutable `CLEANUP_MANIFEST.json` and original provenance; see [cleaned resource index](../sources/cleaned/README.md).
3. **Tool consolidation** — reduce obsolete and duplicated `scripts/` entrypoints only after real-callsite audits, replacement parity tests and historical replay checks, [#430](https://github.com/icfmp/Bible-Resources/issues/430). Do not rewrite active workflows merely to shrink the folder.
4. **Publication integrity** — preserve existing versions and their approved source/rights evidence; verify release archives against compiled native content and published catalogue. Keep discrepancies open, including [LSG release parity #271](https://github.com/icfmp/Bible-Resources/issues/271).
5. **Independent BSI and offline enrichment** — `entity-index/` is a separate protected Bible Semantic Index workstream, not an import-cleanup target. The legacy place-context `datasets/` pipeline is marked for controlled retirement in [#38](https://github.com/icfmp/Bible-Resources/issues/38); any future Wikipedia-derived integration must depend on validated BSI identities and independently reviewed source rights.

## Boundaries

- Preserve Scripture wording, editorial apparatus, missing verses, original-language alignment and commentary scope. No silent changes or invented lexical/cross-reference mappings.
- Do not propose direct YouVersion harvesting or reuse the old place-context dataset pipeline as an active roadmap item.
- Distinguish implemented tools, tested modules, editorial approval and published releases. A draft PR or passed CI sample is not a complete production proof.
- Keep historical pilots and postmortems under [the documentation archive](archive) for provenance; they are not the current procedures.
- Use [seven-stage Bible](workflows/BIBLE_7_STAGE_WORKFLOW.md) and [commentary](workflows/COMMENTARY_7_STAGE_WORKFLOW.md) checkpoints, the general production contract and [publishing rules](workflows/PUBLISHING.md) rather than resurrecting competing import procedures.
