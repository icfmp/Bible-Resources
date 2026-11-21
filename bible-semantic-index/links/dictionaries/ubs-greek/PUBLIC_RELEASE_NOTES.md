# Bible Semantic Index — UBS Greek NT word-level crosswalk v0.1.0

**Standalone, offline, identifier-only crosswalk** based on the original MACULA
SBLGNT word IDs and the UBS Dictionary of the Greek New Testament 1.0
English/French lexical entry/sense identifiers.

## Coverage and uncertainty

- **137,741** source word IDs, all explicitly classified.
- **137,694 (99.966%)** original words have source-supported UBS lexical
  entries; 47 have no sufficiently supported UBS entry.
- **123,195 (89.44%)** have a **provisional** original UBS sense-ID
  recommendation, based on five independently verified kinds of source
  evidence. These are **not 123,195 independently validated contextual
  interpretations**.
- **12,288** offer only a lexical entry, **2,207** preserve multiple genuine
  candidate UBS senses, **4** preserve multiple lexical entry candidates,
  and **47** have no approved lexical mapping.
- The intentionally unresolved 14,546 words are **not guessed at**.

## Public archive

- `BSI-UBS-Greek-0.1.0.zip`: deterministic JSON lookup (`index.json`),
  machine-readable manifest with SHA-256, README and attribution.
- `BSI-UBS-Greek-0.1.0.zip.sha256`: SHA-256 of the archive.

No Greek biblical text, lemma, Strong/Louw–Nida annotations, morphological
annotations, commentary, translations, or UBS dictionary definitions are
redistributed. The archive contains only MACULA original word identifiers,
source UBS entry and candidate sense **identifiers**, qualified evidence
levels, and transparent fallback statuses. No network is needed to use it;
this is **not** a SWORD dictionary module and has **not** been integrated
into the Bible app.

## License, source citations and modifications

The new index is distributed **CC BY-SA 4.0** with source attribution and
documented transformations in the archive's `ATTRIBUTION.md`.

Original UBS Greek Dictionary © United Bible Societies (2023), CC BY-SA
4.0. Original MACULA Greek Linguistic Datasets © 2022–2024 Biblica, Inc.,
CC BY 4.0 (hosted by Clear-Bible). Source citations, frozen commits and
original upstream license links are included in `ATTRIBUTION.md`.
The original MACULA license identifies some third-party datasets,
including UBS MARBLE annotations used with permission; **those annotations
and fields are deliberately not shipped**. This identifier-only release
must not be represented as a license to redistribute any of those other
sources or their definitions.

### Source locks

- UBS Greek NT Dictionary 1.0 EN/FR:
  `a15a96cfaa4ca18a6c0339016645ba1e534db3c8`
- MACULA Greek SBLGNT:
  `8423afe47b9e8f24b7772e808af45c7159a6fe7e`

See the [reproducible source-pinned builder and documentation](https://github.com/icfmp/Bible-Resources/tree/main/bible-semantic-index/links/dictionaries/ubs-greek).
