# MHCC — Original native introduction text ownership audit

**2026-11-14 · Editorial research only, not a corrected edition.**  
Tracker: [#274](https://github.com/icfmp/Bible-Resources/issues/274). Branch: `audit/mhcc-editorial-section-scope`, draft PR [#275](https://github.com/icfmp/Bible-Resources/pull/275).

## Proven stock SWORD facts

All source data was privately read from the original SHA-pinned CrossWire MHCC
2.0 full native libSWORD stream. No authorial text or full XML fragment was
logged, modified, exported or republished.

- 29,975 occupied native records: **28,718 numbered K**, **1,255 introductory I**, **2 opaque U/TOP**.
- **1,243 I entries** contain no Unicode word tokens. **12** contain
  visible words. Of the 12, five are short **book-level titles** and seven
  are **chapter-level** records.
- The two 83-byte original U/TOP raw XML payloads match **byte-for-byte**
  the single standard `osis2mod`-generated U/TOP marker in the independent
  invented `IntroProof` module. [Complete audit #43632888346](https://github.com/icfmp/Bible-Resources/actions/runs/43632888346)
  PASS with 45 generic editorial, 18 navigation, 16 intro-structure
  and 10 real OSIS sample tests. This proves the *raw payload* is a
  standard compiler-generated structural milestone; **original two TOP
  positions are not yet reconstructed**.
- Synthetic standard `osis2mod` IntroProof generated **three original-style
  I keys**, `Gen`, `Gen.1`, `Gen.2`, and one U/TOP marker. The two
  chapter intros and book intro had visible invented text. This proves the
  standard API supports independent I records and does not force intro text
  into K verse slots. Do **not** conclude an OSIS source faithfully matches
  the original full corpus based solely on this synthetic behavior.

### All 12 original I entries with visible text

| Native I key | Unicode words | Existing *distinct* K commentary bodies in same chapter | Intro text owner |
| --- | ---: | ---: | --- |
| `2John` | 2 | n/a — book title | `title` |
| `3John` | 2 | n/a — book title | `title` |
| `Jude` | 1 | n/a — book title | `title` |
| `Obad` | 1 | n/a — book title | `title` |
| `Phlm` | 1 | n/a — book title | `title` |
| `2John.1` | 71 | 4 | after `div` |
| `3John.1` | 27 | 3 | after `div` |
| `Jude.1` | 106 | 5 | after `div` |
| `Lev.19` | **698** | **0** | after `div` and `title` |
| `Obad.1` | 32 | 2 | after `div` |
| `Phlm.1` | 117 | 4 | after `div` |
| `Ps.108` | **136** | **0** | after `div` and `title` |

Original complete native text-to-chapter-slot comparison:
[GitHub Actions #43633243190](https://github.com/icfmp/Bible-Resources/actions/runs/43633243190) **SUCCESS**.
The body of each of the seven chapter-level I entries is **not wholly
duplicated as a K body**. In five single-chapter books the original I
record coexists with one or more distinct K comments. For **Lev.19** and
**Ps.108**, **zero numbered commentary K entries** exist in the original
module for that chapter, even though a substantial original I record
contains visible commentary text. The native introduction text is **not
absent from the module**; whether it is intended as an author's entire
chapter commentary and ought to be navigable from all verses requires
independent editorial source assessment.

The automatic scope proposal must **not** move the original I text
silently into verse 1, delete it, create imaginary distinct verse-by-verse
expositions, or infer that a title/reference nearby authorizes full-chapter
linking. If a source-authenticated *chapter-wide commentary* is established,
add reader navigation without loss, and verify separately that opening the
original book/chapter introduction still displays the original prose.

## Next gates

1. Match each substantive original I entry to the separately pinned CCEL
   ThML **chapter** `scripCom` annotation and the actual source text.
   Different digital editions do not automatically have identical strings.
2. Determine whether the original source treats Lev 19 and Psalm 108 as
   complete chapter comments, verse-section comments, or editorial prefaces.
3. Test original I and TOP readback in a disposable complete-source OSIS
   candidate. The former sample tested only 67 numbered K keys and omitted
   all intro and TOP positions.
4. Require full original native K/I/U value and location reconciliation,
   original XML attributes/paragraphs/notes/reference targets, no
   overwrites, and independent reader display/deduplication checks.
5. Hold publication and modern-English #270/#272 until an actual reviewed
   resource is validated.

No original source, installed source, released BRMHCC or published asset
was altered.


## Independent CCEL book/chapter-correlated evidence

[Complete native + source witness test #43634072027](https://github.com/icfmp/Bible-Resources/actions/runs/43634072027)
**PASS**, with all 47 section tests, 18 navigation tests, 16 structural
transport tests, 6 intro text-location tests and 10 numbered OSIS tests.

Neither source chapter contains a directly usable *chapter-wide*
`scripCom` marker. The source therefore cannot be assigned merely by
looking for `scripCom osisRef="Bible:Lev.19"`. The *existing* strict
source `div1` book title and native book/code verification, full source
chapter division count and source `div2` chapter mapping were reused
instead — not an arbitrary ordinal or scripture citation fallback.

| Original I key | Verified source book/chapter location | Source verse-section markers | Word alignment in differently published CCEL witness |
| --- | --- | ---: | --- |
| `Lev.19` | source book title **and** book markers match; chapter ordinal safe | 0 | **same complete ordered Unicode word sequence** |
| `Ps.108` | source book title **and** book markers match; chapter ordinal safe | 0 | **at least 95% lexical overlap**; one or two source words not matched in the strict ordered comparison |

Both texts are genuinely present at an original native chapter-introduction
key but **have no K-keyed commentary entries at all** in their chapter.
The original native KJV verse registry verifies **37** verse references in
Leviticus 19 and **13** in Psalm 108. If independent editorial review
establishes that each original passage represents the whole-chapter
commentary, these are **50 potential new reader navigation targets**, not
50 distinct commentary expositions, no proof of a source verse loss, and no
permission to remove or duplicate original introduction text.

Source witness for the five shorter single-chapter books remains mixed:
2 John, 3 John and Jude source book identity is ambiguous or conflicts with
known original metadata, and Obadiah and Philemon source chapter words are
not close to the original I text, even though their source book/chapter
locations can be independently recognized. These are **not** approved
chapter-wide aliases: retain the original I texts and all independent
K section bodies.

## Implementation research boundary

A real I-only standard `osis2mod` compilation was attempted separately
for `Lev.19` and `Ps.108`. The original full-corpus native inspector
initially rejected both **by its own requirement for at least one numbered
K entry**; this diagnostic failure is not evidence the original introduction
is unparseable. A separate explicit, strictly opt-in *intro-only* native
reader and parser mode is being tested while retaining all production
full-corpus no-empty-K checks by default.

No original I/TOP content was edited. No publishable replacement module
has been produced. The true source edition and full original layout still
require human editorial verification before an index expansion.


## Exact original I-only OSIS roundtrip achieved

[Full original stock/native diagnostic #43634817753](https://github.com/icfmp/Bible-Resources/actions/runs/43634817753)
**SUCCESS** (47 editorial, 18 link plan, 16 structural, 6 native
intro-text, 10 numbered transport and explicit I-only transport tests).
The first two independently compiled tests had been rejected **by the
diagnostic reader**, not the compiler: both the C++ native scanner and
Python frame parser required a numbered K entry. A narrowly scoped
`--allow-intro-only` reader argument and `allow_intro_only=True` parser
argument now permit genuine I-only private test modules; production
full-corpus calls retain the strict default **K required**.

For **both Lev 19 and Psalm 108**, and for **both** original-source
embedding strategies (`chapter_wrapper` and `book_direct`),
the standard `osis2mod` produced an independently accessible native
chapter-introduction I key:

| Native introduction test | Lev 19 | Psalm 108 |
| --- | --- | --- |
| Original chapter I key present | `Lev.19` | `Ps.108` |
| Original source words preserved, same exact Unicode word sequence | **698/698** | **136/136** |
| Original visible text identical after whitespace-only normalization | **Yes** | **Yes** |
| Original non-`div` element order and all literal attribute values | **Yes** | **Yes** |
| Original `div` attribute multiset retained | **Yes** | **Yes** |
| Original ordered `reference` `osisRef` attribute values retained | **Yes** | **Yes** |
| Only additional `div` markup introduced | **Yes** | **Yes** |
| Unexpected numbered K keys | **0** | **0** |
| Additional automatic book I key | `Lev` | `Ps` |
| Automatically generated synthetic U/TOP keys | 1 | 1 |

These findings prove a reusable original-source **I-entry transport**
mechanism **for the two tested real introduction texts**; no loss of words,
reference destinations or attributes was detected. They do **not** prove
the whole book/chapter layout, the two original TOP positions, the other
1,253 introductions or full-corpus K/I/U parity.

**Next**: compile mixed original I+K entries together (not separately), then
attempt a complete isolated compilation. Compare exact original 29,975
key locations and semantically relevant XML/notes/reference attributes
without hiding compiler wrapper differences, plus reader display behavior.
Source-endorsed verse navigation changes are separate from technical parity.
No original or published module has changed.
