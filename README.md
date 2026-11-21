# Bible Resources

**Source-faithful biblical texts, commentaries and other study resources in standard SWORD format.** Bible Resources is an independent curation and distribution project; it is not an official CrossWire repository or a replacement Bible text format.

The project maintains preserved original source evidence, reviewed cleaned editorial masters, reproducible SWORD packages and a [versioned public catalogue](https://icfmp.github.io/Bible-Resources/catalog/v1/catalog.json). Compatible readers, including the [Bible application](https://github.com/icfmp/Bible), may consume approved modules.

## Start here

- **[Documentation for new contributors](docs/README.md)** — start here for architecture, source ownership, rules and workflows.
- **[One production process](docs/PRODUCTION_PIPELINE.md)** — source identification and rights → immutable original → reviewed cleaned master → full fidelity check → SWORD compilation and readback → independent readers → approved release.
- **[Editorial and legal policies](docs/policies/README.md)** — immutable authorship, notes, original versification, editorial decisions, redistribution.
- **[Architecture and resource paths](docs/architecture/README.md)** — where things belong.
- **[Task-oriented workflows](docs/workflows/README.md)** — import, translation, review, update and publication.
- **[Technical verification methods](docs/technical/README.md)** — schema, OSIS/USFX, native reference index and complete-text/annotation audits.
- **[Contribution guide](CONTRIBUTING.md)** — how to prepare a reproducible change.
- **[BRNP tracking issue #451](https://github.com/icfmp/Bible-Resources/issues/451)** — future common structural normalization profile; the draft is *not yet* a production gate.

Current editorial decisions, approvals, source/archive hashes, and issues belong to each resource's own `sources/cleaned/<type>/<language>/<resource-id>/editorial/`, not to the general manuals.

## Principles

1. **Preserve the work, not an accidental encoding.** The identified work and exact edition govern words, punctuation, source-attested layout, notes, reference relationships and meaning. Improve proved technical defects only by documented, reversible, independent review; never invent content.
2. **Originals are immutable.** Record exact edition/source identity, provenance, rights and SHA-256, and retain input bytes without silent modifications.
3. **Use official standards.** OSIS/USFM/TEI and existing SWORD drivers/versifications take priority over proprietary representations; a schema-valid file still needs independent content and reader checks.
4. **Rights before release.** A publicly accessible upstream archive does not automatically authorize republication or modifications.
5. **Evidence before claims.** Distinguish source integrity, native module fidelity, reader compatibility, human editorial approval and actual public publication.
6. **Reuse and contribute upstream.** Improve existing generic tools and report attested upstream errors to maintainers when appropriate.

## Public distribution

The current published package and its hash must be taken from the actual [v1 catalogue](https://icfmp.github.io/Bible-Resources/catalog/v1/catalog.json). The repository also serves a [standard SWORD file repository](https://icfmp.github.io/Bible-Resources/sword/). Use the [catalogue integration guide](docs/workflows/CATALOGUE_INTEGRATION.md) for identities, safe downloads and updates.

Previously published editions include:

- [Louis Segond 1910 — BRLSG1910 0.1.0](https://github.com/icfmp/Bible-Resources/releases/tag/lsg-0.1.0)
- [Darby — BRJND2024 0.1.1](https://github.com/icfmp/Bible-Resources/releases/tag/darby-jnd-2024-0.1.1)
- [Matthew Henry Concise Commentary — MHCC 0.1.1](https://github.com/icfmp/Bible-Resources/releases/tag/mhcc-0.1.1)
- [Matthew Henry Complete Commentary — MHC 0.1.0](https://github.com/icfmp/Bible-Resources/releases/tag/mhc-0.1.0)

These links are historical release references, not a substitute for checking the current public catalogue and its live package bytes. SWORD IDs may collide between providers; installing or updating a module is a deliberate client choice.

## Verify a checkout

Requires Python and the repository's pinned Python dependencies; native SWORD inspection additionally needs a suitable stable libSWORD toolchain and `diatheke`.

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/validate.py
python scripts/build.py --output dist --base-url https://icfmp.github.io/Bible-Resources/
python scripts/smoke.py
```

Do not interpret a local build as rights clearance, complete source fidelity or public deployment.

## Repository ownership

- `sources/original/`: unchanged upstream sources where redistribution is permitted.
- `sources/cleaned/`: curated source masters, manifests and edition-specific editorial records.
- `modules/`: SWORD payload, metadata and approved module records.
- `catalog/v1/`, `sword/`: versioned public interfaces and compiled package distribution.
- `scripts/`, `tests/`: reusable verification and production tooling.
- `docs/`: lasting architecture, policies, procedures and technical methods.
- `history/`: historical cross-resource research retained for provenance.
- `entity-index/`: **independent Bible Semantic Index workstream**, outside resource housekeeping.

The retired place-context dataset is not a source of truth; future Wikipedia-related enrichment is a separate [Bible-Resources-Wikipedia](https://github.com/icfmp/Bible-Resources-Wikipedia) concern dependent on validated entity identities.

## Licensing

Code, scripts and existing documentation: **GPL-3.0-or-later** (see [`COPYING`](COPYING)). Each source text, original digitization, annotation and compiled module retains its own rights and attribution. For new independent non-software contributions controlled by the project, CC0 may be used where legally authorized, never by re-licensing third-party material. See [rights policy](docs/policies/RIGHTS.md).
