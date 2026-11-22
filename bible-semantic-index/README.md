# Bible Semantic Index (BSI)

**Independent, offline, source-pinned biblical semantic and lexical indexes.**
This directory contains BSI builders, source evidence, tests and UBS dictionary
crosswalks. It is **not** a Bible translation, a SWORD module, or the Bible
application itself.

## Where the indexes actually are

| Resource | Tracked in this repository | Permanent published data |
| --- | --- | --- |
| Biblical entity index (ACAI-derived, v0.1.0) | [Source lock](data/source.lock.json), [reviewed decisions](data/editorial-decisions.json), [builder](scripts/compile_index.py); complete generated data **not** tracked | [BSI entity v0.1.0 release](https://github.com/icfmp/Bible-Resources/releases/tag/bsi-v0.1.0), ZIP containing `index.json` |
| UBS Greek 1.0 lexical crosswalk | [Committed source baseline](links/dictionaries/ubs-greek/index.json); full private evidence index **not** tracked | [Greek word-ID crosswalk v0.1.0](https://github.com/icfmp/Bible-Resources/releases/tag/bsi-ubs-greek-v0.1.0), `BSI-UBS-Greek-0.1.0.zip` containing `index.json` |
| UBS Hebrew 0.9.4 lexical crosswalk | [Committed source baseline](links/dictionaries/ubs-hebrew/index.json); additional verified word-specific reviews are reproducible from Git | [Hebrew lexical crosswalk v1.0.0](https://github.com/icfmp/Bible-Resources/releases/tag/bsi-ubs-hebrew-v1.0.0), `BSI-UBSHebrew-0.9.4-v1.0.0.zip` containing `index.json` |

**Important:** the committed dictionary `index.json` files are *baseline
crosswalks*, not identical to their published versions or all intermediate
editorial candidate overlays. All official versioned release ZIPs are stored
as durable **GitHub Release assets**, not scattered across source folders.
Download the named ZIP and examine its manifest/attribution to identify the
exact distributed schema and version. A GitHub Actions artifact under
`/tmp/` or `dist/` is **temporary build output**, not the permanent index.
Nothing is automatically exported to the Bible application.

**Working-state preservation:** source-verified complete internal states are
different from the published and source-baseline indexes. The new
[private working-state archive procedure](work/README.md) covers the entity,
Greek and Hebrew streams, with commit-locked manifests, SHA-256 checks and
private-only immutable GitHub Release storage. **The archiving destination
must first be configured; no durable private backup is claimed before the
private repository exists and an actual archive is uploaded/read back.**

## Directory map

```text
bible-semantic-index/
├── README.md            Project entrypoint and index locations
├── docs/                BSI release decisions, editorial background and methods
├── scripts/             Shared BSI entity builder, resolver and packaging
├── tests/               Regression tests for shared BSI tooling
├── data/                Source locks, reviewed editorial decisions and evidence
├── sources/             Pinned ACAI checkout procedure; downloaded originals ignored
├── work/                Private working-state archive policy and recovery instructions
└── links/
    ├── schema.v1.json   Reviewed link schema
    ├── dictionaries/
    │   ├── ubs-greek/   Greek pinned dictionary pipeline and its tests
    │   └── ubs-hebrew/  Hebrew pinned dictionary pipeline and its tests
    └── encyclopedias/   Future independently licensed links
```

Dictionary-specific scripts and tests intentionally remain *inside their
own dictionary directory*: their pinned source, exact reviewed decisions,
regression fixtures and source-pinned workflows form a single reproducible
unit. They are **not shared generic scripts**. Do not move or delete them
based on filenames alone; follow tested callers and the immutable releases.

## Rebuild and verification

Fetch the frozen ACAI data **without editing it**, then generate a private
index into ignored build output:

```bash
bash bible-semantic-index/sources/checkout-acai.sh
python3 -I bible-semantic-index/scripts/compile_index.py \
  --source bible-semantic-index/sources/checkouts/acai \
  --verify-source-commit \
  --output bible-semantic-index/dist/index.json
```

The [BSI source-pinned GitHub Actions workflow](
../.github/workflows/entity-index.yml) runs shared offline tests plus full
original-data build verification. Each UBS dictionary has its own pinned
source workflow; see [UBS Greek](links/dictionaries/ubs-greek/README.md)
and [UBS Hebrew](links/dictionaries/ubs-hebrew/README.md).

**Editorial policy:** lexical identity is not proof of a contextual sense.
Keep alternative valid candidates, attest source and edition, record
reversible decisions, abstain where sources remain uncertain. Do not alter
original scripture, Strong/LN/SDBH or source dictionary entries.
