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
- A whole-note target list may be serialized as a whitespace-delimited, OSIS-valid `osisRef` in the intermediate grouped candidate. **This is not the final reader-facing target:** a second, independently tested OSIS candidate segments each such complete label into individual `reference` elements, retaining every original character, target, and all surrounding source markup. This is preferred for supported graphical-reader navigation, subject to real GUI acceptance.
- Original `ior` spans are machine-linked only when the complete literal grammar and all requested endpoints are verified. Preserve the three originals that cannot safely be resolved.
- All changes are **additive `osisRef` attributes on pre-existing start tags**, with every other original XML byte unchanged. Before/after full XML comparisons verify exact element count/order, text/tails, every original attribute and structural association. No missing Scripture verse, note, word or punctuation is invented.
- Original USFX/USFM archives, release SWORD binaries and the current approved `sources/cleaned` file are never overwritten. The new XML is generated separately with its own SHA-256 and review receipt.

## Full-corpus execution: 2026-11-23

The [full source-citation and one-reference-per-passage trial #45136656184](https://github.com/icfmp/Bible-Resources/actions/runs/45136656184) produced two isolated **unpublished** candidate representations and all accompanying provenance: [OSIS, diagnostics, native comparisons and 360-case editorial triage](https://github.com/icfmp/Bible-Resources/actions/runs/45136656184/artifacts/14800056884).

| Check | Original cleaned master | Candidate |
| --- | ---: | ---: |
| Note origins with verified machine address | 0 | **9,751** |
| Note destinations with entire source label mapped | 0 | **9,391** |
| Note destinations intentionally unlinked | 9,751 | **360** |
| Introduction spans linked | 0 | **174** |
| Introduction spans intentionally unlinked | 177 | **3** |
| Total additional `osisRef` attributes | — | **19,316** |

- Candidate: 30,170,715 bytes, SHA-256 `5b135af3081aece3796ac8acf5364e28e252353b558c3d7e721b17fbf9ce28fe`. Exactly 9,751 + 9,391 + 174 = 19,316 added attributes, **zero existing attributes rewritten**.
- The parser follows the source shorthand in 2,538 semicolon book-context repetitions, each on a fully verified, fully consumed note. No unsupported label or unattested verse is assigned a guessed target.
- Both source and candidate passed the independently pinned official OSIS schema check. BRNP now reports **360 unresolved destination labels and 3 unresolved introduction labels**, compared with 9,751/177 before; no new finding category was introduced.
- The [native SWORD cross-compiler comparison in the same run](https://github.com/icfmp/Bible-Resources/actions/runs/45136656184) compiled the released cleaned master and both candidate files into **three isolated temporary SWORD modules** and compared **32,426** ordered raw frames, including **31,169** populated native verse entries. The source's 31,170 authored verses and the existing Segond SWORD Mark 10:52–53 indexing compromise must not be conflated.
- All native differences were limited to the 9,751 expected origin `osisRef` attributes, 9,391 expected printed-destination `osisRef` attributes and 174 expected introduction `osisRef` attributes. **Zero unrelated raw native changes.** This proves engine preservation and scope of the changes, **not** actual clickable rendering in Xiphos, AndBible or Bible.
- All authorial words, note captions, original destination labels, identifiers, poetry, text order and punctuation are preserved. No published module has been altered.

### Unresolved original source cases — genuine questions, not test exceptions

Of the 9,751 notes, **360** are intentionally left without machine destinations:
- **305** labels remain unlinked due to open-ended or embedded shorthand syntax: 242 `etc.` forms, 54 embedded `v.` forms and 9 other forms. Their original printed labels are preserved.
- **55** complete-label attempts include at least one **source-absent** or contradictory target, such as `Jn 1:52` or `Ex 20:11, 31, 17`. A present-number/range mistake in the digital source or the printed edition must be independently checked; do not create an absent verse or omit the invalid part to make the link look complete.
- **37 additional notes** used the original eBible USFX spelling `Mal`, while the printed 1910 abbreviation table uses `Ma`. These are now linked under an **independently named source-provider variant**, pinned to the exact original USFX ZIP SHA-256 and verified against actual `xt` citation tokens. The source's literal `Mal` is preserved; the printed table remains unchanged. A provider alias can never override any historical printed alias.

The 360 remaining unlinked labels consist of **242** open-ended `etc.` strings, **54** embedded relative-verse strings, **9** other literal grammars and **55** strings with at least one nonexistent source verse. No remaining literal book-abbreviation mismatch was observed in the tested LSG corpus.

The candidate's JSON evidence includes a bounded set of exact `book` / `source_origin` / `printed_destination` / `reason` findings to resume the physical-edition review without repeating the audit.

### Three unresolved original introduction labels

| Book | Literal USFX label | Reason |
| --- | --- | --- |
| Philippians | `1:27-30, et` | Incomplete, mixed prose; do not assign a guessed partial target |
| Titus | `1:1-40` | `Titus.1.40` is **not** an attested source verse |
| 1 John | `1:1-4 (voir le prologue de l’évangile de Jn 1:1-18)` | Two embedded references and descriptive text |

These three texts were inherited from the original USFX, not introduced by source normalization. A historical-print correction needs a separate reviewed editorial dossier and source-preserving before/after decision.

## Earlier provider-variant-only checkpoint (superseded by full source-local pass)

The earlier [#45132279039](https://github.com/icfmp/Bible-Resources/actions/runs/45132279039) confirmed that the eBible-original `Mal` spelling could be recognized against the exact original USFX hash without changing the printed `Ma` abbreviation. At that intermediate stage, **9,345** destination labels were linked, **406** remained unlinked and no other native content changed. That is a historical intermediate result; the authoritative **9,391 linked / 360 unlinked** full-corpus result is recorded above.

## Independently verified per-passage presentation and source-local forms

A second candidate, generated by `scripts/segment_osis_reference_destinations.py`, retains the entire first normalized candidate and converts the 4,865 multiple-target notes to **15,052 independently addressed `reference` elements**, adding 10,187 link elements inside notes without adding or removing a single original character. All other original text, verse IDs, note source anchors, target sequences and source element order remain unchanged. Every byte outside the reviewed `reference` elements is preserved.

The whole-source XML source/individual comparison, official OSIS XSD, BRNP checks and **three isolated native SWORD compilations** all passed in [#45136656184](https://github.com/icfmp/Bible-Resources/actions/runs/45136656184). SWORD returned **32,426** ordered native entry frames, and **4,518** frames with altered reference markup were proven to contain **exactly the same compiled full text, note text, note origin and destination sequence**. An 81-frame trailing whitespace discrepancy discovered in the first experiment was repaired by preserving the literal original full stop and terminal blank inside the final reference element. The final trial has **zero** native note-text or unrelated markup differences.

The real libSWORD `OSISHTMLHREF` rendering filter was also executed: a reference element containing two `osisRef` tokens rendered one HTML anchor; two individually marked references rendered **two independently targeted anchors**. This is a stock SWORD rendering-engine check, **not** verification of actual Xiphos, AndBible or Bible user interactions.

The strict source-local citation rule also resolved **46** additional complete labels: 12 original `v. N.` forms with an attested source-note chapter, 18 named `Jud v. N.`/`Ab v. N.` forms within one-chapter biblical books, and 16 unambiguous `Lé 11.`-style whole-chapter references. No missing verse or ambiguous carry-over is inferred, and no historical authorial text has changed. The final normalized candidate has **9,391/9,751** linked cross-reference notes, **19,578** individual explicit destination tokens (including the single-target contextual forms), and 360 unlinked notes.

The remaining **360** original cases were fully classified and retained in the source-hash-pinned `lsg-source-citation-triage.json` artifact: 242 open-ended `etc.`, 54 mixed embedded `v.`, 9 other compound/chapter shorthand strings and 55 labels with invalid or absent endpoints. Preserve the original source testimony; future partial markup of definitely attested explicit fragments must keep the `etc.` and other unresolved authorial qualifiers visible and unlinked, never invent an endpoint.

## Remaining release/merge gates

1. **Individual hyperlink usability:** compare representative one-target, multi-target, ranges, chapters and implicit-context references in real Xiphos and AndBible (and if applicable Bible); preserve exactly the printed punctuation. The stock libSWORD HTML renderer already confirms two independent anchors for two separated source citations; this is still not proof of each graphical reader's click/navigation behavior. Do not relax BRNP to suppress reader defects.
2. **360 unresolved destination notes:** decide via print/editorial witnesses which are genuine malformed labels, non-linkable but faithful printed constructs, and independently verified technical alias variants. Maintain reversible decisions; no source text changes merely to lower a count.
3. **Three introduction pointers:** compare printed source for any actual correction; retain unlinked when no trustworthy proof exists.
4. **Publication and approved cleaned master:** only after the above plus complete source/native and reader checks and project-owner approval may a new edition-specific cleaned master be checked in and the accompanying source manifest/version be repinned. Existing release binaries must remain immutable.

This record is a source-backed technical review, **not** automatic BRNP certification, an editorial amendment to 1910, or permission to publish.
