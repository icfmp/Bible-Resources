# HMCC Modern — final editorial decision packet (not authorization)

**2026-11-19 — PR #272; strictly review-only.** This file identifies **15 pinned original-source hyperlink anomalies** and **two published-SWORD content gaps** so a single editorial decision can be made after technical reader tests. Nothing in this packet changes source manuscripts, navigation targets, visible citations, release metadata or rights. Source identities and exact hashes remain in the previously committed machine-readable manifests.

## A. Seven ordinary digital-target mismatches — recommend correcting *navigation only* in the derivative

| Original source K / reference ordinal | Incorrect published destination | Evidence-supported derivative destination |
| --- | --- | --- |
| `Deut.9.1` #2 | `2Cor.11.12` | `Eph.2.11` + `Eph.2.12` as distinct references |
| `Esth.1.1` #2 | `2Cor.2.16` | `Hab.2.16` |
| `Gen.12.6` #2 | `Heb.13.14` | `Heb.11.13` + `Heb.11.14` |
| `Matt.5.43` #2 | `1Cor.1.16` | `1Pet.1.16` |
| `Song.1.1` #5 | `2Cor.3.1` | `Jer.3.1`, in book-introduction context |
| `Matt.23.1` #2 | `Deut.9.13-Deut.9.21` | `Deut.11.13-Deut.11.21` |
| `Job.21.27` #2 | `1Cor.1.15` | `Jude.1.15` |

**Proposed decision A:** approve seven individually source-pinned corrections to **derivative link destination only**, preserving the existing visible source-labelled text and noting where modern editorial structure relocates the link. For original references printing several disjoint destinations, supply distinct links; never claim the source had an identical clickable span.

## B. Three section-heading / transition links — recommend making them structural navigation, not invented authorial prose

| Original K / ordinal | Wrong original link | Correct documented scope |
| --- | --- | --- |
| `Song.1.1` #6 | `1Cor.7.8` | Song 1:7–8 section transition |
| `Song.1.9` #1 | `1Cor.10.11` | Song 1:10–11 outlined subsection |
| `Jude.1.8` #2 | `Judg.1.17-Judg.1.23` | Jude 1:17–23, printed abbreviation `Jud` |

**Proposed decision B:** approve the corrected passage scopes **as section navigation** with independently labelled provenance, retaining the exact original heading/abbreviation. Do not transform the source's ambiguous `Jud` into an unmarked quotation or assert a different original inline phrase.

## C. Two original *printed* citation defects — recommend an explicitly marked modern-edition correction

| Original K / ordinal | Printed/clickable original | Proposed derivative editorial correction |
| --- | --- | --- |
| `Num.29.1` #1 | Lev 22:24 / `Lev.22.24` | Lev 23:24 / `Lev.23.24` |
| `Eccl.10.11` #1 | Isa 25:8 / `Isa.25.8` | Isa 35:8 / `Isa.35.8` |

**Proposed decision C:** authorize *both* a revised **visible printed citation** and a revised destination **in the modern derivative only**, with a clearly documented erratum referencing the unchanged original. This is a meaningful editorial intervention, not just OSIS repair. Retain the original printed/source value in the audit record and allow rollback.

## D. Three malformed composite source links — recommend explicit disjoint passage navigation

| Original K / ordinal | Invalid original target | Source-supported passages, never a fabricated continuous range |
| --- | --- | --- |
| `Jer.50.1` #1 | `Jer.50.1-Jer.3.8` | Jer 50:1–3; 8–16; 21–32; 35–46 |
| `Jer.50.1` #2 | `Jer.50.4-Jer.7.17` | Jer 50:4–7; 17–20; 33–34 |
| `Matt.23.1` #1 | `Exod.13.2-Exod.10.13` | Ex 13:2–10; 13:11–16; Deut 6:4–9; 11:13–21 |

**Proposed decision D:** permit independently addressable sub-ranges **attached to the original composite outline** in the derivative, without inventing one impossible OSIS span or pretending the source contained several separate link elements. Each target must exist and be click-tested in Xiphos before acceptance. Preserve exact original printed outline and original markup in provenance.

## E. Two original compiled-SWORD coverage gaps

- **1 Samuel 25:39–44.** Original compiled MHCC 0.1.1 body for 32–44 matches the CCEL 32–39 source exposition word-for-word in the previous bounded witness alignment, but **does not contain** the separately attested 39–44 exposition. The modern translation manuscript includes the CCEL-only material; the conservative private SWORD candidate excludes it.
- **Psalm 95:7–11.** Similarly, the compiled original 1–11 body matches the CCEL 1–7 unit, but the distinct 7–11 exposition is absent from the original compiled SWORD body. The modern manuscript includes it; the private source-strict candidate excludes it.

**External corroboration:** the two concise passages appear in CCEL and other contemporary distributions of the **Concise** work, e.g. https://www.christianity.com/bible/commentary/matthew-henry-concise/1-samuel/25 and https://www.biblestudytools.com/commentaries/matthew-henry-concise/psalms/95.html. Different websites can still share a digital ancestor; this does not prove a particular historic print exemplar.

**Proposed decision E:** approve **restoring both separate authored concise passages to the final modern derivative**, as explicitly attributed secondary-source restorations, rather than falsely presenting them as translated from the immutable 0.1.1 native K bodies. Preserve modern manuscripts and full original original-SWORD K spans; the build must prevent overlap/duplicate reader output and require verified distinct authored placement.

**Rights distinction:** Matthew Henry's historic prose is public domain, and CrossWire explicitly distributes its *Concise* text as Public Domain (https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC). This does **not** grant an automatic license for original new modern translations, CCEL-specific added editorial prose/markup, or any modern introduction. Before publication, pin the edition and exclude any independently protected editorial apparatus. Modern derivative metadata must accurately identify this mixed-source provenance. Public-domain status of the underlying Henry passages alone is not a finding that every supplied CCEL package element is unrestricted.

## Approval and implementation sequence

1. Record a **separate explicit accept/reject** for A, B, C, D and E; retain individual hash-pinned link records for each of the fifteen cases and separate source-provenance identifiers for both restored sections.
2. Implement approved changes **only in an isolated reversible derivative overlay**; original published MHCC 0.1.1, historical BRMHCC, and original modern manuscript snapshots must remain immutable. All approved edits need a human-readable before/after provenance ledger and source-linked tests.
3. Run raw OSIS structure, full native K/I exact key/link accounting, SWORD compilation, source label integrity, real Xiphos reader click/navigation checks (each approved new target; no missing GUI proof as PASS), introduction/chapter-only regression checks, and the strict repository tool registry/Validate gates.
4. Do not merge, distribute binaries or edit the public catalogue without a separate final release approval.

### Technical acceptance distinction

The 2026-11-19 Xiphos readback and HTML anchor evidence is **not** a real mouse-click navigation pass. The newer full eleven-case GUI sampling must be assessed from its own GitHub Actions run and per-case metadata. If a source error is still quarantined, it is *not* an approved correction. Do not count independent editorial acceptance as completed merely because the translate → verify cycle for 1,189 modern chapter manuscripts has finished.

**Current editorial state: A–E proposed, not approved.**
