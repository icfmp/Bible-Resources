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
