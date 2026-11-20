# Bible Resources — documentation

**Start here:** [Source-first production procedure: original → cleaned OSIS/USFM → fidelity verification → SWORD → readers → release](PRODUCTION_PIPELINE.md).

This is the navigation entry point. File location does not define authority: a historical audit is evidence, not a policy, and a draft experiment is not a published release. Do not move, delete or combine a document until all references from Markdown, GitHub workflows, scripts, tests and historical review links have been checked.

## 1. Core principles and decisions

- [Architecture](ARCHITECTURE.md) · [formats](FORMATS.md) · [workspace layout](WORKSPACE_LAYOUT.md) · [resource index](RESOURCE_WORKSPACE_INDEX.md)
- [Quality policy](QUALITY_POLICY.md) · [editorial rules](EDITORIAL_RULES.md) · [rights](RIGHTS.md) · [versification](VERSIFICATION_POLICY.md)
- [Normalization policy](NORMALIZATION_POLICY.md) · [OSIS semantic fidelity](OSIS_SEMANTIC_FIDELITY.md) · [main text fidelity](MAIN_TEXT_FIDELITY.md)
- [Commentary editorial policy](COMMENTARY_POLICY.md) · [resource profiles](RESOURCE_PROFILES.md) · [source selection priority](SOURCE_PRIORITY.md)

## 2. Workflow — operating instructions

1. **[Canonical production chain](PRODUCTION_PIPELINE.md)**: full editorial/technical evidence contract for original source, cleaning, reviews, compilation, reader tests and publication.
2. [Source-first six-phase policy](SOURCE_FIRST_EDITORIAL_PIPELINE.md): accepted production principles and editorial scope.
3. [Seven-stage Bible checkpoint workflow](BIBLE_7_STAGE_WORKFLOW.md) and [its GitHub Actions runner guide](BIBLE_STAGE_AUTOMATION.md).
4. [Seven-stage commentary checkpoint workflow](COMMENTARY_7_STAGE_WORKFLOW.md) and [commentary pipeline](COMMENTARY_PIPELINE.md).
5. [Editorial audit execution reference](EDITORIAL_AUDIT_WORKFLOW.md) · [commentary translation from cleaned source](COMMENTARY_TRANSLATION_FROM_CLEAN_SOURCE.md). The older LSG-specific [onboarding playbook is archived](archive/RESOURCE_ONBOARDING_PLAYBOOK.md).
6. [Publishing](PUBLISHING.md) · [catalogue integration](CATALOGUE_INTEGRATION.md) · [catalogue update protocol](CATALOGUE_UPDATE_PROTOCOL.md) · [upstream updates](UPDATES.md) · [upstream policy](UPSTREAM.md).

**Six phases vs seven stages:** six phases describe the production lifecycle; seven stages are per-resource checkpoints for evidence and resumption. They are complementary, not separate competing import pipelines.

## 3. Technical inspection and fidelity reference

- Original/native scope: [source inventory](SOURCE_INVENTORY.md), [OSIS inventory](SOURCE_OSIS_INVENTORY.md), [native book scope](SOURCE_NATIVE_BOOK_SCOPE.md), [native main text](SOURCE_NATIVE_MAIN_TEXT.md), [notes](SOURCE_NATIVE_NOTES_AUDIT.md), [index](SOURCE_NATIVE_INDEX_AUDIT.md), [USFX structure](SOURCE_USFX_STRUCTURE.md).
- SWORD checks: [native index inventory](NATIVE_SWORD_INDEX_INVENTORY.md), [native raw witness](NATIVE_SWORD_RAW_WITNESS.md), [whole corpus](NATIVE_SWORD_WHOLE_CORPUS.md), [stable references](STABLE_SWORD_REFERENCE_AUDIT.md), [OSIS paragraph QA](OSIS_PARAGRAPH_RENDERING_QA.md).

## 4. Edition-specific editorial records

**Canonical location:** `sources/cleaned/<type>/<language>/<resource-id>/editorial/`. The [per-resource decisions](../sources/cleaned/README.md) are kept alongside each approved cleaned master and its `CLEANUP_MANIFEST.json`; global rules remain in `docs/`. These records preserve historical approvals and cite evidence, but do not themselves authorize new textual changes.

- French Bibles: [LSG 1910](../sources/cleaned/bibles/fr/lsg-1910/editorial/README.md) · [Darby JND 2024](../sources/cleaned/bibles/fr/darby-jnd-2024/editorial/README.md)
- English commentaries: [MHC complete](../sources/cleaned/commentaries/en/mhc-crosswire/editorial/README.md) · [MHCC classic](../sources/cleaned/commentaries/en/mhcc-crosswire/editorial/README.md) · [HMCC Modern](../sources/cleaned/commentaries/en/hmcc-modern/editorial/README.md)

## 5. Editions, historical research and publication receipts

- Edition profiles: [profiles/](profiles/) — exact source/edition metadata. Similar profile titles are **not** automatically duplicates.
- Release receipts: [releases/](releases/) — version-specific immutable publication/review history, including drafts when explicitly labeled.
- Evidence and audit material: [evidence/](evidence/) — retain historical approvals and provenance.
- Historical research is collected in the [archive index](archive/README.md): Darby postmortem, LSG research handoff, the first LSG/MHC pilot, the second Bible probe and the original onboarding playbook. Their old paths remain compatibility redirects.
- [HMCC Modern editorial protocol](../sources/cleaned/commentaries/en/hmcc-modern/editorial/HISTORICAL_PROTOCOL.md) now lives beside its cleaned OSIS; its old `docs/MHCC_MODERN_ENGLISH.md` path redirects there.
- [Roadmap](ROADMAP.md) — current high-level priorities, with active issues as the status authority.

## 6. Generated technical inventory

- [Tool registry (generated Markdown)](TOOL_REGISTRY.md) and [machine-readable registry](TOOL_REGISTRY.json): regenerate with `python scripts/tool_registry.py --write`; verify with `python scripts/tool_registry.py --check`. Do not manually edit generated contents. Any removal/renaming of script entrypoints is separately tracked by [#430](https://github.com/icfmp/Bible-Resources/issues/430).

## Cleanup policy and deferred moves

A link-audited first cleanup has archived the clearly historical pilot/research reports and colocated the HMCC Modern edition protocol with its cleaned source. Other workflow guides still in active use remain at their current paths. A later relocation can group policies, workflows, technical references and generated reports into subfolders. Avoid moving these documents solely to make the top-level look cleaner: relative links are used by documentation, code and historical GitHub discussions, and a move would require an evidence-backed full-link audit. The index above establishes navigation immediately without breaking those paths.

**Protected boundary:** `entity-index/` is the independent Bible Semantic Index workstream; documentation cleanup must not change it. The legacy place-context `datasets/` is separately scoped for removal in [#38](https://github.com/icfmp/Bible-Resources/issues/38), with public-endpoint and release parity checks required. These two tasks must not be conflated.
