# MHCC Modern English — working editorial and technical protocol

> **CURRENT STATUS — 2026-11-17 (supersedes dated production counters below):** **All 1,189 canonical chapter-level Modern English manuscripts across 66 books are present**, verified against the entire draft [PR #272](https://github.com/icfmp/Bible-Resources/pull/272) changed-file inventory. [Issue #270](https://github.com/icfmp/Bible-Resources/issues/270) now provides a **compact 1,189/1,189 manuscript-coverage checkpoint**; its full historical 1,189-row checklist was [archived verbatim](../work/mhcc-modern/production/checkpoints/issue-270-body-2026-11-17-pre-reconciliation.md), including 69 formerly stale unchecked rows. This is **NOT** 1,189 independently/source-native approved chapters and **NOT** a SWORD derivative module. Full published `MHCC` 0.1.1 native semantic/markup/intro/reference collation, independent editorial review, structured SWORD build/readback, reader tests, rights and explicit owner publication approval remain outstanding; **keep PR draft / do not merge or publish**. See the [canonical coverage and release-gate audit](../work/mhcc-modern/production/CANONICAL_MANUSCRIPT_COVERAGE_AUDIT_2026-11-17.md). Older dated stage counters in this protocol remain historical and must not be used as current production progress. Latest observed CI: **Validate PASS**, **source-native metadata-only PASS**, **tool registry consistency FAIL** (stale generated registry; not a derivative source-fidelity failure).


**Status (2026-11-16):** Modern English production **started at Genesis 1** using corrected published `MHCC` 0.1.1. The prior **24 scattered WIP chapters remain exploratory pilots**, not production progress. Genesis 1 and the separately modernized Genesis book introduction have committed **production CANDIDATES, not accepted chapters**; their native structure, source-linked notes, source outline and temporary SWORD reader/readback checks have passed. A full independent semantic reviewer signoff remains pending. **0 / 1,189 production chapters accepted**. Tracking: [#270](https://github.com/icfmp/Bible-Resources/issues/270) and draft [PR #272](https://github.com/icfmp/Bible-Resources/pull/272). The original published MHCC source and historical BRMHCC releases remain unchanged.

## Original I-only chapter commentary — narrowly scoped derivative treatment (2026-11-17)

**Clarification: there is NO general rule that fills missing verse commentaries with a whole-chapter commentary.** The Bible application is responsible for deciding how to present chapter-wide introductions alongside verse-specific commentary. Filling gaps throughout an otherwise partly annotated chapter would repeatedly surface the same text while scrolling and is **not approved**. This protocol makes no general app display-policy decision.

The published original **MHCC 0.1.1** has two verified exceptional chapter layouts:

| Chapter | Original native commentary storage | Verse-level entries in original | Modern English derivative treatment |
| --- | --- | --- | --- |
| `Lev.19` | Chapter `I` entry contains the authored exposition | **None** | Make the **same complete chapter commentary** accessible at all **37** verses |
| `Ps.108` | Chapter `I` entry contains the authored exposition | **None** | Make the **same complete chapter commentary** accessible at all **13** verses |

**Implementation requirements for these two chapters only:**

- In the *new Modern English derivative* (never in released `MHCC` 0.1.1), link the single chapter-wide authored commentary to **every actual verse key** of the chapter. Prefer **native SWORD-linked/aliased keys referencing one body**, not 37 or 13 independent copies of the text. Do not invent verse-specific source divisions or headings.
- Verify chapter scope against the declared module versification and native key readback before linking; reject collisions with any verse-level original/commentary unit. These two chapters are suitable **specifically because they have no native K commentary units**.
- Retain exact I-origin provenance in build records. Prevent a second independently rendered copy of the same commentary if an introduction is also exposed separately.
- Confirm both all-verse navigation and unchanged semantics in a compiled test module and real readers before approval. **This is an agreed target behavior, not a completed or published implementation.**

Evidence: [original-native I ownership](https://github.com/icfmp/Bible-Resources/blob/main/docs/evidence/mhcc-274/native-intro-text-ownership.md) and [complete native-structure metadata receipt](https://github.com/icfmp/Bible-Resources/actions/runs/44183321615). The receipt validates source ownership/key coverage, **not** a derivative SWORD build or reader acceptance.

## 1. Source and edition boundaries

The authoritative **current production source** is exactly the publicly released, source-audited corrected **`MHCC` 0.1.1** zCom edition (SWORD ID `MHCC`). It is derived from original CrossWire `MHCC` 2.0 / the historical `BRMHCC` 0.1.0, with **24 links to existing 17 original sections** and exactly **two** audited source errata (Ezek. 3 citation/OSIS target, 1 Chr. 7 `Dn` → `Dan`). Its source, ownership and sections must not be confused with the newer Modern English derivative. The key pins are:

| Object | SHA-256 |
| --- | --- |
| Upstream original CrossWire `MHCC.zip` | `5599108faf01753864d51136a87f120d022e70867cc9df70206a0af3c3a5ef7d` |
| Full ordered upstream 29,975 native-key raw corpus | `8abd8bedb4eb0ff425999a9435e18d3c302d3a4f47863e3af5b1de36dfd538e6` |
| Historical `BRMHCC` 0.1.0 ZIP (preserved) | `0faf4376b6b97093ecb94f306886c24d3030ab1f5e194472ad908dd73921f9c0` |
| **Released `MHCC` 0.1.1 ZIP** (2,449,819 bytes) | **`a0639201b57b9a6ec843fca70ffc08f75e179a24130a22ce1fd43be8ca42c746`** |
| **Reviewed corrected 0.1.1 native SWORD corpus** | **`2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e`** |

See [current published release and notes](releases/MHCC-0.1.1.md), [public release](https://github.com/icfmp/Bible-Resources/releases/tag/mhcc-0.1.1), [source review](../modules/mhcc-crosswire/EDITORIAL.md), [exact 0.1.1 rebuild manifest](../config/commentary-rebuilds/mhcc-crosswire.json) and [approved release issue #276](https://github.com/icfmp/Bible-Resources/issues/276). Historical untouched source: [0.1.0 release](releases/MHCC-0.1.0.md), [original import #177](https://github.com/icfmp/Bible-Resources/issues/177). CrossWire identifies its own digital edition as Public Domain / Copy Freely; this does not license unrelated CCEL digitization or material. The *distinct* CCEL witness is **not** a source substitute or silent correction authority for the released CrossWire corpus.

Preserve all original SWORD binary files, original metadata and original historical text. A modern edition is a **new, independent derivative module** with clearly identified modernized wording, its own edition identifier and catalog entry **only after final approval**.

## 2. Editorial approach: modernize language, not theology

Modernize obsolete English vocabulary, opaque idioms and cumbersome syntax only to improve comprehension. Favor idiomatic, fluent but restrained contemporary English: retain effective original formulations, expressive metaphors, pastoral exhortation, doctrinal vocabulary, rhetorical repetition, argument order, and every meaningful statement. If both choices are equally clear, prefer the wording closer to the original.

Preserve whether Henry makes a claim, inference, tentative judgment, exhortation or warning. Never upgrade uncertainty to certainty, add doctrinal qualifications of our own, collapse an argument into a summary or rewrite theology to align with modern preferences.

### Calibrated reading rhythm — owner feedback, 2026-11-14

The initial three drafts were **too dense and too close to older English sentence rhythm**, even where vocabulary had changed. The target is now **more fluid, less compact contemporary English** while preserving the full authorial thought:

- Shorten unnecessarily long sentences, but retain the actual logical relationship (qualification, contrast, cause, warning, exhortation). Do not recast every sentence into abrupt fragments.
- Use shorter **meaningful** paragraphs, usually one developed thought per paragraph, with visible separation. This is a **reading preference**, not a word-limit validator or permission to delete substantive material.
- Preserve meaningful rhetorical questions and exhortations, and leave significant conclusions room to stand on their own where the source supports the emphasis.
- Keep clear, precise theological terms when their nuance matters (e.g. justification, atonement, Surety, covenant), without adding unexplained contemporary paraphrases that change the author's meaning.
- Preserve the author's imagery and recognizable pastoral voice. Replace heavy or tangled sentence construction, not the meaning or the doctrine.
- Keep **source units distinct**. Added blank lines and editorial paragraph divisions are draft presentation only until they have been mapped to real OSIS/SWORD paragraph and range semantics; the finished module must render these as actual paragraphs, not raw whitespace dependent on one reader.
- Avoid gratuitous headings between every short paragraph. Headings should reflect real argument divisions, with any new editorial headings identified as such.
- Before approving a shortened paragraph, compare **every claim and nuance** to the exact source and ensure no example, limitation or deliberate repetition was dropped simply to make the text lighter.

All three pilot **DRAFTS** were revised for this rhythm; their new readability is a **style calibration only**, not an independent source fidelity PASS. The exact BRMHCC/OSIS semantic audit and SWORD round-trip still remain pending.

### Pilot semantic comparison — source meaning vs fluent English (2026-11-14)

The owner confirmed the **second, more fluid and airy style** as the target; no alternative-style testing is needed. Before extending the examples, three full pilot texts (Ruth 1, Romans 3 and Hebrews 7) were checked **section by section against STEP Bible's display of the original CrossWire MHCC** (13 original exposition units). CCEL's separate digitization was used as a non-authoritative comparison witness for Ruth and Romans. Source-meaning drift was found and corrected in 17 bounded draft text edits (Ruth 7, Romans 6, Hebrews 4), with committed-file coverage/phrase checks. The owner-requested *pilot* review and corrections are recorded in [the complete source-meaning comparison dossier](../work/mhcc-modern/pilots/SEMANTIC_COLLATION_2026-11-14.md).

**Generalize the lessons, not these unvalidated chapter artifacts:** keep the same reading rhythm, but guard particularly against dropped salvation statements, exclusive qualifiers, judgment or curse, doctrinal union with Christ, qualified certainty, source metaphors and the force of pastoral exhortations. A short, pleasant sentence is unacceptable if it weakens a statement. Keep source-meaning checks distinct from prose style checks.

**Production resumed on 2026-11-16, but the pilots are still unvalidated.** The earlier pilot collation was against the *rendered* CrossWire text; it is **not an independent second-reviewer sign-off**, not the pinned compiled corrected `MHCC` 0.1.1/OSIS verification, and not full text-and-range source acceptance. The verified original-editorial correction release is [#276](https://github.com/icfmp/Bible-Resources/issues/276); outstanding independent source matters are tracked in [#274](https://github.com/icfmp/Bible-Resources/issues/274), never silently imported into the derivative. **0/1,189 production chapters accepted**.



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
| Ruth 1 | Narration and exhortation, four separate exposition spans | `work/mhcc-modern/pilots/ruth-01.DRAFT.md` — **draft only** |
| Ruth book introduction | **Independent original book-level unit**, not a fifth Ruth 1 passage or another canonical chapter | `work/mhcc-modern/pilots/ruth-book-introduction.DRAFT.md` — **draft only** |
| Romans 3 | Justification, faith, original rhetoric and doctrinal distinctions | `work/mhcc-modern/pilots/romans-03.DRAFT.md` — **draft only** |
| Hebrews 7 | Melchizedek typology, priesthood, covenant distinctions | `work/mhcc-modern/pilots/hebrews-07.DRAFT.md` — **draft only** |

The initial prose drafts use STEP Bible's **rendering of original CrossWire MHCC**, *not* a byte-attested extraction of the exact corrected `MHCC` 0.1.1 archive. This is a useful **secondary reading witness** but insufficient for source parity, scriptural link/reference, range, paragraph and note verification. It must be collated with the exact pinned corrected `MHCC` 0.1.1 source before claiming a validated chapter. Rework the drafts as needed rather than treating them as proven faithful already.

After three pilots have genuine independent semantic and technical PASS results, document the target style and review findings and proceed by chapter, bounded and restartable.

### 2026-11-16 first resumed 24-chapter batch — native structure PASS, semantic acceptance pending

**What is actually saved:** 24 chapter-level **WIP prose drafts** (Ruth 1–4; Romans 3; Hebrews 7; 2 John 1; 3 John 1; Philemon 1; Psalms 1, 23, 100, 117, 120–125, 131, 133, 134, 148, 150), plus five separately retained book introduction drafts (Ruth, Psalms, 2 John, 3 John, Philemon). The newer drafts are in [`work/mhcc-modern/chapters/`](../work/mhcc-modern/chapters/); the three original pilots stay in [`work/mhcc-modern/pilots/`](../work/mhcc-modern/pilots/). The 1,189-chapter issue checklist has **zero checked**. Each chapter has an individual WIP commit, not a falsely approved production commit.

**Actual source-native evidence:** [GitHub Actions #43930339267](https://github.com/icfmp/Bible-Resources/actions/runs/43930339267) **SUCCESS**. The runner independently downloaded the **released** official `MHCC-0.1.1.zip`, checked the pinned full-asset SHA-256, installed its module in disposable storage and used real libSWORD to read **all 28,742 numbered K, 1,255 I and 2 TOP** entries; the complete corrected source-corpus hash matched the pinned accepted hash. For these 24 chapters, it located exactly **54 distinct original raw commentary body groups and 254 occupied original verse keys**, with **29 relevant native introduction locations**, all separately accounted for. It passed **8 synthetic fail-closed tests** (corrupt hash, malformed input, false approval, false verse scope and intro ownership included) and the source-to-draft metadata/section-label guard: **24/24 chapters and 54/54 groups**, with no section-count or claimed-range disagreement. Original source XML and words were not exported in public CI logs or artifacts. The evidence [24-chapter frozen native key/raw SHA/markup map](../work/mhcc-modern/evidence/MHCC_0.1.1_24_CHAPTER_NATIVE_MAP.json) gives exact original keys, hashes and conservative markup counts for restart. The general, tested source-native metadata receipt and draft-to-native structural guard are `scripts/commentary_modern_source_receipt.py` and `scripts/commentary_modern_draft_guard.py`, with accompanying synthetic tests and the Actions workflow.

**Temporary structured SWORD reader test:** [workflow #43931497021](https://github.com/icfmp/Bible-Resources/actions/runs/43931497021) **SUCCESS** after **11 synthetic tests**. Generic [draft-to-OSIS preview](../scripts/commentary_modern_draft_osis_preview.py) rendered the same 24 WIP chapters as **54 original section-annotated OSIS blocks with 503 genuine XML paragraph blocks**, compiled a **disposable** zCom commentary `MHCCWORK` with CrossWire's real `osis2mod`, and independently read a passage with `diatheke`. Native readback confirmed the **exact original set of 254 numbered key addresses** for this subset. The preview ZIP/OSIS text was not released or attached. It intentionally **does not include book/chapter introductions, inline source notes or original reference/quotation markup**, and it is not approved modern text. This proves preliminary SWORD paragraph/key feasibility only and **does not supersede the missing full source-fidelity stage**. At the time of this update, a separate canonical Genesis 1 *production candidate* is also being prepared on the branch by another active workstream and is not part of these 24 WIP-readback results; do not overwrite or double-count it.

**Important limitations:** A chapter's matching native section count, original source keys and source SHA do **not** prove that its rewritten words preserve all source claims. This is not an independent textual/theological audit of the corrected native raw XML, a complete direct-reference/quotation/intro placement proof, or a compiled independent SWORD derivative. None of the 24 chapters is fully approved. The first drafts and original-source reading witness remain clearly distinguished; CCEL is secondary comparison evidence, not a source substitute.

**Next acceptance sequence:** (1) one source-key-by-source-key **independent source/meaning/imagery/qualifications and literal quotation/reference review** using exact corrected original native XML, with repairs logged; (2) preserve native original introduction and source passage keys, prepare structured source markup with actual paragraphs, and run expected section/annotation/verse integrity checks; (3) compile an independent SWORD commentary module and perform a true real-reader readback; (4) only after a documented semantic and technical PASS, commit **one separately validated chapter** and check that one box in [#270](https://github.com/icfmp/Bible-Resources/issues/270). Continue bounded batches rather than fabricating acceptance because draft readability or metadata checks pass.

## 5. Git, verification, and recovery

Dedicated branch: `feature/mhcc-modern-english`. Issue [#270](https://github.com/icfmp/Bible-Resources/issues/270) is the public checklist and stage log. Source truth is in **committed files, commit SHAs and audit receipts**, not checked boxes or conversation history.

On every restart: inspect source version/hash and branch/PR; reconcile chapter files, their audit status, successful chapter-specific commit and issue checkmark; repair issue if commit was pushed but update interrupted. If no validated source-derived artifact exists, do not mark done. Preserve failed drafts separately, with concrete blockers. Push small independently auditable changes frequently.

**Read-only current-source verification:** GitHub's official 0.1.1 release API identifies the release as **public, not a draft or prerelease**, published at 2026-11-16T17:19:36Z. Its package size is 2,449,819 bytes and its signed asset digest matches the pinned SHA. Although the local container cannot download the ZIP (DNS/network restriction), **GitHub Actions now actually downloads this published ZIP, verifies its SHA, reads the entire corrected SWORD-native source corpus via real libSWORD and matches the pinned native corpus SHA**. The local container's network limitation is therefore **not** a production source blocker; the native/textual evidence is collected in an isolated CI workspace without exposing raw copyrighted commentary in logs. The three unmodified pilot prose drafts were re-pinned, and 13 expected displayed sections, 83 short paragraphs, 9 key semantic phrase regressions, and 12 Ruth book-introduction content markers were checked in the committed files. These assertions are **not** a substitute for native SWORD readback or independent semantic review.

**Restart checkpoint, 2026-11-16:** issue #270 and PR #272 reopened for production work after release #276; three pilot drafts retained unchanged in authorial prose, now re-pinned to source `MHCC` 0.1.1. Source-delta evidence limits edition edits to Ezek. 3 and 1 Chr. 7, outside all three pilots; nevertheless, exact native corrected-source key/range, notes, references and introductory structure still require audit. **Next:** obtain SHA-verified corrected `MHCC` 0.1.1 ZIP/native XML in a working SWORD environment, build exact pilot source-unit and intro map, independently re-review the 13 displayed sections against the exact source, verify structural SWORD roundtrip, record full chapter-specific acceptance **before** checking any chapter in #270. **0/1,189** checked.

## 5a. First canonical production chapter: Genesis 1 (source-audited, independent semantic gate still pending)

**Editorial production order (owner-approved):** Gen.1, Gen.2, …, Rev.22; each chapter is a *single* auditable production unit. Historical scattered pilot chapters are reused only as their canonical turns arrive. Do not begin a subsequent production chapter while the current one remains unaccepted, and do not conflate an early draft commit with the **one validated chapter-specific commit** required by the protocol.

**Saved work:** [Genesis 1 candidate](../work/mhcc-modern/production/genesis-01.CANDIDATE.md), [Genesis book introduction candidate](../work/mhcc-modern/production/genesis-book-introduction.CANDIDATE.md), [entire eight-section meaning collation](../work/mhcc-modern/production/genesis-01.SECOND_PASS_REVIEW.md), [SHA-attested original SWORD section/intro map](../work/mhcc-modern/production/genesis-01.SOURCE_MAP.json) and [two exact original link expectations](../work/mhcc-modern/production/genesis-01.REFERENCE_EXPECTATIONS.json). Each file's title/status explicitly distinguishes draft/candidate from accepted chapter.

**Actual real-SWORD proof:** [isolated original/native source and modern 0.1.1-based derivative CI #43936954142](https://github.com/icfmp/Bible-Resources/actions/runs/43936954142) **SUCCESS** and [latest original-outline preservation CI #43936584327](https://github.com/icfmp/Bible-Resources/actions/runs/43936584327) **SUCCESS**. The original corrected complete SHA matches, with **eight unique authorial source K groups across 31 native occupied keys, two original I placeholders**, 8 authentic source outline tables/rows and 16 exact source outline cells. The two original inline `osisRef` attributes survive in the disposable modernized OSIS and **actual compiled SWORD native readback**, and real `diatheke` renders corresponding modern text at both Genesis 1:3 and 1:26. Source prose is not copied to the logs or artifacts. The new *book introduction* is intentionally placed in a distinct derivative introductory unit, and its old native location is documented precisely.

**Important source-versus-editorial discovery:** Original `I:Gen` and `I:Gen.1` are **wordless**. The digital source instead contains the book-introduction prose, chapter-title/outline and first 1:1–2 exposition together in composite `K:Gen.1.1`. The derivative's move of the logical introduction to a book-introduction display is explicitly documented and source-attested, not an assumption that source `I:Gen` owned any original prose. The original source/module remains unchanged.

**Semantic and publication status:** Same-assistant second editorial read restored five meaning-level nuances and documented all eight source expositions; this is **not** an independent second review. The private SWORD demonstration is an unapproved technical proof, **not** an editorial signoff or a release. Its temporary module is *not* published; no issue checkbox is ticked. Remaining: an independent **full literal source and semantic reviewer acceptance**, verification of any source-inline quote/annotation presentation not covered by the explicit two `osisRef` checks, then one fully attested chapter artifact/commit. **Gen.2 not started.**

**Tool registry CI compatibility:** new universal `python scripts/tool_registry.py --check` introduced on main by completed #254 triggers on the synthetic PR merge, but this older feature branch predates the registry and its generated inventory. The script registry checker reports that `docs/TOOL_REGISTRY.json` and `.md` are stale with respect to new generic scripts. This is separate from original textual fidelity. Reconcile current main/registry and regenerate the inventory once finalizing this PR; don't suppress the check or invent registry hashes.

## 6. Final SWORD and release gate

The derivative must have a clearly different SWORD module ID, metadata, edition description, provenance, separate working source and independent package. Do not replace `BRMHCC`, claim it is the original historical text, or expose unfinished work through the approved public catalogue.

The new module remains **unpublished** until every chapter is validated; all occupied source material, shared passages and introductions are accounted for; consistency and whole-corpus integrity pass; SWORD generation, roundtrip and real independent reader tests pass; licensing/metadata are reviewed; and a human samples representative passages and the project owner explicitly authorizes public publication.
