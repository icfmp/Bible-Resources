# J. N. Darby BPC 2024 — editorial decisions

**Release:** `BRJND2024` 0.1.1, independently curated from the identified BPC 2024 revision 2.0. The original publisher XML is unchanged.

## Why this edition differs technically

- The reviewed source contains **31,166 numbered keys** and **6,340 original notes**. Preserve the publisher's text, omitted-verse conventions and authorial apparatus.
- **521 source-attested division markers** are retained as structural metadata rather than visible asterisks; **4,690 XML indentation artifacts** were removed without rewriting authorial spaces. One genuine text-critical star remains part of the text.
- Note/link repairs and label treatment are *separate, attested transformations*. Never turn an intentional omitted-verse label into an invented verse or infer an ambiguous reference target.
- A paragraph or chapter-layout issue in Xiphos/AndBible/Bible needs source-versus-reader diagnosis, not automatic reflow.

## Where to verify

| Question | Record |
| --- | --- |
| Exact source, stages and changed bytes | [Transformation manifest](../CLEANUP_MANIFEST.json) |
| Approved version and source/payload hashes | [0.1.1 release](releases/DARBY-JND-2024-0.1.1.md) |
| Actual reader samples | [Final 0.1.1 reader QA](evidence/darby-2024-0.1.1-final-reader-qa.md) |
| Resource presentation | [Reviewed French profile](profiles/fr-darby-jnd-2024.md) |
| Earlier processing bottlenecks | [Import retrospective](history/DARBY_2024_IMPORT_POSTMORTEM.md); historical, not an active checklist |

**Only the release and source-pinned manifest determine the accepted state.** Draft notes and pre-release probes are not independent approvals.
