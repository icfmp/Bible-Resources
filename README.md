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

## GitHub Pages and branch rules

For repository creation, push, Pages activation and branch rules, see [INSTALLATION_FR.md](INSTALLATION_FR.md). The source repository is live at https://github.com/icfmp/Bible-Resources. GitHub Pages must be activated in the repository Settings before the public catalogue endpoint will work.

## Documentation

- [Architecture & distribution](docs/ARCHITECTURE.md)
- [Quality policy](docs/QUALITY_POLICY.md)
- [Editorial rules](docs/EDITORIAL_RULES.md)
- [SWORD and metadata conventions](docs/FORMATS.md)
- [Licensing & provenance](docs/RIGHTS.md)
- [Upstream contribution](docs/UPSTREAM.md)
- [Release procedure](docs/PUBLISHING.md)
- [Import roadmap](docs/ROADMAP.md)

## Licenses

Code, tooling and documentation: **GPL-3.0-or-later** (see `COPYING`). **Modules and their source texts are licensed independently**, as recorded in their metadata; this repository's code license does not relicense their contents.

## Source and compatibility references

- [CrossWire module repository structure](https://wiki.crosswire.org/Creating_and_Maintaining_a_Module_Repository)
- [SWORD module configuration fields](https://wiki.crosswire.org/DevTools:conf_Files)
- [CrossWire module submission](https://wiki.crosswire.org/Module_Submission)
