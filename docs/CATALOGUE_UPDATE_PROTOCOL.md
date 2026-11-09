# Bible Resources — curated module update feed (v1)

**Bible Resources exposes a stable, public, machine-readable feed for finding approved curated module updates.** This requires no private API, account, application-specific endpoint or dedicated server.

## Stable public endpoint

**GET https://icfmp.github.io/Bible-Resources/catalog/v1/catalog.json**

The response is a static HTTPS JSON document, built from the approved resource manifests on the protected main branch, and published by GitHub Pages after validation.

### Fields (schema_version = 1)

- **modules[]** — the current approved, redistributable curated resources only. An unpublished upstream change does not appear here.
- **id** — stable package identity within Bible Resources (e.g. lsg-1910).
- **canonical_edition_id** — reviewed underlying edition lineage, independent of the original provider's SWORD identifier.
- **sword_id** — SWORD module identifier installed by a reader (e.g. BRLSG1910).
- **version** — Bible Resources curated release version (e.g. 0.1.0). The publication gate requires that the downloadable SWORD .conf **Version** field agrees exactly.
- **edition, category, language, title, versification** — resource type and identity context.
- **download.url** — HTTPS SWORD ZIP URL, currently the latest approved package for that SWORD ID.
- **download.sha256** — SHA-256 of the **actual ZIP bytes** published at download.url (not the original provider's source ZIP nor the independently packaged GitHub release asset).
- **download.size_bytes** — byte count of that exact published ZIP.

A consumer only needs to read the one JSON document to learn the latest approved curated versions. The standard SWORD repository is available alongside it at https://icfmp.github.io/Bible-Resources/sword/ (mods.d, modules, mods.d.tar.gz and packages), generated from the same approved modules.

## Version and identity semantics

This describes the **publisher's data contract**. Client implementation and user-data migration belong outside this repository.

1. A newer **curated** version for an already-established same-publisher, same-resource identity means a newly approved release is available. A matching displayed title, upstream SWORD ID or canonical edition ID alone never authorizes replacing an unrelated installed module.
2. A **different SHA-256 with the same curated version** is anomalous same-version drift, not an ordinary update. Never silently accept it as a new release.
3. The SHA-256 and size must match the **downloaded ZIP**. This protects against stale HTTP caches, partial transfers and unexpected file changes.
4. A vanished module, smaller version number, changed SWORD ID or different versification does not mean automatic deletion, downgrade or replacement is safe.
5. An original eBible/CrossWire provider's version and our curated version are **independent series**; do not compare them numerically.
6. An unavailable endpoint is not an empty catalogue. The online/offline policy is the responsibility of each client.
7. Approval of redistribution rights, source-to-SWORD fidelity and editorial changes is independent of detecting an upstream release. Only approved resources are advertised.

### Mutable latest-package URLs

The v1 catalogue contains the **current** approved resource versions; it is not a version-history API. The address /sword/packages/<sword_id>.zip is intentionally stable but may serve **different bytes after a later approved release**. Clients must bind downloads to the exact catalogue SHA-256 and size and must not assume the ZIP URL is immutable or provides automatic rollback.

Previously published GitHub release artifacts can remain accessible under their individual release tags, for example https://github.com/icfmp/Bible-Resources/releases/tag/lsg-0.1.0. These may have different packaging and hence a different ZIP SHA-256 from the current Pages package. The separately verified release evidence must always identify which archive's bytes are being checked.

A passed Pages workflow alone does not certify independent external HTTP delivery. End-user-network and native-client acceptance are separate checks.

## Publication of a later approved curated version

1. Verify source identity, authorial content, licensing, transformations and editorial approval.
2. Change the curated module manifest **version** and the embedded SWORD **Version** to **exactly the same value**; the publication validator fails on mismatch.
3. Preserve original publisher sources, previous releases and signed-off audit evidence. Never silently reuse a released version number for modified binary content.
4. Regenerate and review the committed catalog/v1/catalog.json snapshot using the deterministic builder. The build refuses an out-of-date committed snapshot.
5. Merge only after the validation suite succeeds and the project owner has approved publication. The Pages builder publishes the JSON manifest and standard SWORD package together, computing the actual ZIP SHA-256/size.

Repository CI also tests that the generated catalogue and committed snapshot match; the ZIP really exists with the advertised SHA-256 and size; every entry corresponds to an approved resource with the correct reviewed canonical edition; and the embedded SWORD conf Version matches the JSON version. A deliberately mismatched version is rejected.

This protocol does **not** change the published LSG 0.1.0 Scripture text, notes, indexes, released version or binary payloads.

For monitoring updates **from upstream providers** into Bible Resources, including same-version binary drift, see [upstream update tracking](UPDATES.md) and [issue #5](https://github.com/icfmp/Bible-Resources/issues/5).
