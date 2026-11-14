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


## Third gate — source-word, markup and citation-attribute preservation in actual temporary sample

The sample's discrepancies were refined on complete exact-head
[CI #43630794830](https://github.com/icfmp/Bible-Resources/actions/runs/43630794830)
**SUCCESS** with 45 generic editorial tests, 18 link-plan tests,
13 original-structure transport tests and 10 numbered OSIS transport tests.
On exact code/docs head
`8c7fc6432a8c20df5609abce0856a06004781bd0`, the other five project
quality actions also report **SUCCESS**:
[Validate #43630794837](https://github.com/icfmp/Bible-Resources/actions/runs/43630794837),
[original stock text #43630794812](https://github.com/icfmp/Bible-Resources/actions/runs/43630794812),
[full raw census #43630794829](https://github.com/icfmp/Bible-Resources/actions/runs/43630794829),
[reference targets #43630794873](https://github.com/icfmp/Bible-Resources/actions/runs/43630794873)
and [original source/native index #43630794930](https://github.com/icfmp/Bible-Resources/actions/runs/43630794930).

The **67 original native K keys all survive with no extra K keys**;
raw XML bytes and exact literal whitespace differ, but the **same original
Unicode words in the same sequence** and **the identical original Unicode
text after only whitespace normalization** appear in every rebuilt key.
The extra markup is isolated:

| Observed XML element | Original occurrences in the 67 sampled entries | After `osis2mod` |
| --- | ---: | ---: |
| `div` | **917** | **1,089** |
| `cell` | 138 | 138 |
| `chapter` | 16 | 16 |
| `hi` | 66 | 66 |
| `reference` | **58** | **58** |
| `row` | 69 | 69 |
| `table` | 69 | 69 |
| `title` | 49 | 49 |

**In all 67 entries**, the original non-`div` element order **and all
literal attribute values** match; every original `div` has its original
attribute-value multiset represented in the compiled entry; and the entire
original ordered sequence of `reference` attribute values (including actual
`osisRef` destinations) is **unchanged**. The converter added **172**
`div` wrapper elements but **did not drop/rename/alter another original
element name or attribute** in this sample.

This is much stronger evidence that the compiler's difference is **structural
wrapping / whitespace**, rather than altered source words, hyperlink targets
or missing notes. However this sample has no proof of the full source
paragraph semantics in all 5,302 distinct bodies; added wrappers may affect
reader layout and de-duplication even when every word and attribute survives.

**Explicitly not proven:** complete 29,975-key parity; 1,255 I introduction
entry provenance; two opaque 83-byte TOP fragment locations; source
to print-edition parity; 17 index repair scopes; 118 whole-chapter
access proposals; 25 CCEL `scripRef` annotation gaps; font/paragraph
rendering in a real independent reader. All remain separate acceptance
gates. The complete original MHCC compressed module and published BRMHCC
0.1.0 remain unchanged, as do #270/#272.


## Fourth gate — complete original book/chapter intro and opaque TOP structural provenance

[Exact-original complete native audit #43631093133](https://github.com/icfmp/Bible-Resources/actions/runs/43631093133)
**SUCCESS** and 45 editorial, 18 link-plan, 13 native reconstruction-structure
and 10 compiled sample tests passed on the exact original SHA-pinned corpus.

The intros and TOP must be treated as **independent first-class indexed
SWORD records**, not discarded or guessed from the 28,718 K entry texts.

Original intro records:
- **66 book intro keys**, **1,189 chapter intro keys**.
- Their top-level parsed XML children, preserving all original element
  names (counts across 1,255 source entries): **1,191 `chapter`**,
  **1,957 `div`**, **198 `milestone`**, **7 `title`**.
- **None** has unwrapped leading visible text before its first XML child.
- All are included in the 5,302 original distinct safely parsable K/I XML
  bodies; no published source content was rewritten.

Original TOP records:
- **2 indexed opaque TOP** entries, each with **83 exact original bytes**,
  the same raw SHA-256, and exactly **one `milestone` XML element**.
- Each original `milestone` has the original attribute-name set
  `n`, `subType`, `type`; no visible Unicode words.
- Their original byte-level and XML attribute-value identity remains
  an explicit full-rebuild readback gate. A lack of prose does not make
  an indexed structural milestone disposable.

**Technical implication:** a naive K-only `osis2mod` reconstruction is
inadequate even if the 67 sampled K entry words and attributes survive.
The full edition requires a source-faithful way to restore book/chapter
introduction locations and the two structural TOP positions, while not
duplicating the existing intro markup within a newly generated OSIS
book/chapter wrapper. It also requires roundtrip testing against
all 29,975 original native occupied K/I/U entries.

**No complete replacement module has yet been generated.** This is an
inspection and standard compiler feasibility gate, not publication or an
approved editoral change.


## Complete 29,975-entry standard SWORD rebuild — source-constrained research gate (2026-11-14)

[Exact-head isolated original-stock audit #43644376840](https://github.com/icfmp/Bible-Resources/actions/runs/43644376840)
**SUCCESS**, original full-module implementation head
`4d15e918cdecab6dbb322275918c580fc662ef6a`.

The existing original source-native reader streamed every original, SHA-pinned
CrossWire MHCC 2.0 raw native record. A **temporary, separately identified**
zCom source candidate was compiled with the standard `osis2mod` importer
from the **unchanged original I and K fragments**, arranged in their
verified KJV book/chapter and occupied-verse order. The two opaque original
TOP fragments were **not inserted or synthesized by custom index patching**;
the standard compiler generated them, and the independently run native reader
checked their exact original bytes and indexed order.

| Native entry class | Exact original | Candidate readback | Missing | Additional | Content/markup gates |
| --- | ---: | ---: | ---: | ---: | --- |
| Numbered K | **28,718** | **28,718** | **0** | **0** | **28,718/28,718** |
| Book/chapter I | **1,255** | **1,255** | **0** | **0** | **1,255/1,255** |
| Opaque TOP U | **2** | **2** | **0** | **0** | **exact original bytes 2/2** |
| **Total indexed** | **29,975** | **29,975** | **0** | **0** | **all source-constrained checks passed** |

Every I/K entry retained: exactly the original **ordered Unicode word sequence**,
the same **visible Unicode text except for whitespace normalization**
(including punctuation), original ordered non-`div` element names and
literal attributes, all original `div` attribute-value multisets, and
all original ordered citation `reference` attribute values (including
`osisRef`). Every original I/K native key was present and no extra I/K
key appeared. The source fragments were incorporated **verbatim** in the
private OSIS generation step, with no word, heading or navigation correction.

**Precisely what this proves:** the released standard SWORD importer can
reconstruct all original indexed locations of this commentary with the
specified **source-semantic readback invariants** and original TOP bytes.
This is now a full-corpus **technical transport** result, no longer just a
chapter sample.

**Precisely what it does not prove:** original raw XML *byte equality*
(the compiler adds `div` wrappers and normalizes whitespace); absolute
reader-layout/paragraph presentation equivalence; historical print-edition
identity; independent editorial section boundaries or the correctness of
CrossWire's 17/24 omitted keys, 118 single-key chapter scopes, two
intro-text-only chapters, CCEL citation-target differences, and 1 Chr 7
digital-witness wording difference. These remain **separate editorial and
reader acceptance gates**. The tested candidate did not attempt any
section repair, add unverified aliases, alter original stock, or publish.

**Next:** use the demonstrated complete-source transport as the strictly
isolated baseline for reviewed non-overwriting section-link adjustments;
read back every original K/I/U record plus any approved new aliases,
verify that no newly linked verse overwrites a distinct commentary section,
then check one real reader for section deduplication and actual references.
Do not merge or release before full editorial decisions and explicit owner
approval. Modern-English #270/#272 remains paused.
