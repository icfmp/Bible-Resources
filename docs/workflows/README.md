# Working procedures

**There is one canonical production contract:** [Production pipeline](../PRODUCTION_PIPELINE.md). It describes the acceptance evidence from choosing an edition to publication. The files below are specialized *execution aids*, not competing procedures.

## Choose a task

| Task | Read | Output / source of truth |
| --- | --- | --- |
| Import a Bible | [Bible checkpoints](BIBLE_7_STAGE_WORKFLOW.md) | One import issue, pinned source, seven evidenced stages |
| Import a commentary | [Commentary pipeline](COMMENTARY_PIPELINE.md) | One import issue and edition-local editorial record |
| Collect read-only Bible stage evidence | [Bible stage automation](BIBLE_STAGE_AUTOMATION.md) | Machine observation, **not** editorial approval |
| Review structural corrections | [Editorial audit](EDITORIAL_AUDIT_WORKFLOW.md) | Reversible decision ledger and source/cleaned comparison |
| Translate or modernize a commentary | [Translation procedure](COMMENTARY_TRANSLATION_FROM_CLEAN_SOURCE.md) | Separate derivative edition, explicit source/rights evidence |
| Publish an approved version | [Publishing](PUBLISHING.md) | Signed decision, exact module hashes and catalogue checks |
| Add or update a catalogue entry | [Catalogue integration](CATALOGUE_INTEGRATION.md) | Versioned catalogue, verified download and metadata |
| Investigate upstream changes | [Updates](UPDATES.md) | Read-only reports and reviewed change request |
| Propose a correction upstream | [Upstream contribution](UPSTREAM.md) | Source-attested patch and evidence |

## Important distinctions

- `DONE` means the *specified* gate passed. A green Action, sampled reader display, or built ZIP is not evidence of all subsequent gates.
- Module-specific decisions, candidate-specific test results and release histories must live beside that module under `sources/cleaned/**/editorial/`.
- If two guides contradict each other, follow the stricter source-fidelity rule and resolve the disagreement in a reviewed change; do not silently weaken a gate.
- Older [six-phase editorial guide](SOURCE_FIRST_EDITORIAL_PIPELINE.md), [commentary seven-stage checklist](COMMENTARY_7_STAGE_WORKFLOW.md) and [catalogue update protocol](CATALOGUE_UPDATE_PROTOCOL.md) contain implementation detail. They are **not** alternative authorities.

No workflow permits silent changes to Scripture, notes, verse numbering, commentary scope, or published bytes.
