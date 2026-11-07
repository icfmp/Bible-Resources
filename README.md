# Bible Resources

**A curated, reproducible SWORD resource repository for Bible and other compatible readers.**

Bible Resources is an **independent community project**, not an official CrossWire repository. Its goal is to provide one reliable catalogue of biblical texts, commentaries, dictionaries and related resources, with clear provenance and consistent editorial quality. Improvements suitable for the original upstream project should be offered back to their maintainers.

## Principles

1. **SWORD first.** Preserve standard module drivers, versification systems and layout. Never introduce a Bible-only binary format.
2. **Preserve meaning.** Keep authoritative, immutable original inputs and distinguish faithful corrections from reader-optimized derivatives. Never silently rewrite the text.
3. **Rights before release.** Permission to download from CrossWire does *not* imply permission to mirror or modify. Release only after affirmative rights review, recorded evidence and human approval.
4. **Predictable quality.** Validate metadata, module layout, Unicode, references, transformations and artefact checksums; smoke-test with a real SWORD reader before release.
5. **Reproducibility.** Build published packages and catalogues from reviewed versioned inputs; record all editorial changes.
6. **Interoperability.** Publish the standard `mods.d/`, `modules/`, `mods.d.tar.gz`, and `packages/` layout as well as a versioned JSON catalogue.

## Status

**Bootstrap / no public modules yet.** `modules/` intentionally contains no imported content. In particular, a French Matthew Henry translation is **not** licensed for republication merely because a supplied JSON archive advertises CC0.

## What lives here?

```text
modules/<slug>/metadata.json       reviewed manifest and rights
modules/<slug>/payload/mods.d/     exactly one SWORD .conf file
modules/<slug>/payload/modules/    compiled SWORD module files
modules/<slug>/EDITORIAL.md        transformation / review record
schemas/module.schema.json         machine-readable format contract
scripts/validate.py               metadata and structure checks
scripts/audit_text.py              non-destructive editorial warnings
scripts/guard_osis.py               schema-pinned OSIS structure gate; no rewrites
scripts/guard_commentary.py         strict OSIS commentary entry-reference guard
scripts/select_sources.py           prioritized SWORD catalogue deduplication (read-only)
scripts/build.py                   deterministic repo + catalogue builder
scripts/smoke.py                   actual SWORD runtime smoke test
.github/workflows/                 CI and GitHub Pages publication
```

Only modules whose `quality.status` is **`approved`** are published, and only if redistribution rights have been affirmatively verified. Other entries remain source-side records and are excluded from distributable output.

## Getting started

Requires Python 3.11+ and `jsonschema` (`python -m pip install -r requirements.txt`).

```bash
python -m unittest discover -s tests -v
python scripts/validate.py
python scripts/build.py --output dist --base-url https://icfmp.github.io/Bible-Resources/
```

The generated `dist/` contains a stable machine catalogue at `catalog/v1/catalog.json`, and a SWORD repository under `sword/`. To test actual SWORD-module behaviour, install `diatheke`, then run `python scripts/smoke.py --dist dist`. CI performs this before deploying when modules exist.

## Upstream version monitoring

Bible Resources monitors **three separate versions** (installed in SWORD, curated in Bible Resources, and source/original). The daily read-only GitHub Action checks all five SWORD catalogues declared by Bible: CrossWire, AndBible Extra, AndBible, STEP and eBible. YouVersion and the two OpenBible datasets are documented separately as inventory-only sources, not SWORD catalogues. The same Action compares the registered providers and endpoint URLs with Bible's current source declarations and fails on drift. The checker never automatically republishes a module. See [Updating resources](docs/UPDATES.md).

To check a local installation: `python scripts/check_updates.py --installed-root ~/.sword`.

**Duplicate upstream editions:** the operational source order is CrossWire → eBible → STEP → AndBible → AndBible Extra. Only *verified same-edition* aliases are automatically consolidated; possible matches block import for human identity review. Run `python scripts/select_sources.py --report-only --output reports/source-selection.json`. This is a read-only candidate report; the future importer is not yet connected. See [SWORD source priority and deduplication](docs/SOURCE_PRIORITY.md).

## LSG + full MHC pilot (manual, read-only)

The preparation scripts and manual GitHub Actions workflow are described in
[pilot #1](docs/PILOT_SEGOND_MHC.md). The registered `lsg` source is
eBible `fraLSG1910eb`; `mhc` means CrossWire **full MHC**, not
`MHCC`. The preflight checks ZIP safety, source hashes, SWORD metadata
and representative `diatheke` keys **without publishing or normalizing
any module**. The separate official OSIS schema probe records provenance
but does not approve the schema by itself.

## GitHub Pages and branch rules

For repository creation, push, Pages activation and branch rules, see [INSTALLATION_FR.md](INSTALLATION_FR.md). The source repository is live at https://github.com/icfmp/Bible-Resources. GitHub Pages must be activated in the repository Settings before the public catalogue endpoint will work.

## Documentation

- [Architecture & distribution](docs/ARCHITECTURE.md)
- [SWORD source priority and duplicate-edition policy](docs/SOURCE_PRIORITY.md)
- [Official versification and omitted verses](docs/VERSIFICATION_POLICY.md)
- [Pilot: Louis Segond 1910 and Matthew Henry Complete](docs/PILOT_SEGOND_MHC.md)
- [Reversible editorial source audit and normalizer](docs/EDITORIAL_AUDIT_WORKFLOW.md)
- [Quality policy](docs/QUALITY_POLICY.md)
- [Editorial rules](docs/EDITORIAL_RULES.md)
- [Resource presentation and evidence-backed strengths/cautions](docs/RESOURCE_PROFILES.md)
- [Strict OSIS source normalization contract](docs/NORMALIZATION_POLICY.md)
- [Strict commentary annotation and reference rules](docs/COMMENTARY_POLICY.md)
- [SWORD and metadata conventions](docs/FORMATS.md)
- [Licensing & provenance](docs/RIGHTS.md)
- [Upstream contribution](docs/UPSTREAM.md)
- [Release procedure](docs/PUBLISHING.md)
- [Import roadmap](docs/ROADMAP.md)
- [Upstream version tracking and updates](docs/UPDATES.md)
- [Complete Bible source inventory and drift checks](docs/SOURCE_INVENTORY.md)

## Licenses

Code, tooling and documentation: **GPL-3.0-or-later** (see `COPYING`). **Modules and their source texts are licensed independently**, as recorded in their metadata; this repository's code license does not relicense their contents.

## Source and compatibility references

- [CrossWire module repository structure](https://wiki.crosswire.org/Creating_and_Maintaining_a_Module_Repository)
- [SWORD module configuration fields](https://wiki.crosswire.org/DevTools:conf_Files)
- [CrossWire module submission](https://wiki.crosswire.org/Module_Submission)
