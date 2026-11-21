# Louis Segond 1910 — editorial decisions

**Release:** `BRLSG1910` 0.1.0. This index explains the maintained edition; it does not authorize another text change.

## What matters

- The cleaned OSIS is the **recovered source used for the approved compilation**, not a fresh transcription of the 1910 printed edition. Consult [`CLEANUP_MANIFEST.json`](../CLEANUP_MANIFEST.json) for exact hashes and provenance.
- Preserve the original translation's words, punctuation, notes, missing verses and native versification. Historical structural retyping or headings must not become an automatic rule for other passages.
- Distinguish publisher/source differences, native SWORD address behavior and reader-specific rendering. Release approval does **not** independently prove every 1910 print/digital difference has been resolved.

## Where to verify

| Question | Authoritative record |
| --- | --- |
| What was the exact cleaned source? | [Source and transformation manifest](../CLEANUP_MANIFEST.json) |
| What was released and authorized? | [LSG 0.1.0 release](releases/LSG-0.1.0.md) |
| How was the native module audited? | [Native source audit](../../../../../../modules/lsg-1910/SOURCE_AUDIT.json) |
| What are the reader-facing editorial descriptions? | [Approved French profile](profiles/fr-segond-1910.md) |
| What did the early experimental work establish? | [Historical research handoff](history/LSG_AUDIT_RESEARCH_HANDOFF.md), for reproducibility only |

**No open proposal in this directory should be mistaken for an approved source correction.** New findings need their own issue and source-backed review.
