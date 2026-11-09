# Louis Segond 1910 — reader-facing resource profile

**DRAFT — NOT APPROVED FOR APP/CATALOGUE PROFILE PUBLICATION**

**Important distinction:** Bible Resources' SWORD module `BRLSG1910` **version 0.1.0 is already published and owner-approved as an initial reading edition**. This separate descriptive profile has *not* received final editorial approval. Its draft status does not revoke or alter that release.

## Proposed concise reader card

- **Title:** Louis Segond 1910
- **Language:** French (`fr`)
- **Category:** Bible; 66-book Protestant canon
- **Work:** A French Protestant translation associated with Louis Segond; the 1910 revision must not be represented as his original unrevised text
- **Curated module:** `BRLSG1910` version `0.1.0` (Bible Resources)
- **Versification:** SWORD `Segond` (standard installed registry)
- **Reader introduction, draft:** A historical French Protestant Bible made available as a standard SWORD module. Bible Resources' first curated release retains the eBible source text and explicitly documents formatting and verse-index compromises. It is suitable for ongoing reading and review, but not certified as typographically identical to a particular printed copy.
- **Strengths:** No editorially approved strengths have been added to the reader card yet.
- **Points of attention:** See evidenced technical limitations below; this draft does not propose a theological rating.

## Three distinct provenance layers

| Layer | Attested identity and provenance | Limitation |
|---|---|---|
| Original work and edition | Louis Segond 1910, French | Precise 1910 printed-edition comparison and editorial history are not certified |
| Acquired source | eBible `fraLSG`, publisher revision identified in the curated metadata as `2026-10-29`; source details and source hashes are recorded in the [release note](../releases/LSG-0.1.0.md) | Do not treat eBible's separately compiled NRSV-indexed SWORD package as the same curated binary |
| Curated edition | Bible Resources `BRLSG1910` `0.1.0`, standard SWORD `RawText`, `OSIS` SourceType, `Segond` versification; [editorial record](../../modules/lsg-1910/EDITORIAL.md), [approved release](https://github.com/icfmp/Bible-Resources/releases/tag/lsg-0.1.0) | First, provisional publication; not exhaustive source-to-printed-page certification |

**Rights:** eBible identifies the underlying translation as [Public Domain](https://ebible.org/fraLSG/copyright.htm). The rights and separate editorial approval of the curated resource are in [module metadata](../../modules/lsg-1910/metadata.json). That declaration does not independently authorize unrelated lexical enrichment, commentary or annotations.

## Evidence-backed technical observations

### `segond1910-merged-mark-index` — Mark 10:52–53

- **Category:** `technical`
- **Observation:** The acquired eBible authoring source contains Mark 10:52 and 10:53. Released standard SWORD `Segond` has no distinct Mark 10:53 key. Both source verse bodies are preserved in a **single** reader entry at Mark 10:52, through a source-bound owner-approved, reversible compromise.
- **Evidence:** [published release notes](../releases/LSG-0.1.0.md), [editorial decisions](../../modules/lsg-1910/EDITORIAL.md) and [original stock-SWORD audit](../../modules/lsg-1910/SOURCE_AUDIT.json).
- **Status:** Substantiated and disclosed in the approved 0.1.0 *release*. This draft reader-card wording is not independently approved for app display.
- **Caveat:** Some readers display only 52 rather than the preferred combined label 52–53. This is not evidence of deleted biblical words.

### `segond1910-job-empty-index` — Job 34:37

- **Category:** `technical`
- **Observation:** The selected SWORD registry has an available Job 34:37 slot but the original acquired eBible authoring source has no distinct authored verse there. The project does not invent a verse or repurpose neighbouring text.
- **Evidence:** [release notes](../releases/LSG-0.1.0.md), [source/reader index audit](../../modules/lsg-1910/SOURCE_AUDIT.json).
- **Status:** Substantiated in the published technical release notes; no editorial explanation of *why* the source differs from a particular printed edition is asserted.

### `segond1910-original-ebible-module-v11n` — upstream SWORD differences

- **Category:** `technical`
- **Observation:** The acquired source and the original eBible SWORD packaging must not be assumed to use the same verse indexing; the project's module uses `Segond` instead of the upstream package's reported `NRSV`.
- **Evidence:** [source-level discrepancy investigation](https://github.com/icfmp/Bible-Resources/issues/26), [release evidence](../releases/LSG-0.1.0.md).
- **Status:** Technical packaging finding; **not** an accusation about Segond's translation choices.

## Open research, not a published caution

### `segond1910-1tim316` — 1 Timothy 3:16

- **Category:** `textual_variant` / `translation`
- **Research question:** Which underlying Greek reading is reflected in this exact source and edition, and how does that compare with editions of the Textus Receptus and modern critical texts?
- **Required evidence:** Exact LSG 1910 passage, edition's own notes and documented manuscript/critical apparatus; attributable primary or scholarly sources; comparisons with correctly identified editions and representative counterexamples.
- **Status:** `candidate` only. **No claim of deliberate doctrinal suppression, systematic translator bias, or motive is substantiated or approved.**

## Pending editorial review of this profile

- [x] Curated SWORD 0.1.0 release identity, source hashes, rights evidence and first-publication review linked
- [x] Documented, reader-relevant versification limitations separated from theological claims
- [ ] Confirm historical printed-edition attribution and exact editorial/reviser history with primary evidence
- [ ] Approve concise strengths with edition-specific sources, if any
- [ ] Review contested variants with appropriate scholarly/primary material
- [ ] Approve reader-facing summary and all displayed cautions separately from module `quality.status`
- [ ] Decide how the application/catalogue represents approved profile revisions and retains attribution offline

**Editorial rule:** the already-published 0.1.0 Scripture and its immutable release hashes are not changed by edits to this profile. See [resource profile evidence policy](../RESOURCE_PROFILES.md).
