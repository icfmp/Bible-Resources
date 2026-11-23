# Contributing to Bible Resources

Begin with the [documentation guide](docs/README.md), the [production contract](docs/PRODUCTION_PIPELINE.md) and an existing issue. Check related open PRs and current source manifests **before starting a duplicate import or tool**. For a Bible use the [seven-stage checklist](docs/workflows/BIBLE_7_STAGE_WORKFLOW.md); for a commentary use [its own checklist](docs/workflows/COMMENTARY_7_STAGE_WORKFLOW.md). One resource has one issue with exact checkpoints, evidence, blockers and next action.

## What to submit

1. Exact work/edition and upstream provider; original source path, version, URL, SHA-256 and evidence of **redistribution and derivative rights** (including editorial layers).
2. Original immutable archive in the proper source workspace **only if** it may legally be committed, and an independently reviewed cleaned master with an explicit reversible change ledger.
3. `modules/<slug>/metadata.json` under [`schemas/module.schema.json`](schemas/module.schema.json), native SWORD `payload/mods.d/` configuration and `payload/modules/` content when rights and source gates permit.
4. A module-local `EDITORIAL.md` and `sources/cleaned/**/editorial/` evidence covering fidelity, script transformations, independent key/content/notes/reference comparisons and reader QA.
5. An explicit editorial and release decision **separate** from machine test results. Never expose restricted publisher text, private notes or credentials in CI output.

If evidence is missing, mark the resource `BLOCKED`/`restricted` as applicable; do not publish an approximate replacement.

## Architecture is a release-quality contract

Before adding any file, consult the [maintained architecture guardrails](docs/architecture/MAINTENANCE_GUARDRAILS.md). Work in a temporary Git branch; do not commit a general `work/`, `history/` or `examples/` tree. Reuse the current source, tool, configuration or documentation path rather than creating an alternate pipeline. For tools, record the real consumer, positive and negative behavior, and regenerate the existing source-bound script registry. For configuration, document the active consumer and validate referenced paths. Use `docs/` for reusable guidance; individual editorial proof belongs beside the curated edition.

An **Architecture guardrails** check runs on every PR and weekly, alongside the current source, release and test gates. It rejects unreviewed directory roots, disposable tracked files, missing active JSON/file references, and broken workflow references. A deliberate architecture exception requires updating the policy and regression tests in the same PR; do not add edition-specific bypass code. The existing PR template asks for source impact, changed consumers, test links and cleanup of superseded implementations.

## Verify before requesting review

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/validate.py
python scripts/build.py --output dist
python scripts/smoke.py --dist dist
```

Add format-specific official-XSD/USFM validation, whole-source-to-cleaned and source-to-native checks, plus real Xiphos and another applicable reader test for any relevant editorial changes. A successful synthetic unit test or smoke test does not establish original edition fidelity.

Document exact commands and run IDs in the resource's issue/PR. Do not merge while required source, reader, legal or editorial approvals are missing.

## Reuse-first tool policy

Consult the [generated tool inventory](reports/tooling/TOOL_REGISTRY.md), [script guide](scripts/README.md) and current issues before adding code. Prefer existing generic intake, source validators, `normalize_osis.py`, independent native SWORD readers, catalogue builder and release verifier. Do not add one script per textual correction or create a second publisher.

Every tool needs bounded inputs, a reviewed output contract, reproducible tests, clear failure codes and safeguards against leaking publisher content. Distinguish `observed`, `technically verified`, `editorially approved` and `publicly published`.

When moving tools, first audit CLI callers, Python imports, workflows, documentation, external consumers and historical tags; test equivalent behavior on representative real sources. Source-specific exceptions must be manifested and reversible, never coded solely to make tests pass.

## Editorial and upstream responsibilities

Never silently rewrite Scripture, fill intentional omissions, merge commentary sections, change versification, add guessed lexical links, or strip existing notes/quotations. Any justified correction must have original/source-bound evidence, exact old/new text or markup, reviewer acceptance and independent full-corpus checks.

Offer clear source/metadata corrections to upstream maintainers with reproducible evidence. CrossWire or eBible accepting a patch does not automatically mean that the fix is in their current compiled module. See [upstream contribution workflow](docs/workflows/UPSTREAM.md).

The proposed [BRNP profile](docs/architecture/BRNP.md) is experimental and its full implementation is deferred to [issue #451](https://github.com/icfmp/Bible-Resources/issues/451). It is not currently mandatory for publication.
