# Bible source inventory and drift detection

The source of truth for what the Bible application **declares** is
[icfmp/Bible/bible/providers.py](https://github.com/icfmp/Bible/blob/main/bible/providers.py).
Two additional non-SWORD datasets are declared in
[bible/reference_data.py](https://github.com/icfmp/Bible/blob/main/bible/reference_data.py)
and [bible/topic_data.py](https://github.com/icfmp/Bible/blob/main/bible/topic_data.py).

This repository keeps one reviewed snapshot in [config/upstreams.json](../config/upstreams.json).
The read-only checker in [scripts/check_provider_parity.py](../scripts/check_provider_parity.py)
compares all provider IDs, source URLs, catalogue URLs, package URLs, and
OpenBible dataset URLs with Bible's current main branch. It parses Python AST
literals only; it never imports or executes Bible code, fetches Bible texts,
or changes Bible's code.

## The declared sources

| Source | Kind | Version surveillance |
|---|---|---|
| CrossWire | SWORD catalogue | Active for catalogue metadata |
| AndBible Extra (Xiphos HTTPS mirror) | SWORD catalogue | Active for catalogue metadata |
| AndBible | SWORD catalogue | Active for catalogue metadata |
| STEP Bible | SWORD catalogue | Active for catalogue metadata |
| eBible | SWORD catalogue | Active for catalogue metadata |
| YouVersion / Bible.com | API / edition metadata | Inventory only; API permissions differ by edition |
| OpenBible cross-references | ZIP dataset | Inventory only; Bible publishes pinned snapshot revisions separately |
| OpenBible topic scores | ZIP dataset | Inventory only; Bible publishes pinned snapshot revisions separately |

The Xiphos legacy HTTP/FTP source is documented but is not an active direct
Bible provider: AndBible Extra is an incomplete HTTPS mirror, not a claim that
the two catalogues are equivalent. Bible's separately curated topic vocabulary
is **not** an upstream provider.

## What a check does and does not mean

On each scheduled check, the monitor attempts to load all five SWORD
catalogues. A successful catalogue fetch confirms the metadata was retrievable
**at the time of that run**, not that every entry is licensed, installable,
or unchanged. A failed fetch yields \`unavailable\`, never \`up_to_date\`.
Individual module comparisons run only when a curated module records an
upstream relationship; with no approved modules there are no such comparisons.
Some providers' individual \`mods.d/<id>.conf\` endpoints may differ or be
missing, so the checker falls back to catalogue entries and records warnings.

Non-SWORD entries have a separate, explicit \`inventory_only\` status.
They are **not** silently processed as SWORD. Detecting OpenBible dataset
generation changes or authorised YouVersion edition revisions requires
dedicated, separately tested adapters; neither is implemented here.
The Bible application independently maintains pinned OpenBible archives in
its existing study-resource publication workflow.

The drift check detects declared provider additions, removals, and URL changes
across the two repositories. It is deliberately strict: a new API provider must
be classified and reviewed rather than implicitly treated as a SWORD repository.

## Run the checks

    python scripts/check_provider_parity.py --output reports/source-parity.json
    python scripts/check_updates.py --output reports/upstream-status.json

For an offline checkout of Bible:

    python scripts/check_provider_parity.py --bible-root /path/to/Bible

The scheduled GitHub Action and provider-change pull requests upload these
JSON reports as artifacts and write a run summary. A detected mismatch fails
the inventory job. Network failure is recorded as \`unavailable\` and also
fails the check, rather than giving a false pass. The read-only Action does
not download module text, change upstream files, update our registry,
or publish a release.

## Maintenance sequence

1. Verify the new provider appears in Bible's real source declarations.
2. Decide whether it is a standard SWORD repository or a separate API/dataset.
3. Update \`config/upstreams.json\` with its exact, HTTPS-only endpoints.
4. Add an adapter only if its documented update mechanism can be checked safely.
5. Run unit tests and the source parity check; preserve original provider
   identities and source attribution.
6. Never redistribute a resource until its independent rights review is approved.

Related: [UPDATES.md](UPDATES.md) and [Bible's affiliated-source audit](https://github.com/icfmp/Bible/blob/main/docs/SOURCES_AFFILIEES_11.md).
