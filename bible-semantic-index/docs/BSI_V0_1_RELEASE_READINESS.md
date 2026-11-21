# Bible Semantic Index (BSI) — v0.1 release readiness

**Status: PUBLISHED 2026-11-18** — [Bible Semantic Index v0.1.0](https://github.com/icfmp/Bible-Resources/releases/tag/bsi-v0.1.0). Key Terms are excluded from this version. This page preserves the preparation evidence and release criteria; see [the scoped rights audit](BSI_V0_1_RIGHTS_AUDIT.md).

## Identity and scope

- **Public-facing name:** Bible Semantic Index (**BSI**).
- **Technical workspace (unchanged for compatibility):** `bible-semantic-index/`.
- **Purpose:** offline, original-language word-ID anchored lookup of biblical people, places, groups, flora, fauna, realia and (when cleared) concepts.
- Source ACAI is a preserved frozen **historical witness**, not the name or sole authority of BSI.
- Already validated Macula word IDs should be reused, never reindexed by fuzzy spelling, Strong number or inferred token alignment.
- Index-to-dictionary linking is a *separate, later* lexicon-mapping concern: Macula lemma/Strong references may support it, but dictionary editions, homographs and contextual senses require validation; no universal automatic dictionary join is claimed.

## What the current compiled index includes or excludes

The generated index retains entity IDs/canonical IDs, original word ID groups, Bible reference claims, link types, editable provenance, editorial decisions and inverse word lookup. It excludes ACAI localizations (including names), narrative descriptions, biographies, speeches, encyclopedia text, coordinates and speculative genealogies. The immutable 6,644-file ACAI source witness is not changed.

The internal index intentionally contains no display-name layer. The new `minimal_labels.py` generates a **separate** English-only preferred-label candidate from the exact ACAI source files, enforcing each original SHA-256, without copying descriptions or other localizations. The labels are marked `source_unreviewed_label`; an ambiguous name such as Mary does **not** assert a unique identity. Human editorial acceptance and attribution remain required before describing this as a reviewed reader-label layer.

## Rights audit — evidence and decisions still required

| Material | Evidence | Distribution decision |
| --- | --- | --- |
| ACAI-derived identities, source references and original-word associations | Frozen ACAI `README.md` declares its JSON/Markdown release CC BY-SA 4.0, copyright 2025 Mission Mutual; `LICENSE.md` names BiblioNexus and CC BY-SA 4.0 | **Conditional**: preserve attribution, license link, source revision, changes notice and ShareAlike in the eventual redistributed BSI derivative |
| Macula Hebrew and Greek linguistic data | Exact pinned source editions declare CC BY 4.0 with source-specific attribution | Preserve required attribution and exact edition; current BSI index copies word identifiers, not the Macula biblical word text |
| UBS Dictionary data and UBS thematic Flora/Fauna/Realia | ACAI source README cites open UBS datasets; independently verify the precise upstream files and applicable notices before reusing third-party content | **Review required** for any content reused from UBS; Key Terms are excluded from the BSI v0.1 distribution profile |
| UBS Paratext Key Term material | Frozen ACAI README explicitly states “used by permission” | **OUT OF SCOPE for v0.1**. All keyterm records and their inverse lookup links are excluded by the deterministic distribution projection, regardless of the eventual legal position |
| Human-readable display labels | Original ACAI preferred labels are in excluded `localizations` | **Not available** in current compiled artifact; choose and clear a minimal verified multilingual/neutral name source without reinstating biographies |

**Important:** removing the `keyterms` entries from a JSON artifact by hand is not an adequate rights-clearing strategy. The new `distribution_profile.py` generates a separate keyterm-free output while preserving the original compiled QA index. It excludes records and their inverse `by_word`, quarantined, absent-word/verse, and qualified-reference links. CI checks this projection against a full pinned build. This is a technical exclusion, **not** independent legal clearance of the remaining fields. The internal unrestricted compiled witness and its full integrity audit must remain unchanged. Rights review must establish whether any other categories contain restricted third-party annotations.

## Decision: defer Key Terms

Key Terms are **not used in BSI v0.1**, are **not shipped**, and may be independently curated in a later version rather than copied from permission-based Paratext data. This decision does **not** remove or rewrite ACAI's historical source or its full internal QA index.

Build the projected candidate after a successful original full-index build:

```bash
python3 -I bible-semantic-index/scripts/distribution_profile.py \
  --input bible-semantic-index/dist/index.json \
  --output bible-semantic-index/dist/bsi-v0.1-without-keyterms.json
```

The file is a *candidate distribution projection* for reproducible builds; the **published** release is the archived, checked ZIP linked above. The minimal label file comes from the pinned, SHA-verified English `preferred_label` field only:

```bash
python3 -I bible-semantic-index/scripts/minimal_labels.py \
  --source /path/to/pinned-ACAI \
  --index bible-semantic-index/dist/bsi-v0.1-without-keyterms.json \
  --output bible-semantic-index/dist/bsi-v0.1-labels-en.json
```

The reproducible candidate ZIP additionally includes the derived index, these labels, the exact source lock, a file-hash manifest and attribution notices:

```bash
python3 -I bible-semantic-index/scripts/package_candidate.py \
  --index bible-semantic-index/dist/bsi-v0.1-without-keyterms.json \
  --labels bible-semantic-index/dist/bsi-v0.1-labels-en.json \
  --lock bible-semantic-index/data/source.lock.json \
  --output bible-semantic-index/dist/BSI-0.1.0-RELEASE-CANDIDATE.zip
```

A successful artifact upload in CI remains an **internal candidate**, never a GitHub Release. Actual release bytes must be independently verified, attributed and approved for redistribution.

## Required gates before public release

- [x] Document a scoped upstream field-level licensing review in [BSI_V0_1_RIGHTS_AUDIT.md](BSI_V0_1_RIGHTS_AUDIT.md), excluding permission-only Key Terms. This is a documented license-scope review, not legal advice.
- [x] Implement a separate deterministic projection excluding **all keyterms**; CI was green on merged PR #345; archive-level validation remains required on the packaging revision. Recheck rights in remaining categories independently.
- [x] Implement minimal **source-hash-checked, English-only label extraction** in a separate candidate artifact, with provenance and unreviewed labeling; CI was green on merged PR #345; labels remain source-unreviewed, not editorially certified.
- [x] Rebuilt on merged `main` commit `4b45f384c3769431a2e761573cef14554a16b044` in the [successful publishing workflow](https://github.com/icfmp/Bible-Resources/actions/runs/44305997133), checked index parity and ZIP readback.
- [x] Implement a reproducible candidate ZIP generator with attribution, excluded-feature notice, version, source lock and member/archive SHA-256; archive CI must pass before release.
- [x] GitHub Release [bsi-v0.1.0](https://github.com/icfmp/Bible-Resources/releases/tag/bsi-v0.1.0) published with `BSI-0.1.0.zip` (1,867,962 bytes; SHA-256 `3685b09b157f89c42f7766c4f42cf7d5c9fe1e8cde153c8f633afc7a6d2d4c41`) and portable checksum receipt. App integration remains separate.

## Traceability

- Existing internal candidate: [V0_1_CANDIDATE_HANDOFF.md](V0_1_CANDIDATE_HANDOFF.md)
- Acceptance: issues [#337](https://github.com/icfmp/Bible-Resources/issues/337), [#338](https://github.com/icfmp/Bible-Resources/issues/338)
- Open publication rights issue: [#339](https://github.com/icfmp/Bible-Resources/issues/339)
- Historic ACAI audit tracker [#299](https://github.com/icfmp/Bible-Resources/issues/299) is **not** a requirement to resolve all indirect pronoun conflicts before a bounded v0.1 release.
