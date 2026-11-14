# MHCC Modern English — working editorial and technical protocol

**Status (2026-11-14):** preparatory pilot drafts only; **0/1,189 chapters independently validated**. Tracking: [#270](https://github.com/icfmp/Bible-Resources/issues/270). The original published `BRMHCC` 0.1.0 remains untouched.

## 1. Source and edition boundaries

The authoritative **working reference** is exactly the publicly released `BRMHCC` 0.1.0 zCom edition, itself unchanged in authorial content from CrossWire `MHCC` 2.0. The relevant pins are:

| Object | SHA-256 |
| --- | --- |
| Upstream original CrossWire `MHCC.zip` | `5599108faf01753864d51136a87f120d022e70867cc9df70206a0af3c3a5ef7d` |
| Full ordered upstream 29,975 native-key raw corpus | `8abd8bedb4eb0ff425999a9435e18d3c302d3a4f47863e3af5b1de36dfd538e6` |
| Released `BRMHCC` 0.1.0 ZIP | `0faf4376b6b97093ecb94f306886c24d3030ab1f5e194472ad908dd73921f9c0` |

See [published release](releases/MHCC-0.1.0.md), [source/editorial evidence](../modules/mhcc-crosswire/EDITORIAL.md) and completed [#177](https://github.com/icfmp/Bible-Resources/issues/177). CrossWire identifies its own digital edition as Public Domain / Copy Freely; this does not license unrelated CCEL digitization or material. The *distinct* CCEL witness is **not** a source substitute or silent correction authority for the released CrossWire corpus.

Preserve all original SWORD binary files, original metadata and original historical text. A modern edition is a **new, independent derivative module** with clearly identified modernized wording, its own edition identifier and catalog entry **only after final approval**.

## 2. Editorial approach: modernize language, not theology

Modernize obsolete English vocabulary, opaque idioms and cumbersome syntax only to improve comprehension. Favor idiomatic, fluent but restrained contemporary English: retain effective original formulations, expressive metaphors, pastoral exhortation, doctrinal vocabulary, rhetorical repetition, argument order, and every meaningful statement. If both choices are equally clear, prefer the wording closer to the original.

Preserve whether Henry makes a claim, inference, tentative judgment, exhortation or warning. Never upgrade uncertainty to certainty, add doctrinal qualifications of our own, collapse an argument into a summary or rewrite theology to align with modern preferences.

The treatment of biblical material requires separate evidence for:

- Direct quotations (preserve their role and distinguish them from the commentator's own prose; do **not** silently replace by a modern translation).
- Biblical paraphrases or allusions (maintain the actual argument, images and any references).
- Native scripture-reference elements and link targets (retain source `osisRef` and source key; do not infer or modernize identifiers).
- Original titles, tables, notes, paragraphs and in-text divisions (preserve meaning; editorial headings may be added *separately and recognizably* where justified).

Do not mechanically remove apparent repeated verse quotations. A verse quoted inside commentary is still part of the historical source; editorial simplification requires a separate justified decision rather than an automatic strip.

## 3. Chapter as work unit; source entry as data unit

The issue tracks **1,189 canonical biblical chapters**, not 29,975 independent comments. The original SWORD index includes multiple occupied verse keys for the same ranged authorial exposition; other text is attached to introductions. Every chapter must be traced to the exact **source native keys and any covered ranges**, without duplicating the repeated original entry or silently merging distinct ones.

For each chapter:

1. Read full exact-source compiled native XML and all required keys with the existing read-only tools (e.g. `scripts/sword_native_commentary_raw_corpus.cpp` and bounded readers). Verify archive and whole-source SHA first; save only justifiable source-to-modern identity mapping and required review evidence.
2. Identify shared/ranged original commentary, book/chapter introductions, title/paragraph/quotation/reference markup and all meaningful source content. Define how any entry spanning multiple chapters is owned and represented **once** so that no omission/duplication occurs. Never infer a source key from nearby text.
3. Produce a separately versioned, structured modernization that keeps the original source key/range semantics intact. Titles added by the editor must not be falsely attributed to Henry.
4. A reviewer **independent of the drafting pass** checks source and derivative segment-by-segment for complete thoughts, exact theological nuances, claims, emphasis, references, imagery and applications. Flag and resolve concrete discrepancies.
5. Run technical checks: expected nonempty unit/coverage map; immutable source-reference targets; duplicate/omission detection; valid Unicode and structured markup; unusual length expansion/shrinkage warnings; source-to-built SWORD reconstruction and actual native readback. No mechanical check substitutes for semantic review.
6. Correct/re-audit until PASS, or retain clearly marked draft/blocked status with precise issues and **do not** tick the chapter.
7. Commit exactly **one validated chapter per chapter-specific commit** (after separate infrastructure setup commits), push and tick that chapter in [#270](https://github.com/icfmp/Bible-Resources/issues/270). A WIP draft or speculative transcription is *not* this commit.

The existing `docs/COMMENTARY_7_STAGE_WORKFLOW.md`, `docs/COMMENTARY_POLICY.md`, SWORD inspectors, `scripts/guard_commentary.py`, validators and build/smoke tools are starting points. Do not create a bespoke translation/replacement script for this work. Any durable tool added later must be generic for other commentaries and have tests, usage docs and independent source-preservation guarantees. No refactoring of unrelated script-maintenance program #254 is authorized by this edition.

## 4. Pilots and calibration

Initial three contrasted chapters:

| Chapter | Purpose | Current evidence |
| --- | --- | --- |
| Ruth 1 | Narration, personal exhortation, book introduction vs. chapter text | `work/mhcc-modern/pilots/ruth-01.DRAFT.md` — **draft only** |
| Romans 3 | Justification, faith, original rhetoric and doctrinal distinctions | `work/mhcc-modern/pilots/romans-03.DRAFT.md` — **draft only** |
| Hebrews 7 | Melchizedek typology, priesthood, covenant distinctions | `work/mhcc-modern/pilots/hebrews-07.DRAFT.md` — **draft only** |

The initial prose drafts use STEP Bible's **rendering of CrossWire MHCC**, *not* a byte-attested extraction of the exact `BRMHCC` archive. This is a useful **secondary reading witness** but insufficient for source parity, scriptural link/reference, range, paragraph and note verification. It must be collated with the exact pinned `BRMHCC` source before claiming a validated chapter. Rework the drafts as needed rather than treating them as proven faithful already.

After three pilots have genuine independent semantic and technical PASS results, document the target style and review findings and proceed by chapter, bounded and restartable.

## 5. Git, verification, and recovery

Dedicated branch: `feature/mhcc-modern-english`. Issue [#270](https://github.com/icfmp/Bible-Resources/issues/270) is the public checklist and stage log. Source truth is in **committed files, commit SHAs and audit receipts**, not checked boxes or conversation history.

On every restart: inspect source version/hash and branch/PR; reconcile chapter files, their audit status, successful chapter-specific commit and issue checkmark; repair issue if commit was pushed but update interrupted. If no validated source-derived artifact exists, do not mark done. Preserve failed drafts separately, with concrete blockers. Push small independently auditable changes frequently.

**At launch:** 3 pilot drafts saved as `wip` commits; all remain **UNVALIDATED**. Next action: obtain exact pinned `BRMHCC` raw XML by existing private tools, establish a reversible key/range/intro map for each pilot, then perform independent content/markup audit and corrections. **0/1,189** checked.

## 6. Final SWORD and release gate

The derivative must have a clearly different SWORD module ID, metadata, edition description, provenance, separate working source and independent package. Do not replace `BRMHCC`, claim it is the original historical text, or expose unfinished work through the approved public catalogue.

The new module remains **unpublished** until every chapter is validated; all occupied source material, shared passages and introductions are accounted for; consistency and whole-corpus integrity pass; SWORD generation, roundtrip and real independent reader tests pass; licensing/metadata are reviewed; and a human samples representative passages and the project owner explicitly authorizes public publication.
