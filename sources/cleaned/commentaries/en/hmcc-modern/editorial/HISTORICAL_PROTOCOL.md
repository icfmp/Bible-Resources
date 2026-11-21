# HMCC Modern — retained editorial decisions

This is **not** a production run log. It records only edition-specific decisions that another editor must understand to review or update this modern-English derivative. The accepted source and release identity are recorded in [`CLEANUP_MANIFEST.json`](../CLEANUP_MANIFEST.json) and [0.1.0 release notes](releases/HMCC-Modern-0.1.0.md). Earlier draft counts and CI experiments in this file were superseded and remain recoverable from Git history.

## 1. Modernize language, not interpretation

- Use natural, clear modern English and meaningful paragraphs; preserve every source assertion, caveat, rhetorical question, pastoral exhortation, metaphor, theological distinction and logical argument.
- Wording may change in this **separately identified derivative**, but a shortened sentence must never lose a qualification or turn a tentative judgment into a certainty.
- Maintain distinguishable direct Scripture quotations, paraphrases and commentary prose. Do not replace the commentator's biblical quotations with a different Bible translation by default.
- Reviewer checks must separately establish **semantic completeness**, **authored structural coverage**, **reference target parity** and **compiled SWORD navigation**. Smooth prose is not proof of any of these.

## 2. Chapter is a review unit; commentary sections retain their own identity

The derivative spans **1,189 chapters**, but source entries are not 1,189 interchangeable blocks. Preserve source passage ranges, distinct authorial sections, book introductions, shared keys and original references; never duplicate an authorial passage just because its native SWORD index spans several verses.

**Leviticus 19** and **Psalm 108** require special care: each has a verified *chapter-I* commentary and no independently authored numbered-verse commentary. The reviewed plan exposes the **same chapter-level content** through navigable linked verse addresses (37 and 13 respectively), not 50 copies of independently written prose. This is **not a general rule** to fill missing commentary slots in other chapters.

## 3. Placement of source introductions and original hyperlinks

Original chapter/first-verse `K` and introduction `I` storage do not reliably indicate the author's conceptual division. For example, the Genesis book-preface prose originally coexisted with first-verse material in a composite native entry; it must be tracked as one attested introduction, not inferred from empty `I:Gen` keys. Never move source content based on convenience alone.

Existing Scripture links must be associated with the correct **semantic occurrence** in modern prose, not transferred by character offset or guessed from a printed token. Source digital targets that are contradicted or unverified remain recorded for review; new destinations require an explicit editorial correction with independently verified evidence.

The approved release accounts for **15 reference corrections across 28 targets** and **two restored authorial expositions**. This is edition-specific work, not permission for future additions; consult the approved change/release evidence for exact mappings.

## 4. Limits and reproducibility

Earlier draft-phase progress reports (including partial `156/176` and `165/176` citation counts, first chapters, private preview SWORD builds and "not published" banners) have no present acceptance authority. If a specific historical decision must be reconstructed, use the file's Git history, [modernization tracking issue #270](https://github.com/icfmp/Bible-Resources/issues/270), [PR #272](https://github.com/icfmp/Bible-Resources/pull/272) and `work/mhcc-modern/` source-bound receipts.

The [generic translation workflow](../../../../../../docs/workflows/COMMENTARY_TRANSLATION_FROM_CLEAN_SOURCE.md) governs any further change. A new edit requires original/modern side-by-side evidence, rights and editorial acceptance, independent native readback and real-reader checks. The release's Numbers 29:1 → Leviticus 23:24 Xiphos click follow-up is **not automatically certified** by note markup parity.
