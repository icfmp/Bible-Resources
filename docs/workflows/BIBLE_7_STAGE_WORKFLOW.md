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

For already approved OSIS Bibles, the shared native index and full-corpus tools in the Validate workflow re-use the exact cleaned source and installed payload. Where an edition has a source-bound reviewed adjacent-verse merge, the independent index proof must pass first. A private projected reader-slot comparison may then combine the approved adjacent texts and shift note anchors by the preceding text's exact nonspace length; it never modifies source verse IDs or explicit target literals. Keep original key counts, projected slot counts, text/note comparison and original book-wide structural results distinct. The independent numbered-slot content comparison, whole-book body/title/paragraph/poetry structural comparison, body opening order and explicit target index addressability must all pass; none replaces the existing mandatory merge proof. Approved cleaned OSIS must contain no unexplained bare child-free whitespace-only paragraphs. Preserve intentional layout using appropriate source-attested OSIS markup; any removal requires an exact source-bound reversible review. Paragraph differences are localized by complete nonspace spans only in books whose full text streams match; zero-length spans are reported, not silently waived.

The OSIS-first [production pipeline](../PRODUCTION_PIPELINE.md) specifies the active source validation, cleaned-source fidelity, independent SWORD readback and reader checks. Keep evidence for each checkpoint in the edition's editorial records; no legacy stage-audit runner substitutes for those checks.

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
