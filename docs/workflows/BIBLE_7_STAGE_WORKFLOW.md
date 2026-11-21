# Bible import — seven evidence-gated checkpoints

This is the **progress checklist**, not an alternative production policy. The [production contract](../PRODUCTION_PIPELINE.md) defines full acceptance criteria. Record one import issue per edition, using the [issue template](../../.github/ISSUE_TEMPLATE/import.yml).

| Stage | Required evidence | Do not mark DONE when |
| --- | --- | --- |
| 1. Select the edition | Exact title, language, translator, publication edition, official source and redistribution rights for text and annotations | Rights or source identity is uncertain |
| 2. Acquire and pin originals | Immutable original archives, URLs, file sizes, SHA-256 and a provenance manifest | Only mutable URLs or unverified downloads exist |
| 3. Validate authorial source | Complete structure, native versification, missing verses, headings, paragraphs, poetry, footnotes, cross references and errors inventoried | Coverage or authorial intent is unresolved |
| 4. Build/reuse and audit SWORD | Original/master/build hashes, whole-native-corpus key and wording checks, independent compilation or unchanged stock proof | Compilation is the only successful check |
| 5. Verify structural and semantic fidelity | Full source-to-master-to-native notes, headings, references, spans, verse zero, original-language metadata and link destinations compared | Sampling or syntax-only validation substitutes for content checks |
| 6. Test readers and package | Independent Xiphos and another applicable reader, exact package size/hash, navigation, paragraph and poetry rendering | A client-specific failure is hidden with a textual workaround |
| 7. Approve and publish | Explicit editorial and rights sign-off, owner approval, final release hashes, Pages catalogue and public URL checked | Approval or public-package verification is missing |

**Stage 4 is not stage 5.** Stage 4 can check the native key/index and text structure; stage 5 must still verify original-authorial notes, annotations, punctuation, link targets, section scopes, and semantics. An optional combined machine pass does not remove either acceptance gate.

## Running and resuming checks

The [Bible stage audit workflow](BIBLE_STAGE_AUTOMATION.md) describes supported read-only commands and Actions. It collects evidence, **not** editorial approval. Optional combined `4-5` execution may share source acquisition and scanning but must record separate stage receipts.

Maintain **one** issue per resource with its current status (`IN_PROGRESS`, `BLOCKED`, `READY_FOR_OWNER`, `COMPLETE`), the completed count out of seven, exact original hash, evidence links, latest passing tests, unresolved decisions and next action. The issue and approved manifests, not chat history, are authoritative. When interrupted, resume the first unverified stage after checking the real GitHub state.

For every stage:
1. Verify input sources and previous accepted checkpoint.
2. Make one bounded, reviewable change. Never overwrite immutable originals or approved releases.
3. Run applicable source/structural, native and reader checks; retain exact successful workflow URLs.
4. Record what was proved, what was *not* tested, any blocker and the next action.
5. Mark `DONE` only when all stage evidence exists. `N/A` needs a written justification.

## Preservation safeguards

- Never invent an absent verse, change the source versification, silently edit punctuation or prose, or synthesize references.
- Preserve source-attested paragraphs, poetry, titles, notes and cross-reference destinations. A valid OSIS link is not necessarily a semantically correct target.
- Diagnose original-source defects, cleaned transformations, SWORD compiler behavior and reader rendering **separately**.
- A source-specific exception requires independent evidence and a reversible, documented decision, not a hard-coded test escape.
- Important editorial changes, licensing judgments and publication need owner approval; routine audits and technical fixes do not.

Edition-specific test results, release decisions and historical experiments belong next to the resource under `sources/cleaned/**/editorial/`, not in this checklist. See [technical verification](../technical/README.md), [rights](../policies/RIGHTS.md) and [publishing](PUBLISHING.md).
