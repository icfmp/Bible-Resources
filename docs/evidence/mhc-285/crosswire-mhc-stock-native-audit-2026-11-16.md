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
