# Resource versions and upstream updates

Bible Resources tracks three independent version lines: (1) a module **installed locally** in Bible/SWORD; (2) our **normalized, published** edition; and (3) the original **upstream** edition at its provider.

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
