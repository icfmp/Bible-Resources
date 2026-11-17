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
