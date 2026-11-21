# Bible Semantic Index v0.1 — historical internal candidate handoff

This document preserves the **historical internal QA-candidate evidence** as originally recorded. Since then, the independent, keyterm-free [BSI v0.1.0 data artifact has been published](https://github.com/icfmp/Bible-Resources/releases/tag/bsi-v0.1.0). The full unfiltered internal index remains QA-only; this historical handoff is not itself the release manifest. Tracked in completed [#339](https://github.com/icfmp/Bible-Resources/issues/339).

## Reproducible candidate and observed gates

- Existing compilation: `bible-semantic-index/scripts/compile_index.py` builds `dist/index.json` from an exact **frozen** ACAI checkout and a deterministic `../data/editorial-decisions.json`.
- Input: `icfmp/ACAI@e80a874e8282f996199c595378a3b3b9a43aac22`, original **6,644** JSON records. SHA-256 source snapshot `e46fa575d6d9946afe9b63a4ed64f4202cbe50f5a61bf855fad655d33259c084`, locked by `../data/source.lock.json`.
- Source word editions (exact): Macula Hebrew `47db250bd55d0d8577f2a94fba114ef16c35b23c` / Macula SBLGNT Greek `8423afe47b9e8f24b7772e808af45c7159a6fe7e`.
- Latest relevant reviewed-content revision: merged #342, Git commit `4158415b043698636e32c411134d93ec4119312b` (document-only change since data-correction batch).
- **Full index integrity** [Actions run #44294944281](https://github.com/icfmp/Bible-Resources/actions/runs/44294944281): SUCCESS. Pinned **134,822** active source-language original-word IDs verified source-present. QA-only artifact `independent-entity-index-qa` (artifact ID `14421864739`), ZIP SHA-256 `6eb0cb80b144ff19829bc466fc6e72f2889050c25bf39735b7b1007da7d65a87`. This digest identifies the downloaded **artifact ZIP**, not the independent `index.json` file hash. Artifact scheduled expiration: **2026-12-02**; never treat a temporary workflow artifact as a permanent release URL.
- Whole-repository [Validate #44294944190](https://github.com/icfmp/Bible-Resources/actions/runs/44294944190): SUCCESS. Existing v0.1 source-linked reader smoke checks: **16/16** representative `flora`, `fauna`, `realia`, `keyterm` direct word IDs from [#341](https://github.com/icfmp/Bible-Resources/pull/341). Twenty-four previously source-reviewed direct-name and variant cases: [the v0.1 named sample](V0_1_NAME_PILOT.md).

These checks demonstrate **implementation and source-word parity**, not full semantic certification of 6,644 biblical entity records.

## Consumer contract for the Bible application

1. **Only original-language word-level lookups** from one of the exact pinned source editions. Use `(corpus, edition, word_id, verse_id)`; do not guess or derive original word IDs from Strong numbers, French translation tokens or identical surface spelling.
2. The reader calls `EntityResolver.resolve_for_reader(...)` from [resolve.py](../scripts/resolve.py), never the unrestricted raw `resolve()`. The reader-facing result has `lookup_policy=explicit_only`, with source-linked `explicit_instances` only. No automatic person cards on `we`, `you`, `they`, pronouns, implied grammatical subjects or unverified participant cohorts.
3. **Candidate statuses are not editorial guarantees.** `source_candidate` means one or more source records that lead to one canonical entity; `ambiguous_source_candidates` means multiple distinct canonicals; `no_explicit_entity` means only indirect evidence; `no_indexed_entity` means no candidate; missing/wrong edition and original-word/verse mismatch remain separate fail-closed statuses.
4. Preserve source IDs, canonical IDs, `review_status`, link types and provenance. Never render a `source_unreviewed` hit as historically certain. Multiple individuals, regions and family/genealogical name components can share an original word legitimately; do not silently pick the first result.
5. The currently compiled index **does not contain** ACAI `localizations` (preferred labels), biographical descriptions or speech prose. Bible needs a **separately reviewed, rights-cleared display-label layer** (or an expressly qualified ID fallback) before a friendly reader UI can be claimed. Do not invent public-facing names from `person:Mary.2` identifiers.
6. Data is entirely offline at consumption time, with **no runtime dependency on ACAI, Macula or external APIs**. The current JSON index is not yet an SWORD module, and no Bible application integration has been tested under this issue.

## Redistribution rights: source declarations and remaining gate

- The frozen ACAI [LICENSE.md](https://github.com/icfmp/ACAI/blob/e80a874e8282f996199c595378a3b3b9a43aac22/LICENSE.md) explicitly declares **CC BY-SA 4.0** for ACAI Biblical Entity Data, naming BiblioNexus; the [ACAI README](https://github.com/icfmp/ACAI/blob/e80a874e8282f996199c595378a3b3b9a43aac22/README.md) identifies its JSON/Markdown release as CC BY-SA 4.0 and credits Mission Mutual. Any redistributed adaptation requires attribution, license link, modifications notice and ShareAlike terms, without further restrictions.
- Pinned [MACULA Hebrew LICENSE.md](https://github.com/Clear-Bible/macula-hebrew/blob/47db250bd55d0d8577f2a94fba114ef16c35b23c/LICENSE.md) and [MACULA Greek LICENSE.md](https://github.com/Clear-Bible/macula-greek/blob/8423afe47b9e8f24b7772e808af45c7159a6fe7e/LICENSE.md) declare **CC BY 4.0** for their datasets and specify attribution: *MACULA Hebrew Linguistic Datasets, available at https://github.com/Clear-Bible/macula-hebrew/*, and *MACULA Greek Linguistic Datasets, available at https://github.com/Clear-Bible/macula-greek/*.
- The output intentionally excludes the original biblical word text, speech text, biographies, geography and multilingual description prose. It currently retains ACAI's entity identity structure, original-word pointers, source-record hashes and source reference claims, so **ACAI derivative rights and attribution still apply** even when the original JSON itself is not copied.
- **Open third-party data risk:** ACAI's source README says UBS *Key Term* data from Paratext is **“used by permission”**; MACULA licenses also mention some UBS semantic material used by permission. Their blanket dataset licenses do not, by themselves, prove every upstream third-party right relevant to a downstream redistributed derivative. Before shipping `keyterms` or other possibly inherited third-party classifications, confirm that this exact **word ID ↔ entity ID** subset is covered for redistribution or exclude the affected material safely from a separate, well-described distribution variant. No assumptions about rights are made from public source accessibility alone.
- This internal receipt is **not** a legal sign-off. No release, GitHub Pages catalogue entry, app package, SWORD resource or automatic download is approved.

## Remaining decisions before publication

- [ ] Close the provenance/third-party reuse uncertainty for the **actual derivative fields** to be redistributed, in particular the keyterm relation data. Retain written source evidence or a safely scoped exclusion.
- [ ] Decide and validate the **display-label** source and attribution (the current index deliberately lacks friendly names).
- [ ] Test a real pinned original-language reader selection end-to-end in application Bible, including a direct name, a common-noun topic, a genuine direct ambiguity and a pronoun with **no** card.
- [ ] Produce a nonexpiring, independently hashed and appropriately attributed release candidate from the already reviewed tools, with source/edition/version rollback metadata.
- [ ] Obtain **explicit project-owner approval** before public distribution or publishing in the Bible catalogue. Technical test success is **not** publication authorization.

The ongoing historical ACAI audit continues in [#299](https://github.com/icfmp/Bible-Resources/issues/299), but the 2,332 indirect-only person overlaps are **not** a v0.1 publication gate once the reader ignores that evidence. This handoff keeps the first-version scope finite and honest.
