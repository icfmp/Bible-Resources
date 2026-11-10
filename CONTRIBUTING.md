# Contributing to Bible Resources

Open an issue before importing or substantially rewriting a module. For each new **Bible**, start with the [7-stage resource onboarding workflow](docs/BIBLE_7_STAGE_WORKFLOW.md) and [import issue template](.github/ISSUE_TEMPLATE/import.yml). Complete and record one audited checkpoint at a time; resume from the issue after any interruption, never from a partially remembered chat. The seven stages govern progress, not the maximum number of small, focused PRs. Contributions must preserve original source data and supply provenance and evidence of redistribution rights. Do **not** upload copyrighted texts based only on their presence in a publicly accessible SWORD mirror.

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