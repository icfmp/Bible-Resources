# Publishing an approved module

**There is one current publication route:** [`pages.yml`](../../.github/workflows/pages.yml), on reviewed `main`, creates/verifies immutable GitHub Releases **before** advertising approved modules in the static Pages catalogue. The order matters: a visible catalogue without its corresponding versioned release is a failed publication.

This guide describes the current procedure, not the status of a particular release. Resource-specific receipts, decisions, checksums, incident history and exceptions live beside that resource under `sources/cleaned/**/editorial/releases/` and `editorial/evidence/`.

## 1. Accept the exact source and edition

Before setting `quality.status=approved`, confirm the edition identity, original source SHA-256, rights to redistribute all components, source and cleaned comparison, recorded editorial changes, correct versification and annotation coverage, and independent SWORD/reader checks. Owner editorial and publication approvals are separate from CI success.

Choose the correct proof route:

- **Unchanged stock SWORD:** preserve exact upstream bytes and independently verify the original compiled archive and complete native entry/key identity.
- **Source-derived Bible/commentary rebuild:** compare source and reviewed master, build and independently read back *all* native entries and metadata. A changed compiled commentary uses the distinct `reviewed_compiled_commentary_rebuild` route and must not impersonate original `stock_reader_keys` identity. Require original-to-candidate I/K/TOP topology, explicit approved corrections and aliases, source-bound comparison SHA-256 and exact driver-appropriate payload-member hashes. See `scripts/reviewed_compiled_commentary_rebuild.py`.

- **Reviewed published TEI dictionary:** independently validate the exact historical master against pinned official TEI P5 RELAX NG and Schematron, preserve the original source archive and source-bound adapter, compare every native dictionary key and XML/text record, and bind the reviewed receipt to every installed zLD member. For an existing public edition, the authoritative edition source can remain in its independent repository, with exact archive digests and provenance retained centrally. The publication path does not rewrite the native module.

None of these paths authorizes a textual correction by itself. See [editorial policy](../policies/EDITORIAL_RULES.md), [rights](../policies/RIGHTS.md), and [production contract](../PRODUCTION_PIPELINE.md).

## 2. Prepare one release identity

One stable **curated resource ID** identifies the maintained edition; its installed **SWORD module ID** is a separate identity. Renaming the SWORD ID changes the module configuration and installation paths, can collide with another provider's module ID, and is not a transparent client upgrade.

For a new or updated approved module, require **one active source-pinned release plan** in [`config/release-plans/`](../../config/release-plans) with exact versioned GitHub Release tag, expected deterministic ZIP SHA-256, byte length, module/curated IDs and source/rights authorizations.

A previously approved historical release may use the immutable [legacy binding](../../config/release-legacy-bindings.json), but the historical path **must not** become a loophole for new editions. If old GitHub and Pages packages differ, disclose, independently hash and verify both; never call them identical without proof.

A separate optional reader-facing profile requires its own edition/locale/revision-specific editorial approval and pinned source. An approved module does not automatically approve its description.

## 3. Build and verify locally

Use the repository's established tools (`scripts/validate.py`, `scripts/build.py`, `scripts/catalogue_release_coverage.py`, `scripts/publish_reviewed_release.py`). Check actual CLI arguments in the source/CI rather than inventing a release command.

Before merge, [`validate.yml`](../../.github/workflows/validate.yml) must pass relevant unit/integration tests, native SWORD index/readback, exact compiled package checks, licence/source integrity, catalogue coverage and independent reader smoke tests.

Check the approved release plan against the **exact checkout SHA** and built distribution (do not use a floating branch name):

```sh
python scripts/catalogue_release_coverage.py --built dist
python scripts/publish_reviewed_release.py \
  --built dist \
  --repository icfmp/Bible-Resources \
  --target-sha "$(git rev-parse HEAD)" \
  --verify-only
```

This is a read-only release-plan verification, **not** a publication command. A compiled ZIP, successful `diatheke` probe or green build is not the same as a published and rights-cleared release.

## 4. Publish in the enforced order

The single publisher must:
1. Revalidate the exact protected-`main` sources, approvals, metadata and deterministic packages.
2. Verify release-plan / legacy coverage for **every** approved catalogue entry, including `scripts/catalogue_release_coverage.py --built dist`.
3. Download and hash-check pinned historical versioned releases; create or verify current immutable release tags/assets, then **download** the resulting versioned assets and compare exact SHA-256 and size. Never overwrite existing tags/assets.
4. Only after successful release verification, publish the Pages catalogue and SWORD repository/package layout.
5. Independently download the public HTTPS catalogue and **every advertised** package, verify actual size/hash using `scripts/verify_public_catalogue.py`, and retain the run links.

GitHub Releases and Pages are not one atomic transaction. If release creation succeeds but Pages fails, **do not declare the new release available through the catalogue**; preserve the last successful Pages state and repeat verification safely.

## 5. Final receipt and failure handling

Record versioned GitHub release link, catalogue/public package URLs, actual hashes, exact approval/rights evidence, final full-corpus and reader tests, known limitations and next action under the resource's `editorial/releases/`. Never mark a draft, release asset creation, or deployment attempt as public verification.

Retired resource-specific workflows are historical **replay aids only**, not alternate publishers. The main Pages workflow remains the sole release-before-catalogue path. For client-facing schema see [catalogue integration](CATALOGUE_INTEGRATION.md) and [update protocol](CATALOGUE_UPDATE_PROTOCOL.md). For upstream changes see [updates](UPDATES.md).

The owner-approved BRNP v0.4 structural subset is mandatory for the production publisher and its verify-only CI route. Fetch the pinned official schema with `python scripts/fetch_reviewed_schema.py --directory /path/to/reviewed-osis` before invoking the publisher. See [BRNP](../architecture/BRNP.md). Existing published archives remain immutable; no new publication is authorized by adopting the gate.
