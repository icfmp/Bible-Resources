# Modern MHCC — all 1,189 manuscripts vs published native K/I source-group inventory

> **2026-11-18 correction / stronger original-source evidence:** The original five-case report below was a *structural first pass*, not a complete original prose collation. The follow-up [SHA-pinned original native SWORD and immutable original CrossWire-content comparison](FIVE_NATIVE_SOURCE_WITNESS_DISPOSITION_2026-11-18.md) now demonstrates that **multiple distinctive CCEL-authored clauses from the 1 Samuel 25:39–44 exposition and Psalm 95:7–11 exposition are not found in ANY same-chapter original K/I source body**, in **either** the original stock-preserving BRMHCC 0.1.0 or curated MHCC 0.1.1. These are therefore **high-confidence missing-material candidates against the CCEL digital witness**, not merely source-index presentation differences. Exact *edition parity, complete textual loss extent and CCEL material rights* remain unproved and must be checked before any source correction or derivative publication. For Deuteronomy 20, John 3 and Zechariah 9 the relevant later authorial phrases **are** found in original K bodies, supporting *indexing or editorial subdivision* rather than missing prose. The earlier “no authorial prose absence proved” language below must be read in light of this stronger subsequent evidence.

**2026-11-17. Result: whole-canon mechanical source-group audit complete, with 5 original-to-modern navigation/topology cases requiring human editorial classification. This does NOT certify translation meaning or source presentation.**

GitHub Actions: [native-group diagnostic #44199549714](https://github.com/icfmp/Bible-Resources/actions/runs/44199549714) **SUCCESS**, including actual stock `MHCC 0.1.1` source ZIP/corpus authentication and all prior SWORD tests. The relevant CI step wrote a metadata-only JSON diagnosis; no source commentary prose, raw OSIS or new module was published.

## Full-canon counts, independently source-derived

| Quantity | Result |
| --- | ---: |
| Canonical modern manuscript chapters read | **1,189 / 1,189** |
| Original published `MHCC 0.1.1` independent numbered-K raw bodies | **4,047** |
| Original source chapters whose entire commentary is in native chapter-intro I with no numbered K | **2**: Lev.19 and Ps.108 |
| Modern manuscript *leaf* exposition headings, including the two chapter-I cases | **4,052** |
| Original K groups plus the two I-only commentary units | **4,049** |
| Net modern leaf exposition subdivisions in excess of physical original K/I units | **+3**, confined to 3 flagged chapters |
| Chapters with a structural unit-count difference or declared verse-bound discrepancy | **5** |
| Other heuristic warning classes | **624** headings lacking parseable parenthesized verse scope; **367** short prose sections under 25 words |
| Chapters with *any* diagnostic flag including low-severity warnings | **148** |
| Original-source text/meaning independently approved | **0/1,189** |

**Why the first diagnostic overreported discrepancies:** Acts 2, 3, 7, 13 and John 5, 6, 7, 8, 13, 14, 17, 18 have source-aligned Modern English exposition **subheadings marked `###`** inside parent presentation headings `##`. Counting only top-level `##` labels understated the number of translated source units. The revised source-neutral parser counts *leaf sections*, without counting a parent heading as another authored source unit. This removes those false group-count alarms. It does **not** imply their prose/notes/markup has passed a semantic review.

## Five source-topology cases, NO automatic source/editorial changes

| Chapter | Published source's actual original K body keys | Separate modern manuscript exposition labels | Observed situation / next proof |
| --- | --- | --- | --- |
| [Deuteronomy 20](accepted/deuteronomy-20.md) | 1–9; **10–12** | 1–9; **10–20** | **Same number of bodies**, but modern chapter-heading scope is broader than occupied original K addresses. Existing manuscript already notes that CCEL's printed outline gives 10–20, while one original prose title gives 10–12 although the exposition discusses siege law through 20. Inspect exact native body content and distinguish authored scope from indexed addresses, not simply retag the original. |
| [1 Samuel 25](accepted/first-samuel-25.md) | 1; 2–11; 12–17; 18–31; **32–44** | 1; 2–11; 12–17; 18–31; **32–39**; **39–44** | Source has **5 actual K bodies**, modern draft 6 topical presentation sections with overlapping verse 39; existing review records a two-part printed outline. Preserve both prose sections without creating a new original K identity. Verify that both modern topical blocks faithfully represent the *single* K 32–44 body. |
| [John 3](accepted/john-03.md) | **1–8**; 22–36 (no occupied K for 9–21) | **1–21**; 22–36 | **Same number of authored bodies**, but original first unit is linked only to K 1–8. Do **not** infer missing 9–21 prose or invent new verse keys from the displayed outline. Inspect exact native 1–8 body against CCEL and original source comments on 9–21. |
| [Psalm 95](accepted/psalms-95.md) | One source K group **1–11** | **1–7**; **7–11** | Modern layout preserves the original published *printed outline* containing an overlapping verse 7. The published native body is **one continuous K group**. Keep both topical reading sections accessible as one authored commentary body when building; do not split the source physically just because of the outline. |
| [Zechariah 9](accepted/zechariah-09.md) | 1–8; one source K body **9–17** | 1–8; **9–11**; **12–17** | The source has a single 9–17 original commentary unit while the printed outline has two subtopics. The existing modern editorial review already explicitly distinguishes them. Do not manufacture two independent K bodies. |

**No absence of original authorial prose has been proved from any of these five scope differences.** Authorial subsection headings and numeric occupied K addresses are not identical concepts. Individual source and modern prose/paragraph comparisons are still required, as are unverified original `I` headings and book introductions.

## Low-severity warnings are not certified omissions

Many of the **624** nonparseable verse-scope headings belong to one-unit chapters or proverb headings such as `## Verse 1 — ...` that place their verse label *at the beginning* rather than using `(verse 1)` at the end. This is a **parser-format warning**, not proof of an unlinked verse. The **367** short leaf sections include individually brief original proverb or single-verse comments, which may legitimately translate to under 25 words. A second semantic source comparison must distinguish accurate brevity from a real omission, and the original pinned native K body identity remains the authority.

The diagnostic explicitly reported **148 affected chapters** across all severity classes. This is **not** a claim of 148 incorrect or untranslated chapters. The genuinely actionable original/modern scope subset is the **five cases above**; prose fidelity across the corpus is still open.

## Required next actions and acceptance boundaries

1. For the five named scope cases, collate the **exact published original SWORD native body** (I/K words, original internal markup/headers, annotations and cross-references) against the modern manuscript and independently available secondary witness. Record the true unit boundaries before any reformatting of a modern heading or source-index link.
2. Treat the short and differently styled headings as **triage samples** in the full human/independent editorial clause-by-clause audit; do not apply hardcoded verse-span exceptions merely to make this audit green.
3. Preserve the two I-only original cases, Leviticus 19 and Psalm 108, according to the already documented verified 37/13 native-linked derivative transport experiment. Do not implement a global per-verse chapter-commentary fallback.
4. Do not merge or publish the modern derivative until all 1,189 chapters' authorial meaning and notes/cross-reference/verse identities are independently verified, the full SWORD reader/build tests pass, rights are cleared and owner approves.

**Original MHCC 0.1.1 untouched; derivative remains a draft.**
