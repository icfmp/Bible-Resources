# Resource versions and upstream updates

The published, machine-readable interface for discovering **approved Bible Resources updates** is [Catalogue update protocol v1](CATALOGUE_UPDATE_PROTOCOL.md). This stable HTTPS JSON endpoint contains the curated module version, canonical edition ID, actual download SHA-256 and size; it is distinct from the upstream-monitoring reports below. The publication gate checks the advertised version against the released SWORD .conf Version.

## Ownership: Resources versus the Bible application (9 November 2026)

**This repository owns upstream and curated-edition lineage, read-only change detection, publisher-source comparison and new approved resource releases.** Do not mix this with the user's installed edition. Application-side catalogue integration is tracked in [Bible#253](https://github.com/icfmp/Bible/issues/253); opt-in installed-module updates, staged installation, data preservation and rollback are tracked in [Bible#233](https://github.com/icfmp/Bible/issues/233). Both application issues remain open; they do not block completion of this repository's separate monitoring work.

### Compare actual module file bytes, not just SWORD Version

`scripts/check_updates.py` continues to run the metadata-only provider checks. A changed compiled payload **without a changed `.conf` Version or hash** is invisible to that scheduled metadata monitor. For independently acquired and reviewed snapshots of the **same upstream SWORD module ID**, use the additional *private, read-only* comparator:

```sh
mkdir -p /tmp/bible-update-audit
python scripts/diff_sword_snapshots.py \
  --module-id ExampleModule \
  --previous /private/extracted-old-sword-root-or-zip \
  --candidate /private/extracted-new-sword-root-or-zip \
  --report /tmp/bible-update-audit/module-diff.json
```

Inputs must contain a single standard SWORD module `mods.d/*.conf` plus `modules/...` files, either as unchanged directories or ZIP archives. Archive *compression/layout bytes* are not the comparison unit: the tool hashes every bounded original **member file**, checking safe paths, duplicate/case-colliding names, nonregular/symlink members, oversized data and module identity. It writes a new metadata-only receipt containing the previous/candidate file-manifest SHA-256, exact conf fingerprints, original native `Version`/driver/versification, and bounded added/removed/modified filenames. It does **not** print or publish any Scripture or notes, install anything, edit source snapshots, or fetch unknown remote packages. It refuses to overwrite the previous report.

Statuses intentionally mark every change as **requiring review**: same-version binary changes, same-version metadata-only changes, newer/older versions, non-comparable versions, or changed driver/versification. Byte-identical files are marked `file_bytes_identical_not_source_equivalence`, **not** claimed to be the same original textual edition or publication-ready. A false `up_to_date` status cannot be inferred from matching `.conf` alone.

**Real release regression:** normal CI runs this comparator against the exact approved local LSG 0.1.0 payload as a read-only reference and checks that it reports byte identity. Offline synthetic fixtures exercise changed actual data under the *same* version and unchanged conf, altered v11n, bad ZIPs, changed versions, missing files and the differences between compressed/uncompressed package ZIPs. This is not a genuine new upstream revision and does not meet the remaining real-lineage acceptance criterion.

### Important baseline ambiguity: original source versus upstream compiled ZIP

The current published LSG `modules/lsg-1910/metadata.json` links eBible `fraLSG1910eb` with `last_integrated_version=2026-10-29`, while the **separately observed upstream compiled zText module** in the original [real-source pilot](evidence/normalizer-3/real-pilot-source-signals.json) declares `Version=100.0`. The curated LSG was built from **source-attested original USFM/USFX archives**, not that provider's NRSV-indexed compiled zText payload. Therefore the snapshot date **must not be compared numerically to the compiled SWORD version, nor silently replaced with `100.0`**. This remains a source-lineage/provenance issue in [#5](https://github.com/icfmp/Bible-Resources/issues/5).

Before automatically classifying a real upstream change, record the exact source revision type, matching publisher source archive hash, **separate** upstream SWORD `.conf` version and hash, its own package hash, and evidence that each belongs to the same edition/snapshot. Merely seeing a newer remote `Version` never proves that the compiled text differs or that our curated source should be changed.

There are three independent version lines: (1) a module **installed locally** in a SWORD reader (owned by that reader); (2) the **approved, published Bible Resources** edition (owned by this repository); and (3) the original **upstream** edition at its provider (monitored and reviewed here). This repository does not manage an end user's installed resource.

Never compare the numeric values of (2) and (3) as though they were the same release series. A newly detected upstream version is a **review candidate**: verify source changes and redistribution rights, reapply editorial rules, test the result, then publish a separate new curated version.

## Module metadata

An imported module may declare an optional upstreams array with entries containing provider (registered ID), module_id (original SWORD ID), last_integrated_version (version actually **reviewed and imported**) and optionally last_integrated_conf_sha256 and conf_filename. Example:

    "upstreams": [{
      "provider": "crosswire",
      "module_id": "KJV",
      "last_integrated_version": "2.10",
      "conf_filename": "kjv.conf"
    }]

The example is not a statement that this specific version has been checked or imported. Do not advance last_integrated_version merely because a remote provider released a new edition.

## Monitoring

