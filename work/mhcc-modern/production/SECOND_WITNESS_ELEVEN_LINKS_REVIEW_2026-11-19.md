# MHCC Modern English — independent secondary-witness check of 11 unresolved source links

**Date:** 2026-11-19  
**Scope:** editorial **review only**, on draft PR #272. This record supplements the immutable-source K/ordinal/target-hash inventory in [ADDITIONAL_ORIGINAL_LINK_TARGET_ERRATA_2026-11-18.json](ADDITIONAL_ORIGINAL_LINK_TARGET_ERRATA_2026-11-18.json). It does not replace that machine-checkable manifest.

## Method and limits

Each row below was checked against the **displayed printed cross-reference in the CCEL Concise Commentary**, without assuming the original compiled SWORD `osisRef` was correct. The original compiled target and source K/ordinal remain as pinned in the existing manifest. Exact text is **not** copied into this repository.

This is an additional **secondary digital witness comparison**, not a scan of a specifically identified historical print edition, a fresh hash-verification of the binary original, or an independent final semantic signoff. Matching CCEL and the modern translation may reflect shared digital ancestry; it cannot establish edition history. No hyperlink was retargeted, no authored manuscript or original MHCC was modified, no module was released, and no rights clearance is implied.

## Case-by-case evidence

| Source K / original link ordinal | Published native target | Printed Concise source context verified | Candidate derivative target | Disposition |
| --- | --- | --- | --- | --- |
| `Deut.9.1` #2 | `2Cor.11.12` | Deut 9:1–6 explicitly cites **Ephesians 2:9, 11, 12** ([CCEL](https://ccel.org/ccel/henry/mhcc.vi.ix.html)) | `Eph.2.11` and `Eph.2.12` (distinct citations) | Very strong digital-target mismatch; no application |
| `Esth.1.1` #2 | `2Cor.2.16` | Esther 1:1–9 prints **Habakkuk 2:15, 16** ([CCEL](https://ccel.org/ccel/henry/mhcc.xviii.i.html)) | `Hab.2.16` | Very strong digital-target mismatch; no application |
| `Gen.12.6` #2 | `Heb.13.14` | Genesis 12:6–9 prints **Hebrews 11:8, 13, 14** ([CCEL](https://ccel.org/ccel/henry/mhcc.ii.xii.html)) | `Heb.11.13` and `Heb.11.14` (distinct citations) | Very strong digital-target mismatch; no application |
| `Matt.5.43` #2 | `1Cor.1.16` | Matthew 5:43–48 prints **1 Peter 1:15, 16** ([CCEL](https://ccel.org/ccel/henry/mhcc.xxxii.v.html)) | `1Pet.1.16` | Very strong digital-target mismatch; no application |
| `Song.1.1` #5 | `2Cor.3.1` | Song introduction prints **Jeremiah 2:2; 3:1** ([CCEL](https://ccel.org/ccel/henry/mhcc.xxiii.html)) | `Jer.3.1` | Very strong digital-target mismatch; source-first-K introduction ownership must remain explicit |
| `Song.1.1` #6 | `1Cor.7.8` | Song 1 commentary marks the next section **Song 1:7, 8** ([CCEL](https://ccel.org/ccel/henry/mhcc.xxiii.i.html)) | `Song.1.7-Song.1.8` | Very strong digital-target mismatch; **section heading/transition**, not Henry's prose |
| `Jude.1.8` #2 | `Judg.1.17-Judg.1.23` | Jude 8–16 ends with the printed transition **“Jud 1:17-23”**, immediately before the next heading *Verses 17–23* ([CCEL](https://ccel.org/ccel/henry/mhcc.lvii.i.html)) | `Jude.1.17-Jude.1.23` | Strong contextual identification of Jude, **but abbreviated source label and structural transition** require explicit editorial review |
| `Matt.23.1` #2 | `Deut.9.13-Deut.9.21` | Matthew 23:1–12 gives phylactery passages **Deuteronomy 6:4–9; 11:13–21** ([CCEL](https://ccel.org/ccel/henry/mhcc.xxxii.xxiii.html)) | `Deut.11.13-Deut.11.21` | Very strong digital-target mismatch; ordinal #1 is a **different, already quarantined** anomaly |
| `Job.21.27` #2 | `1Cor.1.15` | Job 21:27–34 explicitly cites **Jude 1:14, 15** ([CCEL](https://ccel.org/ccel/henry/mhcc.xix.xxi.html)) | `Jude.1.15` | Very strong digital-target mismatch; no application |
| `Song.1.9` #1 | `1Cor.10.11` | Song 1:9–17 discusses ornaments and prints **Song 1:10, 11** ([CCEL](https://ccel.org/ccel/henry/mhcc.xxiii.i.html)) | `Song.1.10-Song.1.11` | Very strong digital-target mismatch; no application |
| `Num.29.1` #1 | `Lev.22.24` | **Both** published Concise print and original hyperlink say **Leviticus 22:24** ([CCEL](https://ccel.org/ccel/henry/mhcc.v.xxix.html)); the separate **full** Matthew Henry commentary says **Leviticus 23:24** ([complete witness](https://www.christianity.com/bible/commentary/matthew-henry-complete/numbers/29)) | `Lev.23.24` | **Source printed-reference discrepancy**, not a malformed digital conversion; no application |

## Editorial dispositions and safe next action

1. **Nine straightforward digital mismatches** have direct matching CCEL references in the same original commentary context; the existing manifest's source K, ordinal, literal label, original target SHA and proposed target remain authoritative for candidate implementation. *Do not apply automatically.*
2. **Jude 1:8 #2** also has strong support for Jude rather than Judges, but the location is an **editorial cross-section transition** and its printed abbreviation is `Jud`. Do not present it as a restored *authorial in-sentence biblical citation*. If approved, preserve its nature as a section transition.
3. **Numbers 29:1 #1** requires a different decision: a separately labeled correction to the **derivative** printed citation *and* destination, with the inherited Concise error retained in provenance; never silently reword the source or imply it was only a broken link.
4. The **four earlier malformed source targets**, **nine spurious digital markers**, and **0/1,189 independent original-native editorial approvals** are distinct from these eleven cases. They remain subject to the previously documented controls. Do not overstate the **1,180/1,204 currently navigable original occurrences** as full fidelity, GUI acceptance or rights clearance.

**Next gate:** obtain explicit editorial decisions for these eleven candidate corrections (especially the two structurally distinct cases); only then implement an isolated, reversible derivative overlay, run the existing real SWORD/source-hash validations, independently inspect Xiphos/AndBible navigation, and seek separate release authorization. PR #272 remains draft.
