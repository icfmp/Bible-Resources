# Genesis 1–24: original SWORD-native receipt versus modern manuscript divisions

**Date:** 2026-11-17  
**Status:** **SOURCE-NATIVE STRUCTURE RECEIPT ONLY — NOT SEMANTIC APPROVAL**  
**Draft PR:** [#272](https://github.com/icfmp/Bible-Resources/pull/272)  
**Exact CI run:** [#44181874801](https://github.com/icfmp/Bible-Resources/actions/runs/44181874801), job `source_metadata`, PASS  
**Commit tested:** `8ffb66122264f604b309f4086fd87a8788bda097`  
**Canonical source:** published corrected `MHCC 0.1.1`, original ZIP SHA-256 `a0639201b57b9a6ec843fca70ffc08f75e179a24130a22ce1fd43be8ca42c746`, native ordered corpus SHA-256 `2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e`.

## Observed facts

- The tested GitHub Actions job downloaded the actual published source, verified its pinned ZIP SHA-256, checked the **whole** original native corpus SHA-256, and privately traversed **Gen.1–Gen.24** using real libSWORD.
- **24/24 chapters had original numbered source bodies**: **102 distinct source body groups** over **659 occupied native numbered keys** in this selected scope. All **102** sampled group XML fragments parsed strictly. The metadata census recorded **73 original `reference` elements**, not independently checked for preservation in the corresponding modern drafts.
- A separate read-only comparison of the **24 committed chapter manuscripts** under `production/accepted/` with the CI-logged original keys found **exactly corresponding ordered exposition headings and verse-range labels for all 24**. The single extra `##` heading in Gen.1 is its *book introduction*, **not** a ninth exposition group. It requires a separate introduction ownership/deduplication decision.
- This comparison checks **declared source section count, order and numbered verse bounds**, not the content of the actual rewritten sentences. The original source markup hashes and native key lists remain in the CI's **metadata-only** logs/artifact; original prose was not exported.
- **No 1,189-chapter editorial approval** follows from these facts. Original quotation, reference, heading, paragraph and book/chapter introduction mapping remains incomplete, as does independent word/meaning/doctrine collation and compiled derivative acceptance.

## Chapter-by-chapter structure

| Chapter | Native source groups | Numbered native keys | Source group verse spans | Modern exposition sections/ranges |
| --- | ---: | ---: | --- | --- |
| Gen.1 | 8 | 31 | 1–2, 3–5, 6–13, 14–19, 20–25, 26–28, 29–30, 31 | MATCH (metadata only) |
| Gen.2 | 6 | 25 | 1–3, 4–7, 8–14, 15, 16–17, 18–25 | MATCH (metadata only) |
| Gen.3 | 7 | 24 | 1–5, 6–8, 9–13, 14–15, 16–19, 20–21, 22–24 | MATCH (metadata only) |
| Gen.4 | 5 | 26 | 1–7, 8–15, 16–18, 19–24, 25–26 | MATCH (metadata only) |
| Gen.5 | 4 | 32 | 1–5, 6–20, 21–24, 25–32 | MATCH (metadata only) |
| Gen.6 | 4 | 22 | 1–7, 8–11, 12–21, 22 | MATCH (metadata only) |
| Gen.7 | 4 | 24 | 1–12, 13–16, 17–20, 21–24 | MATCH (metadata only) |
| Gen.8 | 4 | 22 | 1–3, 4–12, 13–19, 20–22 | MATCH (metadata only) |
| Gen.9 | 5 | 29 | 1–3, 4–7, 8–17, 18–23, 24–29 | MATCH (metadata only) |
| Gen.10 | 3 | 32 | 1–7, 8–14, 15–32 | MATCH (metadata only) |
| Gen.11 | 4 | 32 | 1–4, 5–9, 10–26, 27–32 | MATCH (metadata only) |
| Gen.12 | 4 | 20 | 1–3, 4–5, 6–9, 10–20 | MATCH (metadata only) |
| Gen.13 | 4 | 18 | 1–4, 5–9, 10–13, 14–18 | MATCH (metadata only) |
| Gen.14 | 4 | 24 | 1–12, 13–16, 17–20, 21–24 | MATCH (metadata only) |
| Gen.15 | 5 | 21 | 1, 2–6, 7–11, 12–16, 17–21 | MATCH (metadata only) |
| Gen.16 | 3 | 16 | 1–3, 4–6, 7–16 | MATCH (metadata only) |
| Gen.17 | 4 | 27 | 1–6, 7–14, 15–22, 23–27 | MATCH (metadata only) |
| Gen.18 | 4 | 33 | 1–8, 9–15, 16–22, 23–33 | MATCH (metadata only) |
| Gen.19 | 2 | 38 | 1–29, 30–38 | MATCH (metadata only) |
| Gen.20 | 3 | 18 | 1–8, 9–13, 14–18 | MATCH (metadata only) |
| Gen.21 | 4 | 34 | 1–8, 9–13, 14–21, 22–34 | MATCH (metadata only) |
| Gen.22 | 5 | 24 | 1–2, 3–10, 11–14, 15–19, 20–24 | MATCH (metadata only) |
| Gen.23 | 2 | 20 | 1–13, 14–20 | MATCH (metadata only) |
| Gen.24 | 4 | 67 | 1–9, 10–28, 29–53, 54–67 | MATCH (metadata only) |

**Total:** 24 canonical chapters; 102 source groups; 659 occupied original numbered keys.

## Explicitly unresolved

1. Gen.1's original `K:Gen.1.1` is composite: book introduction, chapter outline, and first exposition. Original `I:Gen` and `I:Gen.1` do not own the authorial introduction prose. The separate modern introduction candidate and the Genesis 1 manuscript must not be emitted twice in a final module.
2. Gen.5 contains a known original-digital lacuna at 5:25–32. The derivative may use the separately documented witness-backed restoration under [#291](https://github.com/icfmp/Bible-Resources/issues/291), but this receipt does **not** approve the modern wording or change the released source.
3. None of the 73 source reference elements in this 24-chapter metadata census should be assumed faithfully transferred merely because the source-versification heading boundaries match.
4. This is **not independent semantic review** and **not** a source-to-derivative SWORD round-trip. The `accepted/` directory remains an editorial drafting directory, not a declaration of publishable approval.

## Next action

Expand the read-only original-native inventory using the existing generic receipt in subsequent bounded batches. In parallel, independently collate the first modern chapter against exact original source bodies and account for original notes/links and introduction placement. Keep PR #272 in **draft**; do not merge or publish.
