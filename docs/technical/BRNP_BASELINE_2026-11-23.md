# BRNP source-only baseline — 2026-11-23

**Scope:** read-only diagnostics of the four approved cleaned OSIS masters against a preliminary BRNP 0.1 structure subset, with pinned official OSIS XSD checked independently. This is not a source-to-author collation, release approval, or authorization to rewrite a published master.

**Evidence:** [GitHub Actions run 45118704962](https://github.com/icfmp/Bible-Resources/actions/runs/45118704962), including per-edition machine-readable artifacts. Source files and compiled SWORD binaries were not modified.

| Cleaned OSIS | BRNP pilot findings | Classification |
| --- | ---: | --- |
| Louis Segond 1910 | 0 | No finding under the *currently implemented subset*; historical printed-edition verification remains separate |
| Darby JND 2024 | 0 | No finding under the implemented subset; not complete authorial fidelity certification |
| Matthew Henry Concise (MHCC) | 1 finding describing **2 unmatched chapter milestones** | Candidate conversion/markup defect; investigate and correct only with a source-hash-bound, reversible transformation |
| Matthew Henry Complete (MHC) | 1: no `div annotateType="commentary"` | **Representation difference**, not evidence that the commentary lacks verse scopes; map existing keyed OSIS verse ranges before requiring canonical commentary divisions |

## Direct source inspection of the two MHCC chapter-pair gaps

The actual approved cleaned OSIS Git blob `6ec0a78a41f75711e7be1a8885cf29c241228e88` has 1,189 OSIS `chapter sID` start markers and 1,187 `chapter eID` end markers. The two unpaired starts are:

- `1Sam.25`
- `Ps.95`

In both cases the chapter-level `div` is separately closed and the next `chapter` begins normally; the redundant chapter milestone itself lacks an `eID`. This was confirmed by examining the literal XML boundaries, not by assuming a verse was missing. Do **not** inject an `eID` directly into the released 0.1.1 source or claim this is a missing Scripture verse. A reviewed candidate must prove byte-identical visible text, unchanged note/reference anchors and correct SWORD round-trip before publication.

## Direct source inspection of MHC

The approved cleaned XML Git blob `654485d9a7ab31cbd238c7dd5afeda0c2c5ee7e3` has no `annotateType="commentary"` attributes. It uses OSIS `verse` milestones to scope passage commentary, including legitimate distinct canonical/pairing keys such as `osisID="Gen.1.1 Gen.1.2"` and `sID="Gen.1.1-2"`. The parser was corrected to **not** require that `sID` and `osisID` be identical. Thus 3,701 previously reported MHC mismatches were **validator false positives**, not source errors.

The remaining MHC finding is a BRNP canonical-commentary representation question. Its 4,256 authored commentary bodies and native verse/index evidence are separately documented in the existing MHC release record. Any migration must preserve authored passage coverage and test both SWORD navigation and current clients. Do not silently flatten ranges or reconstruct chapter comments as duplicated verse comments.

## Remaining acceptance tasks for #451

1. Complete a standard-derived hierarchy and semantic reference validator with deterministic diagnostics, before treating the BRNP subset as a conformance gate.
2. Demonstrate the two MHCC chapter closure repairs in an isolated, source-pinned candidate, and compare all authored content and native SWORD entries without republishing existing artifacts.
3. Establish one canonical commentary representation or an explicitly versioned and tested set of equivalent standard forms, including MHC verse-scoped and MHCC annotated-div inputs.
4. Independently verify historical authorial/edition witness fidelity, reader compatibility and preservation of existing published release bytes.
5. Obtain project-owner approval before making BRNP mandatory for all newly published resources.

**Status:** partial implementation with passing pilot tests and transparent open findings. This document must not be cited as full BRNP certification.

## v0.2-draft strictness audit and source-only regression (2026-11-23)

**Latest diagnostic evidence:** [BRNP advisory run #45122380252](https://github.com/icfmp/Bible-Resources/actions/runs/45122380252). The 34 positive/negative fixtures passed. This profile is **not** publication conformance; its limits and unresolved issues are explicit. Pinned official XSD validation runs independently before the BRNP inventory.

| Source | Findings | Independently classified meaning |
| --- | ---: | --- |
| LSG | 19,679 | All are `UNRESOLVED_REFERENCE_TARGET`: a `reference` element with no `osisRef`. Preserve labels; research exact historical cross-reference targets and independently verify before introducing links |
| Darby | 0 | No findings under implemented draft rules only; no authorial or full native certification implied |
| MHC | 11 | One noncanonical verse-milestone-only commentary scope (`NO_COMMENTARY_ENTRIES`), plus 10 `osisRef` values with surrounding whitespace; investigate source authority and SWORD behavior |
| MHCC | 529 | 264 repeated `div type="book"` and **the same 264 nested divisions** (two diagnostics per structural occurrence), plus one diagnostic for **two** unclosed chapter milestones |

The 529 MHCC findings do **not** mean 529 independent editorial errors. The exact two unclosed chapter starts are `1Sam.25` and `Ps.95`, documented above. The nested/repeated book structural discrepancies require checking the full subtree, note/reference associations, and original authored coverage before a reversible grouping transformation is approved.

**Controls added after the initial pilot:** duplicate canonical verse identifiers (including members of compound IDs); distinct milestone-key uniqueness for chapters and verses; correct Bible book and chapter ownership, including active chapter milestones; no nested books in the canonical representation; explicit detection of repeated commentary book divisions; standard table/list containment; grouping of poetry lines; unresolved cross-reference targets; and the existing reviewed commentary reference grammar, rather than a permissive second parser. The normalizer's optional BRNP diagnostic detects newly introduced finding classes/counts and blocks its *local candidate* when enabled. None of these checks silently rewrites a released resource.

**Acceptance boundaries:** A zero under these checks means *no findings in the implemented draft subset*, not independently verified printed-edition fidelity, reference target resolution, native SWORD parity, or reader acceptance. Do not suppress any findings to make this table green; create source-hash-bound transformation plans with full before/after equivalence evidence. No editorial/publishing sign-off is implied.
