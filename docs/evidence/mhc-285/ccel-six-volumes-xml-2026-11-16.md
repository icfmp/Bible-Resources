# Six original CCEL MHC volume XML witnesses — SHA-pinned observation

**Status (2026-11-16):** all six individually published **CCEL ThML/XML** volumes were independently obtained into disposable private GitHub Actions storage, strictly XML-parsed and SHA-pinned, with **no original words, file bytes or annotation values** published. Their precise identity as the **source edition** of CrossWire `MHC` 2.2 and the right to republish digital editorial additions are still **unverified**.

- Tracking: [MHC intake #285](https://github.com/icfmp/Bible-Resources/issues/285), [draft PR #286](https://github.com/icfmp/Bible-Resources/pull/286).
- First real six-volume observation: [GitHub Actions #43948030420](https://github.com/icfmp/Bible-Resources/actions/runs/43948030420), **SUCCESS**.
- Primary CCEL work index: https://www.ccel.org/ccel/henry/mhc
- Source files were selected from **the original CCEL volume pages' official "Theological Markup Language (XML)" links**, not guessed from a CrossWire binary or reconstructed by the project. Examples: https://www.ccel.org/ccel/henry/mhc1 and https://www.ccel.org/ccel/henry/mhc6.
- All six SHA-256 digests are pinned in `config/commentary-intake/mhc-crosswire.json`. Later scans must abort on publisher byte drift; no silent repinning.

| CCEL volume | Exact original XML bytes | SHA-256 | `div1` | `div2` | `scripCom` | `p` |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| I, Genesis–Deuteronomy | 7,539,720 | `6eb946647f806f46129001f83013d65c51e40ac59b939ac1c51404aa50375971` | 8 | 195 | 983 | 3,843 |
| II, Joshua–Esther | 9,301,348 | `673fcb4168ad946ab1e6923c0e331cc61e4adca4498fc0ee34cf1507285aa2f7` | 15 | 264 | 972 | 4,726 |
| III, Job–Song of Songs | 9,618,829 | `8ba9779eba5d326acbfc9acaccf2ea1fa2d6b5c48b03ab86fc5e80b0bfa5b17e` | 8 | 251 | 1,427 | 5,824 |
| IV, Isaiah–Malachi | 12,837,774 | `7b6ea0800caa1daab6b0c807f5b95c7567fb5d880290bbe91d848048a80486b2` | 20 | 270 | 944 | 5,346 |
| V, Matthew–John | 9,957,346 | `8b0853b116e9a68215a594bafe29f45502d4c766e1f128cbf5fb050f45cf2518` | 7 | 96 | 494 | 7,585 |
| VI, Acts–Revelation | 9,115,881 | `296195d09d4fbb1e7516ea77c100dbc87ce37542c3109f9f570c3cf155b594c1` | 26 | 197 | 749 | 5,277 |
| **Total** | **58,370,898** | Six *separate* independently reviewable source hashes | **84** | **1,273** | **5,569** | **32,601** |

**Important interpretation:** counts are literal XML element occurrences in six separately published documents. A source `scripCom` annotation may describe a range, not a one-verse body, and its occurrence count is not directly comparable to 31,098 occupied stock SWORD verse addresses. Similarly, 1,273 `div2` and 84 `div1` elements must not be silently equated with 1,189 Bible chapters or 66 book divisions without examining original structures. The CCEL text's **32,601 `p` tags** and MHC stock SWORD's **zero literal `p` tags** establish a *formatting representation discrepancy*, **not yet proof** that authored paragraphs are lost; the compiled stock has other nesting such as `div` and may represent boundaries differently.

## Next proof required

1. On the pinned six-volume XML, report and validate **authorial chapter/book divisions and `scripCom` range semantics**; unknown work-qualified or compound references must remain unresolved until reviewed, never guessed.
2. Compare text, punctuation, reference targets, quotations, notes and ordered section/paragraph boundaries against the already pinned CrossWire `MHC` stock native stream without multiplying linked SWORD aliases into false independent sections.
3. Verify digital-edition permissions and the post-Acts contributions/attribution; CrossWire's stock public-domain claim is a useful rights witness but does not prove every additional CCEL/Logos editorial element may be modified or republished.
4. Do not modernize, re-paragraph, delete any embedded KJV quotation, create a compiled MHC candidate, alter the published catalogue or assert real reader equivalence until separately reviewed.

**Scope gate:** six independently obtained and hashed XML witnesses and valid XML structure; no full CCEL-to-stock fidelity verdict, no accepted authorial section mapping, no release approval.