The daily GitHub workflow “Monitor upstream SWORD editions” produces a report artifact and Actions summary. Run it manually from GitHub Actions, or locally:

    python scripts/check_updates.py --output reports/upstream-status.json
    python scripts/check_updates.py --installed-root ~/.sword --output reports/local-status.json

Multiple --installed-root options and --provider filters are supported.

The report records the local SWORD conf Version, curated metadata version, original source Version and the last integrated upstream Version **separately**. The script reads standard SWORD mods.d.tar.gz and, for linked modules, tries the individual mods.d/<module>.conf to detect catalogues that are stale (observed at eBible). Errors or ambiguous versions are flagged; absent results never mean “up to date”. Same-version conf changes can be detected using the optional recorded SHA-256 of the upstream .conf.

Supported statuses: upstream_update_available, up_to_date, upstream_metadata_changed, upstream_older_than_baseline, needs_review, upstream_unavailable, missing_upstream, provider_disabled_or_unknown.

All five active SWORD repositories in Bible (CrossWire, AndBible Extra, AndBible, STEP and eBible) are registered for read-only HTTPS catalogue monitoring. YouVersion is an API source, and OpenBible.info supplies **two datasets** (cross-references and topic scores), not SWORD modules. These three external sources are explicitly reported as `inventory_only`; no API access, dataset-generation comparison, or automatic download is implied. Bible already manages separately versioned, SHA-256-pinned OpenBible study data; see [SOURCE_INVENTORY.md](SOURCE_INVENTORY.md).

The scheduled check also runs `scripts/check_provider_parity.py` against the current `icfmp/Bible` provider declarations to detect added/removed sources or changed URLs. This comparison can fail because GitHub is unavailable, in which case the result is **unavailable**, not falsely current.

This checker does **not** download module binaries, automatically import upstream resources, remove or modify any installed modules, or confer rights to republish third-party texts. A conf file hash cannot prove module data bytes are unchanged: source/binary comparison belongs in the review pipeline.

## Bible client updates (follow-up task)

The Bible application should fetch the official Bible Resources catalogue only under the user's explicit network preferences; identify which local module **edition** is installed; display installed and available curated versions, as well as upstream changes pending review; verify download SHA-256; install into staging; test with SWORD; atomically replace with rollback. Preserve personal notes, highlights, settings and encryption keys. Never silently overwrite a different publisher's module with the same SWORD ID.

See issue #5 and the CrossWire documentation:
https://wiki.crosswire.org/SWORD_Module_Source_Discovery_and_Module_Updating
https://wiki.crosswire.org/Official_and_Affiliated_Module_Repositories


## Duplicate sources and canonical editions

The five SWORD repositories can redistribute the same edition. The separately reviewed [priority policy](SOURCE_PRIORITY.md) decides a **single preferred import source**, while maintaining the ability to monitor alternate upstream copies. Do not create multiple curated modules or version streams merely because an identical edition appears in several catalogues. Explicit alias verification matters: module ID and title coincidences alone are not sufficient. `scripts/select_sources.py` produces a read-only selection report with blocked ambiguities and unavailable-provider fail-closed behavior. It does not automatically change upstream links or existing installed resources.

## Avoiding the upstream-return loop for our own fixes

If Bible Resources sends a reviewed OSIS, metadata or cross-reference correction
back to CrossWire or another source, a subsequent upstream release may consist
entirely of **our own improvement**. A new version is not automatically a
meaningful new import for our curated edition.

For each curated \`upstreams[]\` entry:

- \`contributions[]\` records the submitted upstream issue/PR URL, its
  \`submitted\` / \`accepted\` / \`released\` state, and SHA-256 of the patch.
  Acceptance is **not** proof that a released SWORD module contains the fix.
- \`reconciliations[]\` records a **human-reviewed exact upstream version**
  and its \`.conf\` SHA-256, original and curated content checksums, a comparison
  evidence URL, reviewer, linked contribution, and whether it is
  \`equivalent_to_curated\` or \`contains_other_changes\`.

The scheduled metadata checker **cannot establish content equivalence**: it
reads catalogues / \`.conf\` entries, not the full released module bytes.
Therefore a mere version bump, merged PR or matching description is never
sufficient to dismiss an upstream update.

When a reviewer has verified that the *specific released upstream content* is
already equivalent to our curated edition, the checker emits
\`our_contribution_returned_upstream\` instead of
\`upstream_update_available\`. Keep \`last_integrated_version\` unchanged:
it records the actual source revision imported into Bible Resources, not
the newest upstream release.

If the upstream release also has other changes, it remains
\`upstream_update_available\` and must be reviewed. An accepted/released
contribution without reviewed correspondence merely adds
\`possible_return_of_our_contribution: true\`; it never skips the review.

The prior review applies only to **one exact upstream version + .conf hash**.
A changed version or configuration forces reevaluation. A publisher may also
change binary content in-place without updating its .conf; such a change
cannot be detected with metadata monitoring alone, so full payload verification
remains mandatory before any real import.

The provider's rights, actual module identity, source provenance and
normalization gates are unchanged. This feature does not import or download
module text and does not alter installed users' Bibles.
