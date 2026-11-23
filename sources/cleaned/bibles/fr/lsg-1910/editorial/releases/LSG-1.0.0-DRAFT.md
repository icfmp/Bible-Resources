# Louis Segond 1910 — 1.0.0 build candidate (NOT PUBLISHED)

**Owner direction, 23 November 2026:** prepare **1.0.0**, not 0.1.1. This document records an isolated, reproducible candidate build; it is **not** an approved publication plan, a release tag, or a new cleaned-master approval.

## Immutable input / exact source identity

- Publisher: eBible `fraLSG`; original USFX ZIP SHA-256 `fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e`.
- Former approved cleaned OSIS SHA-256 `d6abd7416d026c86ce2e9577e3bfe7a10159c5c78d236913359c7fab013449d0`. It remains unchanged until explicit approved replacement. This former state is also preserved in Git history.
- Reviewed, source-pinned, individually linked OSIS 1.0.0 **candidate** SHA-256 `1eb474496bef0388da403528ea080da489d8b4d980d4b11397ffd8cfe2398a4d`.
- [PR #543](https://github.com/icfmp/Bible-Resources/pull/543) merged (advisory BRNP subset); [PR #544](https://github.com/icfmp/Bible-Resources/pull/544) merged (reproducible cross-reference correction evidence); [PR #542](https://github.com/icfmp/Bible-Resources/pull/542) closed unmerged (old 0.1.1 display-only proposal superseded).
- [Tracking issue #545](https://github.com/icfmp/Bible-Resources/issues/545).

## Approved reviewed candidate scope

- 12 documented electronic reference-fragment substitutions, independently source-checked against historical marginal tokens and constrained to exact source note indices.
- Philippians and First John: structural links only, exact source prose unchanged. Titus: the electronic intro typo `1:1-40` → `1:1-4` corrected in the separately reviewed candidate.
- 9,440 of 9,751 original digital notes contain complete source-attested links. The remaining 311 remain visible and unlinked rather than guessed.
- 29,687 linked reference elements; 29,866 link endpoints, all valid in the **original authoring OSIS source**; original verse content and order unchanged.
- New candidate SWORD internal ID `BRLSG1910`; display name `Louis Segond 1910`, abbreviation `LSG1910`, `Version=1.0.0`. The workflow compiles **fresh zText** from the edited reviewed OSIS, not the obsolete 0.1.0 RawText data or the never-published 0.1.1 proposal.

## Known SWORD compatibility blocker

The exact source has **31,170** verse IDs including `Mark.10.53`. Released stock SWORD `Segond` has **31,169 independently populated verse addresses**; the text of `Mark.10.53` is included under `Mark.10.52`. The source has **no `Job.34.37`** and it must not be invented.

The owner accepts Xiphos as the provisional reader for development. This does **not** establish independent GUI test evidence, full source-native key parity, JSword support or final publication approval. The candidate ZIP is therefore explicitly **not a distribution release**. Final release must state the mismatch clearly or use an independently verified supported versification providing exact source addressability, without changing original authored verse IDs.

## Reproducible build and release acceptance

The dedicated [GitHub Actions preview workflow](../../../../../../../.github/workflows/lsg-v1-reviewed-candidate.yml) executes all already-reviewed independent source transformations, binds the final XML SHA-256, validates the official OSIS schema and real references, compiles a **new** stock-SWORD zText module with `osis2mod`, reads back the entire native index, and produces a deterministic **preview-only** ZIP and its exact source/member hashes. Preview artifacts are temporary, not public assets.

Before creating a real release plan under `config/release-plans/lsg-1.0.0.json`, replacing the approved cleaned master or changing the catalogue: retain the exact generated module source and native compile receipts, independently verify all notes and verse text in the compiled package, reconcile the stock-SWORD versification exception, prepare the new source validation/manifests and published reader profile, obtain owner review and run the complete production publication gates. No package checksum or source validation is to be invented from intent.

**Release status: NOT YET AUTHORIZED; NO RELEASE TAG, NO PUBLIC MODULE OR CATALOGUE MODIFICATION.**
