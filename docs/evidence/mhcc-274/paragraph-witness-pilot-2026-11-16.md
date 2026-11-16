# MHCC — independently pinned paragraph pilot, exact original native entries

Date: 2026-11-16. Investigation [#278](https://github.com/icfmp/Bible-Resources/issues/278), draft [PR #275](https://github.com/icfmp/Bible-Resources/pull/275).

## Objective and non-authority caveat

Determine whether a long SWORD commentary section lost **original internal paragraph breaks**, without treating supplier formatting as authoritative or inventing punctuation, section boundaries or text. Use the existing **SHA-pinned original CrossWire MHCC 2.0** and **separately SHA-pinned CCEL ThML** only as independent digital witnesses. The latter is not an authenticated copy of the precise historical Moody Press 28th printing claimed by CrossWire. Both original inputs stay immutable.

A reusable `scripts/commentary_paragraph_witness_probe.py` compares exact **native I/K keys** selected by an audit CLI argument, independently located ThML `scripCom` section-start markers, actual **`<p>` elements within that source section**, eight-word unique lexical start/end anchors and the **entire case-folded Unicode word-token stream**, in memory. The source witness's chapter-level `<p>` count must never be mistaken for the paragraph count of one numbered commentary *section*. It exports no original words, source XML or annotation targets. The probe never proposes modifications.

## Six representative original source observations

[Full six-case original/native and independent-source pilot #43809632885](https://github.com/icfmp/Bible-Resources/actions/runs/43809632885) **SUCCESS** on the exact full pinned SWORD corpus, including 28,718 K/1,255 I/2 TOP, complete text/markup/reference-preservation checks and real Xiphos 3/3 navigation probes. This extends the successful [initial section-marker pilot #43808286629](https://github.com/icfmp/Bible-Resources/actions/runs/43808286629) with full paragraph word-token checks, first mismatch location and internal break-marker inspection.

| Original native entry | Original SWORD word tokens | Independent CCEL `<p>` per same section | CCEL paragraph word tokens | Original native prefatory word tokens before unique paragraph match | All CCEL paragraph words in same exact order? |
| --- | ---: | ---: | ---: | ---: | --- |
| `K:John.3.1` | 1,569 | **1** | 1,544 | 25 | **Yes** |
| `K:Exod.12.1` | 969 | **1** | 907 | 62 | **No — one internal digital-edition word-token difference, offset 774** |
| `K:Matt.4.1` | 760 | **1** | 723 | 37 | **Yes** |
| `K:Gen.3.1` | 578 | **1** | 509 | 69 | **Yes** |
| `K:2John.1.1` | 220 | **1** | 182 | 38 | **Yes** |
| `I:Lev.19` | 698 | **No uniquely matching CCEL `scripCom` start marker** | Not established | Not established | **Unresolved by this locator** |

In each of the first **five** cases, both beginning and ending eight-word runs are uniquely located at the expected source-section position in the original native SWORD exposition. **Four** independently digitized CCEL paragraph word streams equal the entire contiguous original SWORD exposition word stream after its existing prefatory markup. Their word-order parity is a strong digital-witness concordance, **not** punctuation, XML, rights, historical print paragraphing or complete edition equivalence.

The `Exod.12.1` source paragraph has the same **907-word-token length** as the remaining SWORD exposition, with unique first and last eight-token anchors. The refined full-source audit finds **exactly one different internal case-folded word token**, at **zero-based CCEL paragraph token offset 774** (the 775th token), compared with **zero** differences for the four other K examples. This is an **unreviewed variant between digital editions**, not an established transcription error or a reason to replace one version with another.

**Second-level paragraph-markup proof:** In **all five** matched CCEL source `<p>` elements, the internal `<br>`, `<lb>`, `<l>`, `<lg>`, nested `<p>`, nested `<div>` and literal blank-line counts are **zero**. A synthetic regression demonstrates that a `<br>` inside an otherwise single `<p>` would be detected. Thus the selected CCEL digital sections supply **no additional original internal paragraph or line breaks to restore**. This does not establish authorial or Moody print-edition paragraphing, nor certify real-reader display.

The original `Lev.19` prose is present in native **I chapter-introduction** storage with no original K for the chapter, and the established separate source-chapter audit discusses its source location. Do **not** infer that missing a `scripCom` section-start marker means the prose is lost, or move its text to K addresses.

## Editorial implications

1. **Correct the earlier false-positive assumption:** absence of original SWORD `<p>` tags and 807 long unwrapped sections is not by itself proof of **lost internal paragraphs**. Five independent ThML section-start witnesses likewise represent each sampled source exposition as **one `<p>`**. Multiple paragraphs visible across the complete CCEL chapter are generally separate section/outline elements. A long one-paragraph exposition may be unattractive to read without being a source transmission defect.
2. **Do not rewrite the existing K/I/TOP text or insert hypothetical paragraph breaks in BRMHCC 0.1.1.** New internal paragraph splits without an independently identified print-edition source would be a separately labelled editorial presentation adaptation, *not* a verified restoration. Such a decision requires an explicit owner/editorial choice.
3. **Keep the distinct question of reader layout open:** actual Xiphos formatting, historical print evidence and differences between section-heading/outline markup remain to be sampled. Original authorial content/annotations must never be silently altered.
4. **Retain provenance separately:** CrossWire's [module metadata](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC) identifies “Moody Press, 28th printing, ISBN 0-8024-5190-X” as the digital input printing; CCEL's [work record](https://ccel.org/ccel/henry/mhcc/mhcc) identifies a separately prepared abridgement. The cited input provenance is an upstream claim, not independent authentication of the specified printing.

## Release boundary

BRMHCC 0.1.1's separately tested **17 index-section / 24-link** changes and **one strictly bounded Ezekiel 3 reference correction** remain private, reproducible and unchanged. All original K/I/TOP words outside the single authorized private test change remain preserved in the existing full corpus audit. Nothing in this paragraph pilot authorizes additional K aliases, CCEL word replacement, a public download, a catalogue release, merge, a modern-English translation restart or Codex invocation.

This research trail is auditable without publishing independent source text. Independent actual **text/punctuation** comparison, exact print-edition boundaries, final metadata and any editorial paragraphing decision remain separate acceptance gates.


## Printed-edition identification and digital PDF page inspection (follow-up, 2026-11-16)

CrossWire's original module metadata explicitly **claims**, without an
independent facsimile receipt, to have followed **Moody Press, 28th
printing, ISBN 0-8024-5190-X**:
https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC.
Bibliographic listings associate this ISBN with a **Moody hardcover, 1981,
1,024 pages** (some sellers give 1982 or describe a later printing):
https://www.abebooks.co.uk/9780802451903/Matthew-Henry-Concise-Commentary-Whole-080245190X/plp .
Those listings authenticate the ISBN as a useful **physical-edition
identification lead**, **not** the precise printing, paragraph positions,
source wording or source rights of the file shipped by CrossWire.

A separately accessible **typeset CCEL-derived PDF** was checked by actual
page images, especially John 3 on **printed pages 1047–1049**:
https://reformed.org/wp-content/uploads/2019/04/MatthewHenrysBibleCommentary.pdf .
Its title metadata expressly identifies **Christian Classics Ethereal
Library** as publisher and **Logos Research Systems** as source. The
*John 3, Verses 1–8* exposition starts on printed p. 1047, flows across
pp. 1048–1049 without a visibly inserted internal paragraph break, and
is followed by the distinct *Verses 22–36* heading on p. 1049.
This aligns with the separately pinned CCEL ThML's **one section-level
paragraph**, but is **not an independent authorial/print witness**:
a PDF rendering derived from CCEL cannot be counted as a second edition
that corroborates CCEL's own editorial decisions. A physical page break
in its typesetting is not a paragraph boundary.

A public-domain **complete/unabridged** Matthew Henry PDF, or a
**Thomas Nelson 1997** concise volume (ISBN 0-7852-1247-7), is also not
evidence of the **specific Moody printing's** pagination/paragraphing:
https://openlibrary.org/books/OL678768M/Matthew_Henry%27s_concise_commentary_on_the_whole_Bible.

**Disposition:** no accessible authenticated page from the claimed Moody
**28th printing** was verified in this research pass; consequently **no
new historically restored paragraph boundary can be certified**. Do not
promote the CCEL-derived PDF to independent evidence or infer that a
long digital paragraph is automatically corrupt. Keep #278 open for a
genuine source-edition facsimile and bounded **actual Xiphos rendering**
comparison. No SWORD, original source, rights or public release change.

## Owner's scope decision — preserve original segmentation (2026-11-16)

The project owner clarified that **BRMHCC's existing editorial section and paragraph segmentation must remain as transmitted**. The purpose of this source-correction edition is to **correct actual, substantiated errors** in text, references, indexing or markup, **even when an error can be traced back to the historical printed edition**. CrossWire and the historical printing are evidence, not infallible authorities. Every correction must be identifiable, documented, testable and reversible. This is not a blanket rule to perpetuate verified errors.

**Do not introduce new stylistic paragraph divisions, recombine independent sections or reflow the original exposition simply to improve readability.** The 807 long K bodies and one long I body are diagnostics, **not** a pending task to split them. No further Moody facsimile hunt or reader-layout pilot is required merely to justify optional paragraphing. If concrete evidence later shows that a particular existing boundary is *erroneous* (lost/corrupt), investigate that precise error as a separate, bounded correction; do not apply a global layout transformation.

The future **modern-English adaptation** is the appropriate edition for new readability-driven paragraphing, while preserving Matthew Henry's sense, reasoning and theology. This decision supersedes the preceding proposal to hold 0.1.1 for optional paragraph restoration. BRMHCC 0.1.1 remains subject to its real technical, editorial, rights and publication gates, but **not** to an open-ended paragraph-redesign investigation.

## Exod.12.1 single-word variant classified — full-source rerun (2026-11-16)

The reusable paragraph witness now identifies the **semantic XML owner** of
the first different case-folded word token, rather than silently labelling all
different digital tokens as exposition defects. This source-neutral diagnostic
does **not** compare or overwrite link destinations and returns only
`SCRIPTURE_REFERENCE_LABEL` or `EXPOSITION_OR_OTHER_MARKUP` classes,
never source wording or XML.

[Full pinned-original and independently pinned CCEL ThML audit #43848131445](https://github.com/icfmp/Bible-Resources/actions/runs/43848131445)
**SUCCESS**: `K:Exod.12.1` still has exactly **one** different word
token at paragraph-relative zero-based offset **774**, and the new
read-only inspection establishes that **both digital witnesses place
this differing token inside their existing scripture-reference label
element**, not in the explanatory prose. The other four sampled K
section word streams remain identical. Generic synthetic tests also
distinguish reference-label differences from actual exposition changes.

The publicly rendered [CrossWire MHCC in STEP
(Exodus 12)](https://www.stepbible.org/?q=version%3DMHCC%40reference%3DExo.12)
uses the abbreviated book label `He 13:13, 14` at the relevant citation,
whereas the [CCEL concise Exodus 12
page](https://ccel.org/ccel/henry/mhcc.iii.xii.html) renders
`Heb 13:13, 14`. This is consistent with the measured **single
reference-label word token** difference, not a demonstrated corruption
of the author's exposition. The publicly visible cited passage is the
same; the exact underlying XML `osisRef` target equality was **not**
independently proven by this paragraph witness.

**Disposition:** retain the original CrossWire label and its target
unchanged. Do not describe the single-word cross-edition difference as
an authorial-text error, copy CCEL typography or create a stylistic
paragraph split. No change to the already corrected **private**
BRMHCC 0.1.1 scope (24 approved-for-testing index aliases and one
reversible Ezekiel 3 correction); publication remains separately gated.
