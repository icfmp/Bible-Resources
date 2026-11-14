# Resource onboarding playbook — lessons from Louis Segond 1910

Status: **operational guidance, not a claim that all gates are automated**. This records the first Bible release (LSG 0.1.0, 2026-11-09) and defines the repeatable procedure for future translations and commentaries.

References: [First LSG release](releases/LSG-0.1.0.md), [full LSG research PR #24](https://github.com/icfmp/Bible-Resources/pull/24), [generalization backlog #28](https://github.com/icfmp/Bible-Resources/issues/28), [normalizer issue #3](https://github.com/icfmp/Bible-Resources/issues/3).

## Operational checkpoint tracking for the next Bible

Use the [seven-stage resumable Bible workflow](BIBLE_7_STAGE_WORKFLOW.md)
**before starting a new edition**. It is the day-to-day sequence and issue
progress tracker; the checklists below are detailed technical evidence
requirements inside those seven stages, **not dozens of extra steps**.
After each successful stage, record a GitHub issue checkpoint with the
exact approved inputs, merged PR/commit, tests, remaining gaps and next
action. Never mark a stage complete on a pending CI run or an unmerged
branch. The full source→SWORD audit remains under development in
[issue #28](https://github.com/icfmp/Bible-Resources/issues/28).

## Eight lessons that change our process

1. **Upstream before rebuilding.** Compare the publisher's original text/USFM/OSIS, any publisher-compiled SWORD package and the candidate **before writing new conversion code**. In LSG, the original SWORD module preserved the same lexical alignments and note words. The measurable value of our rebuild was source-verse addressability and selective display compatibility, not new Bible wording.
2. **Textual equality is not reference-index equality.** The entire text may survive while source verse keys are merged by an incompatible registry. Audit original keys, the module's actual indexed entries and its declared SWORD versification separately. Never choose a new v11n just because it makes a specific GUI comparison pass.
3. **Verse-zero material matters.** Real LSG poetry/paragraph/heading markers were found inside book and chapter introductions, not ordinary verse bodies. All verse-zero keys must be included in structural and note-position audits.
4. **Count, position and formatting are distinct checks.** Verify all word-to-Strong associations, note type/caller/body and whole-book word-relative position; check matched opening and closing events for titles, poetry and paragraphs; separately compare whitespace and typography. All 9,751 LSG note bodies preserved content, but not identical source whitespace.
5. **An XML reference is not automatically a valid hyperlink.** Source titles may contain targetless references that frontends render as blue links. Preserve the exact editorial text and neutralize only verified targetless heading markup via a reversible, schema-validated operation. Never invent an osisRef or alter genuine note references.
6. **Reader behavior needs independent evidence.** A parallel-view screenshot initially made LSG's Ecclesiastes 12 look incomplete. Standalone readers had all the text. Bible application's automatic correspondence across modules declaring different versifications produced false gaps. Inspect module source/readback independently, then report application-specific bugs separately (see [Bible #252](https://github.com/icfmp/Bible/issues/252)).
7. **Do not confuse test ZIP, GitHub Release, and remote SWORD catalogue.** The initial LSG 0.1.0 GitHub Release was published before the catalogue. GitHub Pages initially failed because it was not enabled, then the owner activated it. The final [catalogue registration and Pages run #42668476650](https://github.com/icfmp/Bible-Resources/actions/runs/42668476650) succeeded: `BRLSG1910` is approved in `main`, its source-audited files are retained, and the [JSON catalogue](https://icfmp.github.io/Bible-Resources/catalog/v1/catalog.json) lists one module. Independently verify each future stage and URL; an approved catalogue entry does not by itself prove an application has already imported it.
8. **A CI success does not imply final editorial approval.** Full-corpus semantics, reader rendering, exact printed-edition typography, derivative rights for enrichments and actual publication are distinct statuses. Document unverified Xiphos tests, the Mark 10:52–53 reviewed compromise, source Job 34:37 absence and literal introduction formatting residues instead of disguising them.

## Intake checklist (for every new resource)

### A. Identity, rights and upstream baseline

- Record edition/year, publisher, language, canon, source format, URLs, revisions, immutable original archive SHA-256, distribution and derivative permissions.
- Independently review rights for Bible text, notes, headings, lexical/Strong enrichments. A public download is not automatic permission to redistribute everything.
- Fetch official source and official SWORD when both exist. Check differences and record a concrete reason for building an alternative. **Reuse a sound official module rather than needlessly rebuild it.**

### B. Source and versification

- Use main-branch read-only tools: **scripts/audit_osis.py** and **scripts/guard_osis.py** (official pinned OSIS 2.1.1 XSD).
- Apply **scripts/normalize_osis.py** only with approved source/SHA-bound reversible structural plans. No automatic source rewrites.
- If input is USFM or USFX, apply a reviewed standards-based conversion and verify exact original verse keys, titles, paragraphs, poetry, note order and introductions.
- For a separately validated original OSIS document, run **`scripts/source_osis_inventory.py`** to produce the edition-independent, SHA-bound authorial key list. It rejects duplicate, non-ordered, ranged or unclosed source verse milestones, but does not prove the USFM/USFX conversion or actual compiled reader inventory. See [SOURCE_OSIS_INVENTORY.md](SOURCE_OSIS_INVENTORY.md).
- Independently inventory **actual native stock-SWORD occupied reader keys**, chapter ceilings and verse-zero intro keys with `scripts/sword_native_index.cpp` / `scripts/sword_native_inventory.py` against an isolated exact compiled payload. See [NATIVE_SWORD_INDEX_INVENTORY.md](NATIVE_SWORD_INDEX_INVENTORY.md). This is not a source text or note parity test.
- Compare source chapter/verse keys with actual compiled SWORD reader slots and registry, including empty/omitted verses and all verse-zero material. Distinguish source omission, alternative numbering, inaccessible keys and actual missing data.
- Any unavoidable source-index merge must be documented in an explicit, edition-bound, reviewer-authorized, reversible manifest. LSG's one special Mark merge does not justify a universal merge rule.

### C. Compiled SWORD fidelity

- Use the released stable SWORD importer and a separate installation root; verify the actual binary readback.
- For the full source canon, compare Scripture character streams and individual references, word-to-Strong ordered pairs if present, notes (caller/type/body/word offsets), explicit machine reference targets, and the *ordered opening and closing* of title, poetry, quotation, verse and paragraph structures, including introductions.
- Report exact/NFC/whitespace-normalized differences separately and flag escaped formatting residues (the LSG case left three literal backslash-i sequences in introductions).
- **New (Darby 0.1.1 lesson):** audit each source-leading symbol and paragraph-open whitespace category against the **actual native SWORD**, not only verse-key and nonspace text parity. Authorial subject stars may require reversible structural metadata, whereas note/text-critical symbols must remain visible. XML pretty-print whitespace can leak into displayed verse starts. Do not blindly strip either. See [generic OSIS paragraph rendering QA](OSIS_PARAGRAPH_RENDERING_QA.md).
- Compare real upstream compiled data before claiming editorial improvements. Fail closed on unexplained differences.
- **Current limit:** These exhaustive checks are predominantly **LSG-specific scripts in research PR #24**, not yet a generic one-command source-to-SWORD tool on main. Reuse their algorithms, not LSG-specific numbers or book IDs. Tracked in [#28](https://github.com/icfmp/Bible-Resources/issues/28).
- **Recovered reusable aids:** `scripts/private_sword_bundle.py` tests a bounded, edition-parameterized SWORD ZIP in an isolated reader installation; `scripts/note_whitespace_diagnostics.py` records non-content-only note whitespace differences for explicit review. They were extracted from #24; neither performs the entire original-source-to-compiled full-canon audit. See [LSG audit research handoff](LSG_AUDIT_RESEARCH_HANDOFF.md).

### D. Reader matrix and release

- Check isolated package install and real diatheke readbacks; test actual AndBible/JSword and Xiphos when available, distinguishing tested from untested.
- Cover book ends, long poetry, headings, note-heavy verses, unusual introductions, editorially absent verses and actual verse-system boundaries. Compare standalone and parallel reading. Test both pane directions.
- Include passage-specific checks for source-leading editorial signs, paragraph indentation and protected textual markers in at least two independent readers. Verify screenshots actually show the requested reference (a stale reader view is **not** visual signoff), on the exact final package/module ID. See [paragraph rendering preflight](OSIS_PARAGRAPH_RENDERING_QA.md).
- Separate application issues from source/module issues. Preserve every author's word even when a client fails.
- Keep source archives immutable, metadata/rights evidence current, and package source/release SHA-256 pinned. Compare all data files byte-for-byte after any module-ID repackage.
- **scripts/promote_sword_preview.py** is available on main but its current inventory and metadata assumptions are **RawText/Segond-specific**. It is not a generic zText packager. See [#28](https://github.com/icfmp/Bible-Resources/issues/28).
- Before describing a module as public, verify the actual immutable GitHub Release URL. Before describing a SWORD repository as available in Bible, independently verify the Pages deployment, mods.d.tar.gz, JSON catalogue and app import.

## Current capability inventory

| Capability | State |
| --- | --- |
| OSIS official schema guard, source audit, reversible layout normalizer | Implemented on main |
| Manifest/rights validator, deterministic catalogue builder, SWORD smoke | Implemented on main; LSG 0.1.0 is approved and the Pages SWORD/JSON catalogue deployment succeeded |
| Hash-locked first-release packaging and regressions | Implemented on main for the first RawText/Segond recipe |
| Native SWORD reference-index, full-corpus raw scan and USFX/SWORD main-text diagnostics | Reusable, read-only tools now on main; tested on real LSG and WEBP sources, but not yet a complete source-to-release acceptance gate (#28) |\n| Note body/type/caller/explicit raw-target diagnostics | Available on main; actual positions, resolved reference targets, source-only note relocation and full editorial structure remain unverified (#28) |
| Source-aware multi-reader end-to-end acceptance matrix | Partially manual, not yet a CI gate |
| Generic zText/RawText source-to-published-module framework | Pending, tracked in #28 |

## Completion receipt for the next Bible

Each resource issue must link original source hashes and edition rights; explain upstream comparison and rebuild rationale; show exact verse-index coverage and source-to-SWORD semantic/structural parity; show reviewed changes and rollback; identify reader tests performed/absent; list known limitations and editorial approval; and provide **independently verified** public artifact URL and checksum.

Do not label a stage complete from memory, a planned test, a single green CI badge or a screenshot alone.
