# Louis Segond 1910 — reader-facing resource profile

**DRAFT — NOT APPROVED FOR APP/CATALOGUE PROFILE PUBLICATION**

**Important distinction:** Bible Resources' SWORD module `BRLSG1910` **version 0.1.0 is already published and owner-approved as an initial reading edition**. This separate descriptive profile has *not* received final editorial approval. Its draft status does not revoke or alter that release.

## Proposed concise reader card

- **Title:** Louis Segond 1910
- **Language:** French (`fr`)
- **Category:** Bible; 66-book Protestant canon
- **Work:** Louis Segond's French translation of the Hebrew and Greek Scriptures, in the **posthumously revised 1910 edition** issued by the British and Foreign Bible Society. The 1910 editors must not be presented as Louis Segond himself.
- **Curated module:** `BRLSG1910` version `0.1.0` (Bible Resources)
- **Versification:** SWORD `Segond` (standard installed registry)
- **Reader introduction (`fr`, draft):** « La Bible Louis Segond 1910 est une édition révisée, publiée après la mort de Louis Segond, de sa traduction française de l'Ancien et du Nouveau Testament. Cette traduction historique, réalisée d'après l'hébreu et le grec, est proposée ici à partir de la source numérique eBible. Certaines particularités de présentation et de numérotation sont documentées ; le module n'est pas certifié identique à un exemplaire imprimé de 1910. »
- **Strengths (factual candidates; pending approval):** Original translation from Hebrew and Greek (1910 title page); historically identifiable revised edition (1910 title and preface); underlying text declared public domain by eBible. These are documented features, not a ranking of translation accuracy.
- **Points of attention (draft):** The edited 1910 text is not identical to Segond's unrevised work; this digitized SWORD release has the evidenced verse-index and layout limitations below. No theological rating is proposed.

## Three distinct provenance layers

| Layer | Attested identity and provenance | Limitation |
|---|---|---|
| Original work and edition | Louis Segond's translation, **1910 posthumously revised edition**, Paris, British and Foreign Bible Society; printed title and preface verified below | Exact word-for-word and typographical equivalence of the eBible digitization to the scanned 1910 printing has **not** been certified |
| Acquired source | eBible `fraLSG`, publisher revision identified in the curated metadata as `2026-10-29`; source details and source hashes are recorded in the [release note](../releases/LSG-0.1.0.md) | Do not treat eBible's separately compiled NRSV-indexed SWORD package as the same curated binary |
| Curated edition | Bible Resources `BRLSG1910` `0.1.0`, standard SWORD `RawText`, `OSIS` SourceType, `Segond` versification; [editorial record](../../modules/lsg-1910/EDITORIAL.md), [approved release](https://github.com/icfmp/Bible-Resources/releases/tag/lsg-0.1.0) | First, provisional publication; not exhaustive source-to-printed-page certification |

**Rights:** eBible identifies the underlying translation as [Public Domain](https://ebible.org/fraLSG/copyright.htm). The rights and separate editorial approval of the curated resource are in [module metadata](../../modules/lsg-1910/metadata.json). That declaration does not independently authorize unrelated lexical enrichment, commentary or annotations.

## Original 1910 printed-edition evidence (primary witness)

- **Title page:** *La Sainte Bible ... par Louis Segond, docteur en théologie. Nouvelle édition revue avec parallèles*, Paris, 1910. [Digitized facsimile, printed page 1](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/1); [full facsimile metadata](https://fr.wikisource.org/wiki/Fichier:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu).
- **Publisher's original preface:** the [1910 *Avertissement*, printed page 3](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/3) dates the original Old Testament and New Testament publications to 1873 and 1880 respectively, describes Segond's 1880 permission for posthumous editing, and attributes the proposed corrections to pastors and theology professors from France and Switzerland acting at the Society's request. It does **not** name every reviser.
- **Editorial context, not an accusation:** the same 1910 preface states that its editors omitted certain earlier notes, including notes expressing theological opinions or commentary, consistent with the Society's editorial policy. It also explains the newly emphasized parallel-reference apparatus. This describes the **printed 1910 edition**, not a proven loss of particular notes during eBible→SWORD conversion.
- **Limit of this witness:** a scan of a 1910 printing establishes its title and what its editors said; it does **not** establish complete character-by-character equivalence between that printing, eBible's `fraLSG` transcription and the curated `BRLSG1910` module. They remain separate provenance layers.

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
- [x] Confirm 1910 title page and *Avertissement* against a printed-edition facsimile; identify this as a posthumous revision and do not assume named individual revisers
- [ ] Verify any more specific named-editor/revision attributions before publishing them
- [ ] Approve or reject the source-backed concise factual strengths
- [ ] Review contested variants with appropriate scholarly/primary material
- [ ] **Owner editorial approval pending:** approve reader-facing French introduction and each visible strength/caution separately from module `quality.status`
- [ ] Decide how the application/catalogue represents approved profile revisions and retains attribution offline

**Editorial rule:** the already-published 0.1.0 Scripture and its immutable release hashes are not changed by edits to this profile. See [resource profile evidence policy](../RESOURCE_PROFILES.md).
