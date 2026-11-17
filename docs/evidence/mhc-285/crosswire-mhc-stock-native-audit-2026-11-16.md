# MHC 2.2 original CrossWire stock — read-only source/native evidence

**Resource:** Matthew Henry's **Complete** Commentary on the Whole Bible, `MHC` (not `MHCC`).  
**Tracking:** [import #285](https://github.com/icfmp/Bible-Resources/issues/285), [draft intake PR #286](https://github.com/icfmp/Bible-Resources/pull/286), early mixed [pilot #12](https://github.com/icfmp/Bible-Resources/issues/12).  
**Observed:** 2026-11-16, original official CrossWire package; no text edits, reindexing, repackaging, publication, or approval.

## Identified exact original

- Official metadata: https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHC
- Original SWORD ZIP: https://www.crosswire.org/ftpmirror/pub/sword/packages/rawzip/MHC.zip
- Observed and reverified original ZIP SHA-256:
  `6bcb936873ca144e317805e5c1677940fd86e2403f7c14517752e44f25c8882b`
- Original `.conf`: `MHC`, version `2.2`, English, `zCom4`, effective `KJV` versification, `SourceType=OSIS`.
- Upstream `Public Domain--Copy Freely` claim; CCEL / Logos identified as prior digital witnesses. This claim has **not yet cleared** all derivative/digital annotations and editorial rights gates.
- The stock `SourceType=OSIS` does **not** prove that original independently authored OSIS XML was acquired or validated.

## Reproducible original module scans

1. [Pinned intake + independent full native key index](https://github.com/icfmp/Bible-Resources/actions/runs/43945404124): **SUCCESS**. The changed-manifest source selector explicitly chose `mhc-crosswire`; the upstream ZIP digest matched the pinned SHA.
2. [Complete stock native content + markup census](https://github.com/icfmp/Bible-Resources/actions/runs/43945788585): **SUCCESS**. Real SWORD native reader privately hashed all occupied entries; independent key inspector required an exact ordered match; every numbered/introduction payload was strictly XML-fragment parsed without rewriting malformed entries.
3. [Repeat content scan and durable fingerprint log](https://github.com/icfmp/Bible-Resources/actions/runs/43946314351): **SUCCESS**. Same original ZIP and full native reader pathway; complete original ordered raw-corpus SHA-256:
   `2c4fe82710165202fdec300ca9636a150a9998f19c7b19ee4e81db5a6b75f5b5`.

### Observed occupied native slots

| Kind | Count | Semantics |
| --- | ---: | --- |
| Numbered verse keys (`K`) | 31,098 | Occupied index addresses, **not** original commentary sections |
| Introduction keys (`I`) | 1,255 | Original stock introduction slot addresses |
| Opaque TOP keys (`U`) | 2 | Metadata not presumed to be XML |
| **All occupied native slots** | **32,355** | Independent native-key order reconciled with raw content frames |

**32,353** original K/I records were successfully parsed as strict XML fragments; **0** malformed or oversized K/I records were observed. The two opaque TOP entries were inventoried but not parsed as authorial commentary. The complete *readback* was **470,220,331 unfiltered raw-entry bytes**, which includes repetition from linked addresses and must **not** be misreported as 470 MB of distinct authored exposition.

### Original stock markup census, summed across readback slots

| Tag / category | Count |
| --- | ---: |
| `reference` | 636,538 |
| `hi` | 2,073,380 |
| `div` | 592,318 |
| `title` | 27,696 |
| `chapter` | 11,281 |
| `note` | 96 |
| `milestone` | 198 |
| Other element category | 9,782 |
| Literal `p` elements | 0 |

**No literal `p` tags is not evidence that authorial paragraphs were lost**: original commentary block divisions may instead be encoded in nested `div` elements. The ordering and editorial meaning of such divisions still require a source-edition comparison.

All 636,538 `reference` elements had a nonempty original `osisRef` and a nonempty visible label. These are *element occurrences across readback slots*, not distinct scripture reference targets.

Read-only reference target **shape** classification:

| Observed shape | Count |
| --- | ---: |
| Single OSIS verse-like | 538,604 |
| Verse range-like | 93,647 |
| Book/chapter-like | 767 |
| Compound | 3,438 |
| Other/unclassified | 82 |

The **82 unclassified** targets and compound forms require source-bound examination; their classification is **not** a finding of malformed links, nor proof that referenced verses exist. No source reference was changed, normalized or deleted.

## Distinct pending gates

- Verify a specific independent **six-volume CCEL** original text and markup witness (https://www.ccel.org/ccel/henry/mhc), its edition/version and electronic rights; independently pin originals. Do **not** equate CCEL text with CrossWire stock merely because the latter names CCEL/Logos.
- Reconcile authentic authored commentary **section/range boundaries** and book/chapter introductions, rather than inferring one commentary unit from each occupied K slot.
- Perform independent text/punctuation/section/quotation/notes/reference target parity, with explicit explainable exceptions and reversible edits only when warranted.
- Review the 82 unknown reference shapes, compound link behavior, 9,782 `other` markup occurrences, and long passages against the actual source and real reader.
- Verify genuine diatheke/Xiphos/AndBible behavior separately. Any duplicated biblical quotation must be classified and **preserved** unless a separate owner-approved editorial decision is supported.
- Keep rights and editorial approval and public release **blocked**. Existing MHCC/LSG/Darby packages, catalogue and published assets are unchanged.

**Status boundary:** independently complete **stock native key/raw/XML inventory**, **not** full authenticated historical-source parity, editorial review, an accepted corrected version or publication. This is evidence toward stage 3 and stage 4a/4b only; those stages are not thereby declared complete.


## Official authoring OSIS versus published stock metadata (2026-11-17)

**Independently executed exact-head observation:** [read-only original-source job #134322183231](https://github.com/icfmp/Bible-Resources/actions/runs/44163145497/job/134322183231) in [six-volume workflow run #44163145497](https://github.com/icfmp/Bible-Resources/actions/runs/44163145497), branch revision `bcb1035f16d43bc6935a715d96f2df4d88da89e6`; job **SUCCESS**, as were the other eight separate workflows on that revision. This is a source/metadata acceptance checkpoint only, not a rebuilt commentary.

The upstream official [CrossWire MHC GitLab repository](https://gitlab.com/crosswire-bible-society/mhc) was read **at pinned commit** `537591a94c991941877b47a06666b6a7812e05d8`. The original authoring `mhc.osis.xml` is 48,020,985 bytes, SHA-256 `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`; source `mhc.conf` is SHA-256 `813160b22ea9662273269600bc16d48af0d5dc07de7a918f8f0f267c1400caf2`. The job also independently downloaded and authenticated the *published original* `MHC.zip` against its pinned package SHA `6bcb936873ca144e317805e5c1677940fd86e2403f7c14517752e44f25c8882b`, then extracted its genuine original `mhc.conf`, SHA-256 `889f178712b8bcc1794284f0c2dec042a0680e501587a553cdb6ed4bc6beb537`.

| Critical config field | Original official authoring source | Pinned distributed original | Exact field agreement |
| --- | --- | --- | --- |
| `Version` | `2.2` | `2.2` | Yes |
| `ModDrv` | `zCom4` | `zCom4` | Yes |
| `SourceType` | `OSIS` | `OSIS` | Yes |
| `DistributionLicense` | `Public Domain` | `Public Domain` | Yes |

**Bounded conclusion:** all **four** explicitly checked critical field values are identical in independently verified upstream and package configurations. The complete `.conf` byte digests **differ**, so byte-for-byte config identity is **not** claimed; other fields have **not** been reconciled. Nor does agreement with an upstream `Public Domain` metadata claim itself clear CCEL/Logos-prepared electronic-edition rights. The authentic full source OSIS and binary zCom4 K/I/TOP contents, formatting, verse mappings and notes have **not yet** been exhaustively paired; no inference of compilation parity, historic printed-edition identity, editorial correction authorization or release follows. The original source, published package, catalogue and commentary prose remain untouched.


### Entire original configuration field-name comparison — successful private CI (2026-11-17)

[Original-source job #134334648809](https://github.com/icfmp/Bible-Resources/actions/runs/44165819190/job/134334648809) **SUCCESS** on exact branch SHA `9665f1966f1632b984ce4794238415d35085f1c6`. Independently authenticated both original source/package bytes again; the nine independent workflows at that SHA also all **SUCCESS**, including the six real CCEL volumes. The source-neutral comparison preserves *ordered lists* for repeated keys, does not collapse duplicates into a map or print original field values.

| Observed class | Original configuration field names (metadata only) |
| --- | --- |
| **11 ordered-value equal fields** | `About`, `BlockType`, `CompressType`, `Description`, `DistributionLicense`, `Encoding`, `Lang`, `ModDrv`, `SourceType`, `TextSource`, `Version` |
| **6 changed ordered-value fields** | `DataPath`, `GlobalOptionFilter`, `InstallSize`, `LCSH`, `MinimumVersion`, `SwordVersionDate` |
| **2 additional distributed-only field names** | `OSISVersion`, `Versification` |
| Upstream-only field names | None |
| Duplicate-value field names in **each** original config | `GlobalOptionFilter` |
| Nonempty unparsed lines | Upstream **9**, distributed **10**; original comments and section headers can account for part of this, but those lines are not semantically classified |

**Implication:** publisher-to-distribution metadata lineage is better established than with the initial four-field check, but the changed field *values have deliberately not been published or semantically adjudicated*. `Versification` appears only in the distributed configuration, making the effective native versioning/versification contract a **distinct source-to-package validation item**, not automatically an error or an indication of textual divergence. The full config SHA hashes differ, and no canonical equivalence of all settings is asserted. This audit still does **not** compare original authoring-OSIS word order, markup, references, notes, or complete K/I/TOP transport against the compiled SWORD stock. Rights and editorial approval remain separate gates; no original files were changed.

## First original authored-OSIS → genuine compiled-native K lexical anchor replay (2026-11-17)

**Exact source/head validation:** [original source/native reader job #134342199191](https://github.com/icfmp/Bible-Resources/actions/runs/44168810342/job/134342199191) **SUCCESS** at PR branch SHA `6f1b906507d204bd8b4f00dcb0c259e00059a6ea`, including **10/10** source-neutral synthetic tests. The reader independently authenticated the official original CrossWire authoring OSIS (`3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`), pinned published ZIP (`6bcb936873ca144e317805e5c1677940fd86e2403f7c14517752e44f25c8882b`), **all 32,355 authentic compiled occupied K/I/TOP frames** against a separate actual SWORD native-key inspector, and the full original ordered raw SHA-256 `2c4fe82710165202fdec300ca9636a150a9998f19c7b19ee4e81db5a6b75f5b5`. The stock module is never rebuilt or modified.

The new **generic, in-memory, read-only** comparator takes the source text *only between genuine authoring-OSIS chapter `sID/eID` milestones*, validated by chapter text hashes, then compares all distinct genuine compiled native **numbered K** XML raw bodies in the **corresponding original chapter**. Identical raw bodies occupying adjacent verse keys are deduplicated for text comparisons, but their actual occupied-slot counts remain visible. It tokenizes rendered element text, uses exact case-sensitive **eight-consecutive-word** windows, and reports aggregate counts and SHA receipts, **not any original prose or native verse-key strings**.

| Independently scoped chapter | Original source visible tokens | Distinct original source eight-word windows | Source windows seen inside genuine compiled chapter K raw | Occupied original K slots | Distinct original native K raw payloads | Summed distinct native raw visible words |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Psalm 7** | 3,686 | 3,666 | **3,513** | 17 | 2 | 3,537 |
| **Acts 17** | 15,712 | 15,634 | **15,436** | 34 | 5 | 15,542 |

Source chapter references are transmitted as hashes (`4cc45baa545490e77d896ed22019afe9b81d3aba1410614b1481d0107dd6f196` and `db754acc705ee64f67940938bff28466ceddf3fa088201b7734c70828ba2aa38`) in the job metadata; they have been mapped to the **already published source marker case labels**, not newly inferred original commentary section or native verse mapping.

**What is now demonstrated:** extensive exact visible-word short-window overlap between the authentically bounded official MHC 2.2 source and actual published original SWORD native K contents for these two chapters, with fully reconciled raw corpus identity. The observed nonmatching eight-word windows (153 in Psalm 7; 198 in Acts 17) are **not** 153 or 198 missing words, paragraph defects, or proof of authorial omission. Markup segmentation, source/native typography, quotation and reference representation, editions and neighboring structures may all contribute. A single native raw body did **not** match either entire authoring chapter exactly; the source has several commentary units per chapter.

**Still open:** exact complete ordered source→native word/character/punctuation parity, each section's source/compiled location and boundaries, intro `I` and opaque `TOP` source ownership, complete notes and markup, independent historic printed-edition identity for CCEL Psalm VII and Acts XVII suspect paragraphs, legal/CCEL electronic derivative rights, owner/editorial acceptance and *genuine corrected* Xiphos/AndBible GUI. The earlier absence of exact entire CCEL paragraphs in the authenticated source OSIS remains a **different source-to-source comparison**; this native eight-word audit does not authorize text restoration or declare the published MHC fully faithful. No sources, stock ZIP, module, catalogue or release were modified.

## Original authoring OSIS → authentic compiled K **and chapter I** lexical coverage (2026-11-17)

The first full original source-chapter word-coverage conclusion is **independently validated**, not inferred from metadata: [real CrossWire source/native job #134354033580](https://github.com/icfmp/Bible-Resources/actions/runs/44172163578/job/134354033580) **SUCCESS**, PR SHA `2ae3c752bda3561477cb62fc49a99c5c0e016d1f`, **17/17** source-neutral synthetic tests passed. The job verified the original authored OSIS SHA `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`, published original MHC 2.2 ZIP SHA `6bcb936873ca144e317805e5c1677940fd86e2403f7c14517752e44f25c8882b`, every original SWORD occupied K/I/TOP native frame against an independent libSWORD index, and original full ordered native raw SHA `2c4fe82710165202fdec300ca9636a150a9998f19c7b19ee4e81db5a6b75f5b5`.

The source-neutral inspector derives real source chapter boundaries from original authenticated `chapter sID/eID` milestones. It checks all distinct occupied native **K** bodies as *whole, case-sensitive, contiguous, exactly ordered word-token sequences* in the corresponding source chapter, never treating multiple occupied verse slots containing the same raw block as multiple authorial sections. It then separately admits only original compiled **chapter-specific I** keys (not book-level introductions) and checks those whole visible-word sequences against the same exact authentic source chapter.

| Original OSIS chapter | Authenticated source visible words | Distinct original K bodies with unique whole exact source placement | Source-only prefix after K | Real original chapter-specific I entries with unique exact placement | Words left uncovered by unique K+I intervals |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Psalm 7** | **3,686** | **2 / 2** across 17 occupied K slots | **149**, start offset zero | **1 / 1**, exactly covers 149-word prefix | **0** |
| **Acts 17** | **15,712** | **5 / 5** across 34 occupied K slots | **170**, start offset zero | **1 / 1**, exactly covers 170-word prefix | **0** |

Both chapters have **zero word-token overlap among the uniquely located distinct K body intervals**. All reported I and K full-body positions are individually unique in their original source chapter. The original prefix-only SHA receipts are `468f2e53e55a6a9551112e8982e88b90d865d4537ac6cfbcefdcbc00d100ec72` (Psalm 7) and `3a96dce743d745ddffec71415fe7bc6143e99bb9db09dfe9ae8641a21` (Acts 17). These are original **word-token** and source-location receipts; no raw words, original XML bytes, native verse keys or private SWORD payloads were printed or committed.

**Supported narrow conclusion:** every visible word token, in exact case-sensitive order, inside these **two authenticated original authoring OSIS chapters** is accounted for by its *actual genuine distributed* K and chapter I raw XML entries. The previously unexplained beginning-of-chapter 149/170-word spans were in the separate compiled introduction slots, **not lost from the original MHC 2.2 SWORD module**. That finding says nothing about whether an independent historic printed/CCEL edition contains additional Henry exposition beyond the original *publisher's OSIS source*. In particular, independently SHA-pinned **CCEL Psalm 7 exposition II** and **Acts 17 paragraph #17** remain absent as *complete exact passages* from the upstream authored OSIS, and their different-edition identities/rights are not resolved by OSIS→SWORD lexical coverage.

**Acceptance boundaries:** this compares **word tokens for two chapters**, not character-perfect spelling/whitespace/punctuation, inline Bible references/targets, notes, nested markup, paragraph and section ownership, chapter introductions of other chapters/books, book-level I, TOP metadata, a complete all-books transport proof, exact historical print edition or electronic derivative rights. The CI's read-only Xiphos/JSword checks are not genuine **corrected module graphical content** acceptance. No source, authorial prose, original XML, compiled SWORD ZIP, catalogue or release was modified; the PR stays draft/unmerged. The next **technical** stage is private, source-position-aware full character and punctuation comparison for these same original-authenticated scopes before extending a source-neutral method across the corpus.

## Original source/native **interior visible-character** parity — two chapters (2026-11-17)

**Real-source verification:** [authentic MHC upstream OSIS vs published SWORD job #134358154731](https://github.com/icfmp/Bible-Resources/actions/runs/44173332812/job/134358154731) **SUCCESS** on source revision `c15436d38c6bd720aedea8bf7fd96c75e2ebd917`, with **20/20** source-neutral synthetic tests successful. The same previously authenticated source, published MHC 2.2 original ZIP, real SWORD K/I/TOP inventory and original raw corpus hashes were independently rechecked; no source words, XML, reader keys or binary were exported to reports.

For **each original whole K and chapter-specific I body uniquely placed inside its genuine original authoring-OSIS chapter**, the private inspector derived the visible text of that precise complete native raw XML fragment and independently isolated the source original visible-character interval **from its first matched whole word token to its final matched whole word token**. It then compared the actual unmodified character streams, case-sensitively, with a separate classification for whitespace-only differences. Character matching is *anchored to the complete exact original word sequence and unique original chapter-source position*, not an eight-word sample or a neighboring verse guess.

| Original source chapter | Native original K bodies — exact internal chars | K bodies — only whitespace differs internally | K bodies — interior punctuation/nonword difference | Chapter-specific original I — exact internal chars |
| --- | ---: | ---: | ---: | ---: |
| **Psalm 7** | 0 / 2 | **2 / 2** | **0 / 2** | **1 / 1** |
| **Acts 17** | 0 / 5 | **5 / 5** | **0 / 5** | **1 / 1** |

This is a new, independent **interior visible-character** acceptance for these **nine genuine source-located native bodies**. All authored original source *word tokens* across both complete chapters were already independently reconciled, with separate exact K/I source intervals and no uncovered words, as documented above. Here, all seven compiled K bodies preserve all **interior punctuation and nonword characters after whitespace collapsing**, while the two chapter I bodies are **exact character matches within their first-to-last visible word boundaries**.

**Critical boundaries:** the method expressly **excludes nonword punctuation and whitespace preceding the first/following the last word of each native body**, and does not compare XML element structures, original `osisRef` attribute values/target behavior, inline notes, footnote attribution, or authorial `p`/section divisions. Therefore this is **not** proof of complete byte/character/markup/annotation parity or even full boundary punctuation identity. Actual book-wide introductions and TOP records are not mapped here. Most importantly, upstream original authoring OSIS vs separately prepared CCEL/printed-edition wording, electronic rights and genuine corrected Xiphos/AndBible GUI acceptance remain independent unsatisfied requirements. No text, source XML, SWORD module, publication catalogue or release changed. The private read-only PR remains draft/unmerged.


## Seven authentic OSIS chapters — native bodies and inline link attributes (2026-11-17)

**Real-source run:** [source vs genuine stock-MHC native job #134369854209](https://github.com/icfmp/Bible-Resources/actions/runs/44177283661/job/134371951060) — **SUCCESS** at source commit \`b680a81912f29202db0bc40312f9b21e4d7051ef\`, with **22/22** independently constructed source-neutral unit tests passing. Official CrossWire authoring OSIS and unchanged published MHC 2.2 original zCom4 were separately hash-pinned, and the **32,355-entry** original K/I/TOP inventory was read as genuine native raw payloads. The seven chapter scopes were bounded by actual single start/end chapter milestones in 66 genuine source book divisions. Five chapter samples were selected via the reviewed source manifest; Psalm 7 and Acts 17 retain their separately source-pinned CCEL case identifiers.

| Authored OSIS chapter scope | Authored visible word tokens | Distinct original native K entire exact word bodies / tested | Source words not covered by K | Chapter-I outcome | Inline \`osisRef\` attributes equal, exact full ordered strings |
| --- | ---: | ---: | ---: | --- | ---: |
| Ps.7 | 3,686 | 2/2 | 149 | 149/149 prefix words exactly present | 33/33 |
| Acts.17 | 15,712 | 5/5 | 170 | 170/170 prefix words exactly present | 89/89 |
| Gen.1 | 18,344 | 10/10 | **0** | Original chapter-specific I **not** a whole exact source-chapter sequence; separately audited | 186/186 |
| Ps.23 | 3,356 | 1/1 | 221 | 221/221 prefix words exactly present | 27/27 |
| Isa.53 | 9,307 | 3/3 | 312 | 312/312 prefix words exactly present | 89/89 |
| John.3 | 17,727 | 2/2 | 68 | 68/68 prefix words exactly present | 176/176 |
| Rev.22 | 2,820 | 3/3 | 41 | 41/41 prefix words exactly present | 12/12 |
| **Seven-chapter sample** | **70,952** | **26/26** | **961 before I** | **Zero original chapter words missing from uniquely positioned K or K+I** | **612/612** |

**What was actually compared:** the private probe placed each genuine distinct full native K body at a unique exact case-sensitive contiguous word-token location in its *own* authored OSIS chapter. None of the 26 K-body intervals overlaps. Their internal visible punctuation/nonword characters show **zero discrepancies** (internal whitespace-only differences on all K bodies). For the six source-located chapter I bodies, the full first-to-last-word interior visible character stream matches exactly. Together, source coverage is complete for all seven samples (for Gen.1 the 10 genuine K bodies alone cover all source words). The private link-target extension collects each original chapter's actual \`reference/@osisRef\` values **including their order and empty values**, then compares exactly the fully ordered target string sequence with only uniquely source-located native K/I bodies. All **612 original chapter inline reference targets** were identical in native payloads. Both ends' complete ordered sequences are SHA-256 length-framed without logging the actual strings; synthetic negative tests detect a one-character target change. This is **not** a test that a target resolves in every viewer or that *all* other XML attributes, footnotes and paragraph boundaries match.

**Gen.1 distinct stock chapter-I witness, preserve as-is.** The original genuine native \`I\` for Genesis 1 does not have a whole-body exact word-token interval inside the original authored Gen.1 OSIS chapter. A second in-process probe examined the exact source book structure *before its first actual chapter milestone*: **zero authored visible words** precede Gen.1 in its official book div, so no prechapter authoring-text match exists. Gen.1 K already accounts for all **18,344** original chapter words. This exposes a **separate stock introduction of undetermined origin/ownership**, not a demonstrable missing, duplicate, or wrong authorial source entry. Do not remove, merge, reclassify, normalize or silently replace this stock I. Its origin, original editorial structure, potential book-level ownership and the role of generated importer text remain unproven.

**Important remaining gates:** a seven-chapter sample is not full 66-book/whole-corpus content parity; visible word+interior punctuation+inline reference-target parity does not establish boundary nonword punctuation, nested OSIS element structure, all notes, reference navigation, intro ownership, full native metadata, exact historical CCEL volume/printed editorial identity, redistribution rights, corrections, GUI-reader behavior or final release. The **independent CCEL Psalm 7 exposition II and Acts 17 paragraph 17** remain unconfirmed as complete authored stock/OSIS bodies and cannot be inserted without source/rights/editorial approval. No source words, native payloads or private verse keys were committed. This is research only; the original CrossWire module and catalogue are not edited, and [PR #286](https://github.com/icfmp/Bible-Resources/pull/286) remains draft.


## Three adjacent 2 Chronicles chapters — exact stock 2.2 source/native proof (2026-11-17)

**Actual pinned-source/real-native [CI job #134381341427](https://github.com/icfmp/Bible-Resources/actions/runs/44179916409/job/134381341427): SUCCESS** on SHA \`aac4626cef621be3893c8363717ef2eb8b7d8f8a\`, with **25/25 generic tests passed**, exact verified stock SHA and **full 32,355 original native K/I/TOP frame** inventory replayed. The original authentic CrossWire authored OSIS chapter milestones, not CCEL's *different digital edition's chapter annotations*, select these first-hand source scopes.

| Original CrossWire authoring chapter | Source words | Genuine distinct K complete exact case-sensitive whole-body source locations | Numbered occupied K verse slots | K-only source prefix words | Unique actual I covering prefix | Exact ordered inline \`osisRef\` values |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| \`2Chr.27\` | 1,173 | 1 / 1 | 9 | 120 | 1 / 1 | 16 / 16 |
| \`2Chr.28\` | 3,903 | 3 / 3 | 27 | 117 | 1 / 1 | 41 / 41 |
| \`2Chr.29\` | 4,787 | 3 / 3 | 36 | 165 | 1 / 1 | 43 / 43 |
| **All three contiguous chapters** | **9,863** | **7 / 7** | **72** | **402** | **3 / 3** | **100 / 100** |

**For each of these three complete authenticated authored OSIS chapter scopes**, all original visible word tokens are accounted for by exact, uniquely located genuine native K and original chapter I segments. No overlapping K source spans, case changes or interior punctuation/nonword discrepancies in the seven K bodies. All **100** source inline link-target attribute strings, in their exact authored order, are preserved by the genuine published native blocks; no source text, original reference target or read-only original binary was edited.

**Across all ten selected original authoring-OSIS chapters:** **80,815** original visible words, **33/33** distinct whole native K bodies exactly source-placed and internally punctuation-preserving, **712/712** ordered original inline \`osisRef\` attributes exact. All ten source word streams are completely explained by matched K and uniquely located chapter I, **or K alone for Gen.1**, whose extra genuine chapter I remains separate/unattributed. The sample was extended to ten under an explicitly tested hard cap of twelve; full native scan and independent ZIP/OSIS digests remain unchanged.

**Relevance to CCEL digital source discrepancy [#288](https://github.com/icfmp/Bible-Resources/issues/288):** CrossWire's independently pinned original authoring OSIS and published native MHC 2.2 **already agree on the three adjacent authentic chapter-owned textual scopes and link attributes**. The documented six original CCEL-volume-II \`scripCom\` labels pointing to the preceding chapters are a distinct **CCEL digital reference-index/edition** problem, not evidence of wrong CrossWire native chapter placement. These results do *not* rewrite or “correct” any CCEL original, do not identify CCEL original authorial edition with the CrossWire edition and are not full CCEL-to-CrossWire paragraph-identity or rights proof.

**Strict release gates remain:** this is a ten-chapter lexical/interior punctuation/reference-attribute sample, not all-source corpus parity, complete XML/heading/paragraph/footnote structure, working GUI link resolution, Gen.1 separate native I attribution, historically printed expository identity, derivative rights, authorial approval or release permission. The original MHC 2.2, original six CCEL volumes, public catalogue and binaries remain unchanged; draft [PR #286](https://github.com/icfmp/Bible-Resources/pull/286) stays unmerged.


## Complete visible non-whitespace character stream including native boundaries — ten chapters (2026-11-17)

**Real stock vs authoring test: [independent original OSIS/native job #134384579337](https://github.com/icfmp/Bible-Resources/actions/runs/44180839322/job/134384579337) — SUCCESS**, source branch revision \`3795a0d35d6cc3201c1c969e708ea86267d485fd\`. **27/27** source-neutral tests passed, including synthetic source/native end-boundary punctuation mutations that are independently detected and an unmatched genuine chapter-I that is explicitly excluded rather than silently reassigned. The original CrossWire OSIS and stock 2.2 ZIP were SHA-authenticated and the **entire 32,355 native K/I/TOP inventory** was independently reconciled again.

The audit first requires every **genuine unique K and source-matching chapter I** entire original visible-word sequence to have **one unique case-sensitive contiguous source location**. It then demands that the corresponding genuine native text segments, sorted by those independently established word offsets, form a **strict, gapless, non-overlapping partition of *every* original OSIS chapter visible-word position**. If there is any ambiguity, gap, overlap or missing original source character stream, it makes **no chapter-level equivalence claim**. For complete partitions only, the private runner joins **actual original native visible XML text**, retaining the native characters before the first word, after the last word and between adjacent K/I fragments, and compares this to the complete, authentic bounded chapter OSIS visible text. The **only transformation** for this comparison is removing Unicode whitespace on both sides, while preserving all other original characters, their spelling, case, punctuation, quotation marks, symbols and exact order. Both complete sequence lengths and SHA-256 digests are measured in private; only digests/counts/booleans are reported. Neither original word, original XML bytes, native raw payloads nor native verse addresses leave the private runner.

| Authenticated whole source chapter | Source complete visible non-whitespace characters | Actual native assembled complete visible non-whitespace characters | Whole non-whitespace character streams equal |
| --- | ---: | ---: | --- |
| \`Ps.7\` | 16,125 | 16,125 | **Yes, SHA-256 equal** |
| \`Acts.17\` | 69,238 | 69,238 | **Yes, SHA-256 equal** |
| \`Gen.1\` | 79,154 | 79,154 | **Yes, SHA-256 equal** |
| \`Ps.23\` | 14,073 | 14,073 | **Yes, SHA-256 equal** |
| \`Isa.53\` | 40,020 | 40,020 | **Yes, SHA-256 equal** |
| \`John.3\` | 76,843 | 76,843 | **Yes, SHA-256 equal** |
| \`Rev.22\` | 11,903 | 11,903 | **Yes, SHA-256 equal** |
| \`2Chr.27\` | 4,962 | 4,962 | **Yes, SHA-256 equal** |
| \`2Chr.28\` | 16,796 | 16,796 | **Yes, SHA-256 equal** |
| \`2Chr.29\` | 20,739 | 20,739 | **Yes, SHA-256 equal** |
| **Ten complete source chapter scopes** | **349,853** | **349,853** | **10/10 exact**, ignoring only whitespace |

**Strengthened specific acceptance:** these ten original authored OSIS chapters, representing **80,815 complete original visible word tokens**, **33/33** uniquely mapped distinct native K blocks, and **712/712** identical ordered \`reference/@osisRef\` target strings, also have **all original visible non-whitespace characters (including punctuation at individual native segment boundaries) preserved exactly in their genuine published native K and source-matched chapter-I payloads**. The proof applies to the original source-visible chapter scope, **not** the *entire* original SWORD module: the separately native original chapter-I attached to Gen.1 did not match any complete Gen.1 authoring chapter words and was **not included in the reconstruction**, since Gen.1 K alone already forms a strict exact source-word partition and the origin/role of its extra native I remains unresolved. No native original entry was changed or suppressed: exclusion here is only from the *research comparison*.

**Still strictly out of scope:** original XML tag nesting and element semantics, chapter-introduction/book-introduction attribution, note placement and paragraph/poetry/layout preservation (whitespace was ignored), functional \`osisRef\` navigation in actual readers, original authoring OSIS equivalence to separately digitized CCEL six-volume/historical print, possible independent CCEL exposition absent from CrossWire, exact derivative rights and full **66-book/whole-corpus** coverage. Do not present a ten-chapter sample as whole-source parity or as authorization to release/merge. This work is read-only; all CrossWire/CCEL originals, stock SWORD binary and public catalogue remain unchanged. [Draft PR #286](https://github.com/icfmp/Bible-Resources/pull/286) stays open.
