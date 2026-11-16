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
