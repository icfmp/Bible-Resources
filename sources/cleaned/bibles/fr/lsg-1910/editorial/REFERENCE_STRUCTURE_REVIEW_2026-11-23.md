# Louis Segond 1910 — source-attested OSIS reference normalization

**Status:** private, reproducible, source-pinned **cleaned-master candidate**, pending editorial and end-reader approval. No change to the release-attested `sources/cleaned` master, original eBible archives, SWORD releases, or catalogue.

## Four independent authorities

1. **Cleaned OSIS master:** `sources/cleaned/bibles/fr/lsg-1910/lsg-1910.osis.xml`, exactly 29,686,495 bytes, SHA-256 `d6abd7416d026c86ce2e9577e3bfe7a10159c5c78d236913359c7fab013449d0`, as pinned in `CLEANUP_MANIFEST.json`. This is the recovered compilation input for published LSG 0.1.0, not an independently certified transcription of a physical 1910 printing.
2. **Original digital authoring witness:** `sources/original/bibles/fr/lsg-1910/fraLSG_usfx.zip`, SHA-256 `fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e`. Its `fraLSG_usfx.xml` has exactly 66 books, 9,751 `x/xo/xt` reference annotations, and 177 `ior` table-of-contents/section labels. The unchanged original USFM ZIP is also retained.
3. **1910 printed-edition abbreviation table:** [1910 facsimile page 4](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/4) and [corresponding full-volume pagination page 1061](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/1061). The exact 66 print-defined book abbreviations and the independent `config/standard_usfm_osis_66.json` canonical book identities are recorded as separate, named source layers in `config/lsg-1910-printed-book-aliases.json`. In particular `Ph` means Philippians and `Phm` means Philemon; do **not** perform fuzzy alias guessing. The publisher's [1910 preface](https://fr.wikisource.org/wiki/Bible_Segond_1910/Avertissement) explains the historical parallel-reference apparatus.
4. **Official grammar/reader contracts:** SHA-256-pinned official OSIS 2.1.1 XSD, the draft BRNP source-structure checker, and actual libSWORD compiler/native raw readers. [CrossWire OSIS Bibles](https://wiki.crosswire.org/OSIS_Bibles) cautions that multiple targets in one `osisRef` are supported by OSIS syntax but not consistently navigable in graphical SWORD frontends.

## Source-fidelity normalization decisions

- Match each exact USFX `x/xo/xt` source note to one cleaned OSIS note, preserving callout, book, origin, printed destination text, paragraph/poetry/verse layout and note placement. Refuse any original↔cleaned count, identity, label or order mismatch.
- Add `osisRef` to a corresponding `x-origin` element **only when the original `xo` gives an exact existing book/chapter/verse**. These 9,751 additions represent note origins, **not** destination hyperlinks.
- For original `xt` text, interpret **only the complete printed citation string** using exact source-edition abbreviations, explicit book/chapter/verse groups, comma-delimited additional verses, semicolon-delimited chapter/verse contexts, full stops between explicit book groups, and source-attested, endpoint-verified ranges. Preserve reference order/repetitions. All tokens and punctuation must be consumed; an unfamiliar or missing target blocks the **whole note**, never just an inconvenient part.
- A whole-note target list may be serialized as a whitespace-delimited, OSIS-valid `osisRef` on the existing `reference` element. **This is a technical candidate only:** native SWORD preservation does *not* prove that all individual passages can be clicked. If reader UX requires individual links, a separate reviewed retyping into individually linked references must preserve **all original printed text and punctuation**.
- Original `ior` spans are machine-linked only when the complete literal grammar and all requested endpoints are verified. Preserve the three originals that cannot safely be resolved.
- All changes are **additive `osisRef` attributes on pre-existing start tags**, with every other original XML byte unchanged. Before/after full XML comparisons verify exact element count/order, text/tails, every original attribute and structural association. No missing Scripture verse, note, word or punctuation is invented.
- Original USFX/USFM archives, release SWORD binaries and the current approved `sources/cleaned` file are never overwritten. The new XML is generated separately with its own SHA-256 and review receipt.

## Full-corpus execution: 2026-11-23

The [strict full-list test and candidate build #45130871622](https://github.com/icfmp/Bible-Resources/actions/runs/45130871622) produced an isolated **unpublished** candidate: [XML + independent schema/BRNP/native reports artifact #14797444382](https://github.com/icfmp/Bible-Resources/actions/runs/45130871622/artifacts/14797444382).

| Check | Original cleaned master | Candidate |
| --- | ---: | ---: |
| Note origins with verified machine address | 0 | **9,751** |
| Note destinations with entire source label mapped | 0 | **9,308** |
| Note destinations intentionally unlinked | 9,751 | **443** |
| Introduction spans linked | 0 | **174** |
| Introduction spans intentionally unlinked | 177 | **3** |
| Total additional `osisRef` attributes | — | **19,233** |

- Candidate: 30,168,504 bytes, SHA-256 `289548b4a3fdabbf8c8edc4b3722aa1ee870385a830d2ed8a271a7a282281f36`. Exactly 9,751 + 9,308 + 174 = 19,233 added attributes, **zero existing attributes rewritten**.
- The parser follows the source shorthand in 2,531 semicolon book-context repetitions, each on a fully verified, fully consumed note. No unsupported label or unattested verse is assigned a guessed target.
- Both source and candidate passed the independently pinned official OSIS schema check. BRNP now reports **443 unresolved destination labels and 3 unresolved introduction labels**, compared with 9,751/177 before; no new finding category was introduced.
- The [native SWORD cross-compiler comparison in the same run](https://github.com/icfmp/Bible-Resources/actions/runs/45130871622) compiled the old and candidate files into **two isolated temporary SWORD modules** and compared **32,426** ordered raw frames, including **31,169** populated native verse entries. The source's 31,170 authored verses and the existing Segond SWORD Mark 10:52–53 indexing compromise must not be conflated.
- All native differences were limited to the 9,751 expected origin `osisRef` attributes, 9,308 expected printed-destination `osisRef` attributes and 174 expected introduction `osisRef` attributes. **Zero unrelated raw native changes.** This proves engine preservation and scope of the changes, **not** actual clickable rendering in Xiphos, AndBible or Bible.
- All authorial words, note captions, original destination labels, identifiers, poetry, text order and punctuation are preserved. No published module has been altered.

### Unresolved original source cases — genuine questions, not test exceptions

Of the 9,751 notes, **443** are intentionally left without machine destinations:
- **351** complete labels do not fit the approved, fully consumed reference grammar (e.g. `etc.`, `v.`, chapter-only or other mixed text); the printed label itself is preserved.
- **55** complete-label attempts include at least one **source-absent** or contradictory target, such as `Jn 1:52` or `Ex 20:11, 31, 17`. A present-number/range mistake in the digital source or the printed edition must be independently checked; do not create an absent verse or omit the invalid part to make the link look complete.
- **37** use a source-digitization abbreviation not established by the independent printed 1910 table; e.g. `Mal` rather than the edition-table abbreviation `Ma`. Preserve the source's spelling until a verified provider-specific alias decision exists.

The candidate's JSON evidence includes a bounded set of exact `book` / `source_origin` / `printed_destination` / `reason` findings to resume the physical-edition review without repeating the audit.

### Three unresolved original introduction labels

| Book | Literal USFX label | Reason |
| --- | --- | --- |
| Philippians | `1:27-30, et` | Incomplete, mixed prose; do not assign a guessed partial target |
| Titus | `1:1-40` | `Titus.1.40` is **not** an attested source verse |
| 1 John | `1:1-4 (voir le prologue de l’évangile de Jn 1:1-18)` | Two embedded references and descriptive text |

These three texts were inherited from the original USFX, not introduced by source normalization. A historical-print correction needs a separate reviewed editorial dossier and source-preserving before/after decision.

## Remaining release/merge gates

1. **Individual hyperlink usability:** compare representative one-target, multi-target, ranges, chapters and implicit-context references in real Xiphos and AndBible (and if applicable Bible); preserve exactly the printed punctuation. The native engine storing target lists is not proof of clicking the intended destination. Where readers cannot navigate a group, redesign the grouped reference **structure** with independent source-text parity, rather than weakening BRNP to suppress warnings.
2. **443 unresolved destination notes:** decide via print/editorial witnesses which are genuine malformed labels, non-linkable but faithful printed constructs, and independently verified technical alias variants. Maintain reversible decisions; no source text changes merely to lower a count.
3. **Three introduction pointers:** compare printed source for any actual correction; retain unlinked when no trustworthy proof exists.
4. **Publication and approved cleaned master:** only after the above plus complete source/native and reader checks and project-owner approval may a new edition-specific cleaned master be checked in and the accompanying source manifest/version be repinned. Existing release binaries must remain immutable.

This record is a source-backed technical review, **not** automatic BRNP certification, an editorial amendment to 1910, or permission to publish.
