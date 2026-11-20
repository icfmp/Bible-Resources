# Commentary import — seven checkpoints

**Purpose:** a resumable issue checklist for importing *any* commentary. The [production contract](../PRODUCTION_PIPELINE.md) is authoritative for required evidence; [commentary production](COMMENTARY_PIPELINE.md) explains the steps. This checklist must not record any particular edition's audit results.

| Stage | Required result | Stop if |
| --- | --- | --- |
| 1. Identify edition and rights | Exact work/edition/provider/version, language, authorial source and component-specific redistribution rights | Identity, source or license is uncertain |
| 2. Preserve upstream bytes | Immutable source (OSIS or stock SWORD), URL, SHA-256, configuration/driver and acquisition record | Source is changed, unpinned or incomplete |
| 3. Inspect original scope | Full entry/key coverage; book/chapter/verse scope; introductions, title/paragraph/quote layout; genuine scripture links and notes | Expected records or authorial boundaries are unaccounted for |
| 4. Review cleaned editorial master | Deterministic transformations, entry-level ledger, independent source comparison, no unexplained text or navigation edits | Any semantic change lacks evidence or approval |
| 5. Compile and verify native SWORD | Reproducible source pin; every native key and passage scope checked; complete text, structure, references and link targets compared | Built output loses or silently remaps source content |
| 6. Test independent readers | Xiphos and another applicable client; navigation, sections, introductions, ranges, typography and package identity checked | Display or navigation defect unresolved and material |
| 7. Obtain sign-off and publish | Rights/editorial approval, exact release hashes, package and catalogue checks, public link verification | No explicit owner release authorization |

## Distinguish the two intake routes

**Original compiled SWORD:** When redistributing unchanged stock, preserve its native archive and prove byte identity. Read-only inventory or a successful `diatheke` retrieval does not establish independent historical edition equivalence.

**Source-derived rebuild:** When rebuilding from a documented authoritative text, preserve the original separately and maintain an approved, reversible ledger of changes. A rebuilt SWORD binary must not be described as identical to upstream stock. The same authorial chapter/range scopes and scripture-reference semantics must survive rebuilding.

Both routes require exact licensing checks for text *and* later digitization, annotations or other editorial material. A modern translation/modernization is a **separate edition**, not a normalization of the original.

## Checkpoints and recovery

Maintain one `[Import]` issue per edition. Record current stage, evidence location, original SHA, PR/commit, tests actually passed, unresolved questions and one next action. Stage statuses are `DONE`, `BLOCKED`, `IN_PROGRESS`, `NOT_TESTED`, with `N/A` only for justified optional checks. No auto-promoting based on a green workflow.

Use the [commentary intake workflow](../../.github/workflows/commentary-intake.yml) only as read-only upstream evidence, with the current reviewed `config/commentary-intake/<resource-id>.json` manifest where applicable. Run stage-specific tests and verify all corpus records. Store source-bound audit receipts in the resource's own `sources/cleaned/commentaries/<language>/<resource-id>/editorial/` directory, not here.

When resuming: read the issue, edition manifests and last successful Actions run, then continue the **first unverified checkpoint**. Do not derive a module's status from this generic checklist or from historical chat summaries.

## Scope and escalation

- Never invent a missing verse, duplicate a chapter-only commentary across authorial verse keys, or alter verse/range labels merely to satisfy a client.
- Distinguish invalid source structure, authorial conventions, SWORD index behavior and reader presentation; report client-specific defects to the client.
- New special cases must arise from documented source evidence, not an exception that merely makes a test pass.
- Major editorial decisions, ambiguous rights and publication require owner approval. Ordinary technical corrections and non-destructive audits do not.

See [source-first technical verification](../technical/README.md) and [publishing](PUBLISHING.md).
