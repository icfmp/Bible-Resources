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

## Historical LSG release replay

The immutable 1.0.2 heading correction can be replayed from commit `5ea881265ba9cd525cd03fccc7925c1d5e5530c6` using `modules/lsg-1910/tools/stage_chapter_heading_hotfix.py` with its original source/native receipts and previous-version inputs. Do not run this staging command against the current approved module. For 1.0.3, `modules/lsg-1910/tools/stage_empty_paragraph_hotfix.py` consumes exact source-bound overlay, native and real reader evidence, produced by the one-shot workflow in commit history; `modules/lsg-1910/tools/review_empty_paragraph_xiphos.py` is the corresponding isolated prior/candidate GUI witness. These are historical replay tools, not independent publication authorization. The generic empty-paragraph detector remains active in Validate.

### Lexical association diagnostics

The independent book-body stream now also fingerprints each ordered OSIS word element's exact attribute values and nonspace start/end span against the native SWORD corpus, including addressable introductory body text. A matching lemma list or word count alone is insufficient: moving an annotation to another word must be detected. Attribute order is irrelevant, but values are not rewritten. Reports contain counts and bounded book IDs only. Note/title/header and outside-book lexical content, exact whitespace and original-publisher-to-cleaned-OSIS lexical fidelity are separate scopes. The Validate workflow requires this body-lexical proof on approved stock-reader-key OSIS Bibles. Zero word elements means no body lexical annotations to compare, not a successful annotated-edition witness. Real-edition diagnostic run 45501574235 verified all 705,605 body word elements in LSG across 66 books and confirmed Darby has none. The 123 LSG word elements in excluded scopes require a separate audit; they are not covered by the mandatory body check.

### Editorial inline and introduction diagnostics

Research run 45502660046 found exact selected inline attribute/span parity in both approved editions, including 2,644 LSG quotation elements, 66 LSG introduction spans and 123 title word elements; 9,751 LSG and 6,340 Darby anchored note inner streams match. The reusable comparison checks selected inline spans and cross-tag event order, and explicit introduction containers versus paired SWORD milestones, with no edition-specific exception. Body word associations remain covered by the existing independent mandatory gate. Outer note/title attributes, outside-book inline metadata, unsupported markup and exact typography are not certified by this diagnostic. Real-edition Validate run 45503516404 confirmed the reusable implementation, including cross-tag event order, on both approved editions (556 tests passed). Validate now requires the supported book editorial parity check alongside body lexical and structural checks.

### Original-format numbering inventory

`original_authorial_key_inventory.py` independently preserves literal chapter/verse labels from preflighted, pinned USFM and explicitly selected USFX Scripture members. The parser does not expand bridges or suffixes, assume a canon, or choose a provider member implicitly. Compare ordered labels per book with an explicit reviewed identifier crosswalk before OSIS compilation. LSG original USFM/USFX and cleaned OSIS matched 31,170 labels in run 45504471359. Unsupported formats/labels require review. The original numbering comparison is now part of the mandatory supported original USFM/USFX numbered-content gate below. It does not by itself certify text, notes, lexical or conversion fidelity.

### Original-format numbered content proof

The generic `original_authorial_content_parity.py` compares independently decoded USFM/USFX verse prose, note bodies, callers, anchors and numbered Strong spans against OSIS. Exact previously approved note repairs are supplied as source-bound input, not hard-coded exemptions; unmatched or partial repairs fail. Original LSG trials 45562090720, 45562348920 and 45566140719 confirm all 31,170 verses, 9,751 notes (12 exact approved repairs), 705,605 numbered word spans and 705,728 global ordered word/Strong associations. This does not certify all editorial structures, external target semantics, whitespace bytes, other source formats, or reader rendering. The comparator rejects unreviewed syntax/attributes rather than claiming a complete USFM grammar.

The `config/original-bible-content-adapters.json` registry makes the supported numbered USFM/USFX route mandatory for approved non-OSIS-source Bibles in Validate. Each adapter declares immutable original hashes, the exact archive member, reviewed book crosswalk and (if applicable) the source-bound owner-approved note-repair ledger. An unknown source format or absent adapter blocks the check. The same registry's `osis_resources` entries bind intentional OSIS-to-OSIS edits to exact original and approved cleaned SHA-256 values and an owner authorization manifest. The Validate workflow uses the existing independent verse/note reader to check ordered verse keys, nonspace and whitespace-folded prose and note bodies, note counts, callers, types, nonspace anchors, and ordered explicit targets. Reviewed relocations of leading editorial division signs and contextual target corrections/removals are reconciled exactly; missing, unused or unexplained changes block validation. Editions without a reviewed OSIS adapter must preserve these numbered semantics without such edits. This gate does not certify nonnumbered notes or all original editorial layout, lexical metadata, or reader QA.

The same independent native corpus/index/exact-key readback now runs on every approved Bible, selected from module metadata rather than a translation name. It checks numbered, introduction and opaque TOP frames against the separate native inventory and samples raw bytes through an independent exact-key reader. This readback is separate from the original-to-cleaned and cleaned-to-native semantic comparisons. The reports bind actual payload and inspector hashes; they are not reader GUI acceptance or authorization to release.

When bringing in a new edition, first use the supported existing route. Unsupported source grammar or an editorial transformation not yet represented in the registry requires a reviewed extension and regression tests, not a silent bypass. Retain evidence of reader navigation and parallel-mode behavior separately; exact typography is not implied by nonspace comparisons. The project is responsible for its own curated resources; upstream fixes are not a completion dependency.
