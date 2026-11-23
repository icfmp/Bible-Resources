# Workspaces for unpublished source-first investigations

New unpublished work belongs under `work/<type>/<language>/<resource-id>/`,
using real resource categories only as needed. Do not commit placeholder
directories or disposable build output. Immutable originals go to
`sources/original/`, approved editorial masters and edition-specific evidence
to `sources/cleaned/`, and SWORD payloads to `modules/`.

## Existing HMCC Modern authoring archive

`work/mhcc-modern/` remains an **active provenance-bearing authoring archive**,
not scratch space: the historical 1,189 chapter manuscripts and preliminary research/intro
candidates are pinned at immutable Git revisions. The approved modern
editorial source is under `sources/cleaned/`. In particular, the
published SWORD `TextSource` URL and reviewed source/release records refer
to these paths. The authoring snapshots are recoverable via the preserved `accepted/README.md`
and the approved original source and release hashes remain unchanged. Use the navigation pointer at
[work/commentaries/hmcc-modern/README.md](commentaries/hmcc-modern/README.md).

The former private CCEL MHC ThML-to-IMP feasibility code is **not** an OSIS-first
production tool. Its last tracked bytes are recoverable at
[the pre-cleanup Git revision](https://github.com/icfmp/Bible-Resources/tree/e496c55f1c3727797ffcb0603cf7bc7fb14a9a4b/work/commentaries/mhc-crosswire/experiments/ccel-imp);
do not run that historical experiment as an active compiler.

Consult the current
[workspace architecture](../docs/architecture/WORKSPACE_LAYOUT.md)
and [production contract](../docs/PRODUCTION_PIPELINE.md).

For modern HMCC release evidence see [the retained working-index](mhcc-modern/production/README.md).
