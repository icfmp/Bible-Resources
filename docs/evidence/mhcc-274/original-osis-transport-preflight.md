# Original CrossWire commentary XML → OSIS reconstruction feasibility

**2026-11-14 — Research only.** Issue [#274](https://github.com/icfmp/Bible-Resources/issues/274), draft [PR #275](https://github.com/icfmp/Bible-Resources/pull/275).

**Do not use as a release or as an approved source edition.** The published BRMHCC
0.1.0, the exact original compressed CrossWire MHCC 2.0 module, all original
metadata and the paused modern-English edition are unchanged.

## Inputs and authenticated origin

Original stock archive, module ID, version and SHA-256 and full original
native stream are pinned in `config/commentary-intake/mhcc-crosswire.json`.
The existing independent stock index and full raw inspect tools are invoked
before this reconstruction feasibility assessment. No data here is derived
from an unverified webpage or an automatically invented scripture verse.

## First gate: all original native entries can be inspected

[Original full-source CI success #43628933967](https://github.com/icfmp/Bible-Resources/actions/runs/43628933967)
and [subsequent annotated metadata-only CI #43629393797](https://github.com/icfmp/Bible-Resources/actions/runs/43629393797):

| Observed original data | Count |
| --- | ---: |
| Independently indexed and SHA-validated native occupied records | 29,975 |
| Original K numbered key records | 28,718 |
| Original I introduction records | 1,255 |
| Original U opaque TOP records | 2 |
| Distinct original nonopaque raw XML bodies (SHA-256) | **5,302** |
| Other K/I keys repeating an identical native raw body | 24,671 |
| Distinct raw bodies parseable verbatim inside a standard OSIS section wrapper | **5,302 / 5,302** |
| Those bodies whose Unicode visible text remains exactly unchanged in wrapper | **5,302 / 5,302** |
| Those bodies retaining exact immediate child element names/counts | **5,302 / 5,302** |
| Distinct bodies containing nonwhitespace original direct element tails | 4,054 |
| Cross-chapter or cross-book identical raw-body groups | 0 |

The **1,255** introductions are **66 book introduction** and **1,189 chapter
introduction** native keys. The **two TOP records are 83 bytes each**, have
identical native raw bytes, parse as XML fragments with one element each, but
contain **no visible Unicode prose**. They are still source structure and must
be explicitly preserved, not omitted silently.

A syntactically valid OSIS wrapper is not equivalent to an authorially,
editorially or binary-preserving SWORD import. These findings prove only
safe *transport syntax and original Unicode text in the wrapper*.

## Second gate: private actual osis2mod original sample, no release

The generic `commentary_osis_transport_probe.py` creates a temporary OSIS
from verbatim original indexed K raw fragments. It groups only **consecutive
keys with exactly the same raw bytes**, without inferring authorial section
boundaries, and explicitly **excludes I/TOP** from this exploratory sample.
The original and candidate modules are separate and independently read by
libSWORD. Files containing source text are not attached to PRs or artifacts.

Tested exact selected complete original K chapters:
- `Gen.36` (single-entry whole-chapter pattern);
- `Matt.13` (multiple sections, including genuine discontiguous 24–30 and
  36–43 situation in the *heading* but original 36–43 keys are unoccupied);
- `Song.1` (original two-verse comma range index omission).

[First actual roundtrip CI #43629950079](https://github.com/icfmp/Bible-Resources/actions/runs/43629950079)
and [word/markup classification #43630294090](https://github.com/icfmp/Bible-Resources/actions/runs/43630294090)
**SUCCESS**:

| Probe outcome (67 originally occupied K keys) | Result |
| --- | ---: |
| All existing original sampled K keys found in the rebuilt sample | **67 / 67** |
| Missing original or added unexpected K keys | 0 |
| Original compiled raw XML byte-perfect equality | **0 / 67** |
| Original visible Unicode including exact whitespace equal | **0 / 67** |
| Original Unicode word tokens in identical order, case-insensitive | **67 / 67** |
| Original Unicode visible string equal after *whitespace only* normalization | **67 / 67** |
| Original element-name counts match exactly | **0 / 67** |

Therefore **the importer has changed the original XML representation**; the
sample does not show missing original words or misaddressed K verse indexes.
It **does not prove** source XML/markup, references, titles, notes, paragraph
layout or exact source punctuation parity. We must identify precisely which
element names or attributes changed and test whether SWORD roundtrip can
retain the originally sourced structure using a permitted standard OSIS
representation, without post-hoc "correction" that changes content.

**One severe hazard found in development:** a formatter inserted an
extra XML sibling newline during initial synthetic OSIS generation. Tests
failed because even that altered original visible text. The generator now
concatenates original XML without inserting any whitespace inside
commentary sections. This is a generic regression, not an MHCC exception.

## Remaining gates before any corrected module

1. Classify the actual original-versus-recompiled markup element and
   attribute differences. A word-preserving result is **not** sufficient.
2. Independently prove a valid, roundtrip-parity-capable standard OSIS
   representation of **all** original 29,975 entries, including the complete
   66 book and 1,189 chapter intros and both opaque TOP source records.
3. Keep original 17 index omissions / 24 missing canonical keys separate from
   118 whole-chapter reader-first extension candidates; match the original
   chapter authorial scope and prevent any overwrite or discontiguous gap fill.
4. Resolve separately the 25 original CCEL `scripRef` to compiled SWORD
   clickable target differences; **CCEL is an independent digital edition**,
   not necessarily a byte-identical origin for CrossWire stock.
5. Verify the one changed word outside the CCEL citation labels (1 Chr 7)
   and source paragraph/notes/title and all cross-reference semantics.
6. Build a **new isolated, separately identified** candidate with exact
   original readback proof and one independent reader smoke test, including
   deduplicated single-comment display; no automatic release or merge.

Modern-English MHCC #270 and #272 remain paused pending real editorial
source validation. No source authorial bytes or published module were edited.
