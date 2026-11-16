# Contributing to Bible Resources

Open an issue before importing or substantially rewriting a module. For each new **Bible**, start with the [7-stage resource onboarding workflow](docs/BIBLE_7_STAGE_WORKFLOW.md) and its [read-only GitHub Actions runner](docs/BIBLE_STAGE_AUTOMATION.md) and [import issue template](.github/ISSUE_TEMPLATE/import.yml). Complete and record one audited checkpoint at a time; resume from the issue after any interruption, never from a partially remembered chat. The seven stages govern progress, not the maximum number of small, focused PRs. Contributions must preserve original source data and supply provenance and evidence of redistribution rights. Do **not** upload copyrighted texts based only on their presence in a publicly accessible SWORD mirror.

For a module submission, provide:

1. `modules/<slug>/metadata.json` conforming to `schemas/module.schema.json`.
2. One standard SWORD `.conf` and the corresponding compiled module files in `payload/`.
3. `EDITORIAL.md`: source revision, exact transformations, anomalies remaining, reviewer, upstream feedback status.
4. Evidence of redistribution and modification permissions; if rights are unclear, mark `restricted` and do not submit compiled content.
5. A real-reader smoke-test key and screenshots or logs for any formatting-sensitive module.

Run the full local tests and audit any source text before opening a PR:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/validate.py
python scripts/audit_text.py path/to/text.md
```

Automated normalization must be deterministic and reviewable. Do not remove scripture quotations by regex; retain the faithful text and publish any shortened reading edition as a separate, explicitly derived variant **only if modification rights permit**.

Use an issue or pull request to propose upstream fixes. Never force upstream to accept our reader-specific editorial choices.

## Reuse-first script and review policy (post-MHCC)

Before adding a tool or workflow, inspect the generated [tool registry](
docs/TOOL_REGISTRY.md), the current 7-stage process, relevant open issues/PRs,
and existing standards-based SWORD/OSIS/USFM libraries. Reuse `validate.py`,
`build.py`, `commentary_intake.py`, the native SWORD inspectors and the
reviewed release preflight rather than creating a new importer, raw SWORD
decoder, private packaging format or parallel publication channel.

**Do not add a permanent script merely to repair one bad sentence, title or
verse label.** A direct, independently reviewed, reversible patch is often
better, provided the source archive remains immutable and the patch is
recorded with its source SHA, exact before/after edit, reason, affected native
references and sections, rights, independent check and owner approval.
Run the complete source→native fidelity checks after any editorial change.
Keep source-specific identities, known alias counts, verse samples, approval
and release-day hashes in reviewed manifests/evidence, not generic algorithms.

Every retained tool must have a precise purpose, bounded inputs, a CLI or
importable interface, source/output provenance, detectable errors, and a
clear distinction between **observed**, **verified on one edition**,
**verified across editions**, **editorially/legally approved**, and
**actually published**. A unit test on a synthetic fixture is not an
independent live-reader test. An upstream `Public Domain` claim is
a rights *witness*, not proof that separately edited third-party material
may be republished. No copyrighted source text/notes, unpublished module
payload, credentials or personal data should appear in public CI artifacts.

Use **Python 3.12** and PEP 8-compatible code for new tools; prefer type
hints at public boundaries, clear public docstrings, and comments explaining
the SWORD/OSIS invariant or safety boundary instead of narrating syntax.
Propose targeted Ruff checks with a reviewed incremental configuration
rather than mass-reformatting historical scripts. C++ SWORD helpers should
own their memory safely, bound native output/inputs and expose explicit
nonzero errors. Error reports should identify a path and line/entry
when known, with stable categories and no invented corrections.

Script lifecycle decisions use `KEEP_GENERIC`, `GENERALIZE`, `MERGE`,
`HISTORICAL/ARCHIVE` and `UNDECIDED`. **The generated registry is a
conservative static inventory, not approval to delete anything.** Check
workflows, subprocesses, documentation, external tooling and **historical
tags/releases** before moving an allegedly unused script. Preserve
previous GitHub Actions receipts, exact source/compiled checksums, immutable
release assets and rollback evidence. Test behavior equivalence with
independent source/native data on at least two different resources before
extracting a reusable implementation. No change is merged with failing
acceptance gates.

For worked commands and decision points, see
[the reusable commentary workflow](docs/COMMENTARY_PIPELINE.md),
[publication process](docs/PUBLISHING.md), and
[tool inventory](docs/TOOL_REGISTRY.md). Work through small auditable PRs;
use the relevant issues as checkpoints. **Codex review or delegation must
not be initiated without the project owner's request.**
