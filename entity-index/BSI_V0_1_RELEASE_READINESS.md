# Bible Semantic Index (BSI) — v0.1 release readiness

**Status: NOT RELEASED.** This document records the adopted project name and the specific publication gates. It does not grant redistribution permission or assert that all source-derived material is cleared.

## Identity and scope

- **Public-facing name:** Bible Semantic Index (**BSI**).
- **Technical workspace (unchanged for compatibility):** `entity-index/`.
- **Purpose:** offline, original-language word-ID anchored lookup of biblical people, places, groups, flora, fauna, realia and (when cleared) concepts.
- Source ACAI is a preserved frozen **historical witness**, not the name or sole authority of BSI.
- Already validated Macula word IDs should be reused, never reindexed by fuzzy spelling, Strong number or inferred token alignment.
- Index-to-dictionary linking is a *separate, later* lexicon-mapping concern: Macula lemma/Strong references may support it, but dictionary editions, homographs and contextual senses require validation; no universal automatic dictionary join is claimed.

## What the current compiled index includes or excludes

The generated index retains entity IDs/canonical IDs, original word ID groups, Bible reference claims, link types, editable provenance, editorial decisions and inverse word lookup. It excludes ACAI localizations (including names), narrative descriptions, biographies, speeches, encyclopedia text, coordinates and speculative genealogies. The immutable 6,644-file ACAI source witness is not changed.

The current index has **no validated reader-friendly display-name layer**. A label fallback to `person:Mary.2` is not equivalent to a verified name. Prepare and license an explicit, independently reviewed label layer before a reader-facing release.

## Rights audit — evidence and decisions still required

| Material | Evidence | Distribution decision |
| --- | --- | --- |
| ACAI-derived identities, source references and original-word associations | Frozen ACAI `README.md` declares its JSON/Markdown release CC BY-SA 4.0, copyright 2025 Mission Mutual; `LICENSE.md` names BiblioNexus and CC BY-SA 4.0 | **Conditional**: preserve attribution, license link, source revision, changes notice and ShareAlike in the eventual redistributed BSI derivative |
| Macula Hebrew and Greek linguistic data | Exact pinned source editions declare CC BY 4.0 with source-specific attribution | Preserve required attribution and exact edition; current BSI index copies word identifiers, not the Macula biblical word text |
| UBS Dictionary data and UBS thematic Flora/Fauna/Realia | ACAI source README cites open UBS datasets; independently verify the precise upstream files and applicable notices before reusing third-party content | **Review required**, do not assume one license covers every category and field |
| UBS Paratext Key Term material | Frozen ACAI README explicitly states “used by permission” | **BLOCKED** for public redistribution of potentially derived keyterm classifications and word-to-concept links until transferable license/permission and exact provenance are demonstrated; alternatively create a separately tested distribution output that excludes affected data and derived references |
| Human-readable display labels | Original ACAI preferred labels are in excluded `localizations` | **Not available** in current compiled artifact; choose and clear a minimal verified multilingual/neutral name source without reinstating biographies |

**Important:** removing the `keyterms` entries from a JSON artifact by hand is not an adequate rights-clearing strategy. A dedicated release profile must exclude every affected record and inverse `by_word` link, preserve counts and source/provenance receipts, be deterministic, and pass existing source/reader checks with explicit scope. The internal unrestricted compiled witness and its full integrity audit must remain unchanged. Rights review must establish whether any other categories contain restricted third-party annotations.

## Required gates before public release

- [ ] Verify upstream provenance and rights at **field level**, including whether `keyterms` or other categories contain permission-only data. Attach dated evidence.
- [ ] Either obtain sufficient downstream authorization, or implement and validate a reproducible **rights-filtered** public distribution profile with explicit coverage exclusions.
- [ ] Prepare a minimal reviewed display-label layer, including provenance and rights.
- [ ] Regenerate from pinned sources on final commit; verify index parity, active-token coverage, category readback and resulting content SHA-256; retain permanent build instructions.
- [ ] Package BSI `v0.1.0` with attribution, license file, excluded-feature disclosure, version/source lock and checksum.
- [ ] Publish only after the above checks pass. App integration is **not owned by this repository** and is not a condition of releasing a properly scoped standalone BSI dataset.

## Traceability

- Existing internal candidate: [V0_1_CANDIDATE_HANDOFF.md](V0_1_CANDIDATE_HANDOFF.md)
- Acceptance: issues [#337](https://github.com/icfmp/Bible-Resources/issues/337), [#338](https://github.com/icfmp/Bible-Resources/issues/338)
- Open publication rights issue: [#339](https://github.com/icfmp/Bible-Resources/issues/339)
- Historic ACAI audit tracker [#299](https://github.com/icfmp/Bible-Resources/issues/299) is **not** a requirement to resolve all indirect pronoun conflicts before a bounded v0.1 release.
