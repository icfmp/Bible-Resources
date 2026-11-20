# MHCC Modern English — Ecclesiastes 1–12 focused fidelity review

**Date:** 2026-11-19  
**Branch:** `feature/mhcc-modern-english`, draft PR #272  
**Scope:** all twelve existing Modern English Ecclesiastes manuscripts (Eccl.1–12) compared to the full online [CCEL *Concise Commentary* Ecclesiastes](https://ccel.org/ccel/henry/mhcc.xxii.html) witness.

## Method and source limits

Reread each of the original English authored verse-range sections against its already-translated modern draft, paying particular attention to explicit eschatological terms, divine agency, judgment terminology, historical qualifications, source divisions and Scripture links. This CCEL witness is **secondary**; publication source of record is the unchanged, released, SHA-pinned `MHCC 0.1.1` compiled SWORD edition. Do not mistake a matched lexical phrase for full original-source textual, markup, references, note or semantic acceptance. All edits below are **draft-only, individually reversible and subject to independent review**.

| Chapter | Result |
| --- | --- |
| Ecclesiastes 1 | Compared; no new substantive amendment |
| Ecclesiastes 2 | **Corrected draft**: in 12–17, restore Henry's explicit **soul in hell** alongside the body in the grave, rather than generic *soul under judgment* |
| Ecclesiastes 3 | Compared; no new substantive amendment |
| Ecclesiastes 4 | Compared; no new substantive amendment; keep five original source sections |
| Ecclesiastes 5 | Compared; no new amendment; existing documented draft outline correction **9–7 → 9–17** is a **separate preexisting editorial decision**, original printed label not silently rewritten |
| Ecclesiastes 6 | **Corrected draft**: in 1–6, restore Henry's explicit claim that **the Lord may leave** a wealthy person to covetousness/evil disposition rather than deleting the divine agency |
| Ecclesiastes 7 | **Corrected draft**: in 11–22 restore **dread of hell**, physical/economic consequences and **public justice**, not generic *judgment* and *reputation* |
| Ecclesiastes 8 | **Corrected draft**: in 9–13 restore Henry's **vengeance comes slowly but surely**, rather than generic delayed judgment |
| Ecclesiastes 9 | Compared; no new substantive amendment |
| Ecclesiastes 10 | **Corrected draft**: in 16–20 restore the contrasted **his curse** and **lowest hell** instead of generic *judgment* and *eternal destruction* |
| Ecclesiastes 11 | Compared; no new substantive amendment |
| Ecclesiastes 12 | Compared; no new substantive amendment |

**Five distinct draft chapters amended, seven unchanged.** Each of the five has a dated editorial note, direct CCEL citation and reversible original Git file history. No blanket replacements were made.

## Source-linked reference anomaly not altered

**Ecclesiastes 10:11–15** in the original Concise printed witness has **`Is. 25:8`**, while the statement about a highway for inexperienced travelers suggests **Isaiah 35:8**. This is one of the original link-error review cases already quarantined in [the source errata manifest](ADDITIONAL_ORIGINAL_LINK_TARGET_ERRATA_2026-11-18.json) or its separate four-link predecessor, **not** a simple typo licensed for automatic correction. No source `osisRef`, printed citation, modern reference or corresponding navigational target has been edited here. The separate original-versus-proposed erratum review and owner approval remain required.

## Native source K evidence and verification gate

The five affected original source sections are independently identified by first and last original K keys and exact SHA-256 original K-body identities extracted from the existing successful full-canon native-source GitHub Actions receipt:

- `Eccl.2.12–17`
- `Eccl.6.1–6`
- `Eccl.7.11–22`
- `Eccl.8.9–13`
- `Eccl.10.16–20`

Ten short secondary-witness lexical anchors are recorded in [the scoped JSON witness manifest](ECCLESIASTES_NATIVE_FIDELITY_SOURCE_ANCHORS_2026-11-19.json), and the **existing source-neutral private source-probe** is now invoked from the full MHCC source-receipt workflow against the SHA-pinned released `MHCC 0.1.1`. Its expected result is **five original K groups and ten attested anchors**, tested in private with no original authorial prose or raw XML emitted to public logs. This is **not** an independent meaning or copyright approval; do not report the check as passed until the GitHub run on the relevant head succeeds.

## Secondary English witness links

[1](https://ccel.org/ccel/henry/mhcc.xxii.i.html) ·
[2](https://ccel.org/ccel/henry/mhcc.xxii.ii.html) ·
[3](https://ccel.org/ccel/henry/mhcc.xxii.iii.html) ·
[4](https://ccel.org/ccel/henry/mhcc.xxii.iv.html) ·
[5](https://ccel.org/ccel/henry/mhcc.xxii.v.html) ·
[6](https://ccel.org/ccel/henry/mhcc.xxii.vi.html) ·
[7](https://ccel.org/ccel/henry/mhcc.xxii.vii.html) ·
[8](https://ccel.org/ccel/henry/mhcc.xxii.viii.html) ·
[9](https://ccel.org/ccel/henry/mhcc.xxii.ix.html) ·
[10](https://ccel.org/ccel/henry/mhcc.xxii.x.html) ·
[11](https://ccel.org/ccel/henry/mhcc.xxii.xi.html) ·
[12](https://ccel.org/ccel/henry/mhcc.xxii.xii.html).

## Next editorial and technical gates

1. Confirm all five original-source K anchor probes and investigate any source-vs-CCEL lexical disagreement before accepting a repair.
2. Independently collate exact `MHCC 0.1.1` original K/I wording, linked references, source notes, headings and paragraph markup against each derivative unit.
3. Confirm compiled whole-canon modern OSIS → SWORD native readback and actual reader GUI acceptance, without merging or publishing a draft.
4. Resolve redistribution rights and obtain separate project-owner release approval.

The original `MHCC 0.1.1` module, source links, verse keys, Bible app and public catalogue remain unchanged. The project still has **0/1,189 independently signed-off chapters**; the existing 165/176 source-link recovery and 11 withheld candidate errors are unaffected. PR #272 remains **draft, unmerged, unpublished**.
