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

The [full source-citation and one-reference-per-passage trial #45136656184](https://github.com/icfmp/Bible-Resources/actions/runs/45136656184) produced two isolated **unpublished** candidate representations and all accompanying provenance: [OSIS, diagnostics, native comparisons and 359-case editorial triage](https://github.com/icfmp/Bible-Resources/actions/runs/45136656184/artifacts/14800056884).

| Check | Original cleaned master | Candidate |
| --- | ---: | ---: |
| Note origins with verified machine address | 0 | **9,751** |
| Note destinations with entire source label mapped | 0 | **9,392** |
| Note destinations intentionally unlinked | 9,751 | **359** |
| Introduction spans linked | 0 | **174** |
| Introduction spans intentionally unlinked | 177 | **3** |
| Total additional `osisRef` attributes | — | **19,317** |

- Candidate: 30,170,765 bytes, SHA-256 `e68f81b8298bcf364221af7f178e4f8e556a6b9452f9fd8780784cc76fbf2ac4`. Exactly 9,751 + 9,392 + 174 = 19,317 added attributes, **zero existing attributes rewritten**.
- The parser follows source-defined shorthand in 2,539 verified contextual followups (including one disambiguated chapter-comma-verse group), each on a fully verified, fully consumed note. No unsupported label or unattested verse is assigned a guessed target.
- Both source and candidate passed the independently pinned official OSIS schema check. BRNP now reports **359 unresolved destination labels and 3 unresolved introduction labels**, compared with 9,751/177 before; no new finding category was introduced.
- The [native SWORD cross-compiler comparison in the same run](https://github.com/icfmp/Bible-Resources/actions/runs/45136656184) compiled the released cleaned master and both candidate files into **three isolated temporary SWORD modules** and compared **32,426** ordered raw frames, including **31,169** populated native verse entries. The source's 31,170 authored verses and the existing Segond SWORD Mark 10:52–53 indexing compromise must not be conflated.
- All native differences were limited to the 9,751 expected origin `osisRef` attributes, 9,392 expected printed-destination `osisRef` attributes and 174 expected introduction `osisRef` attributes. **Zero unrelated raw native changes.** This proves engine preservation and scope of the changes, **not** actual clickable rendering in Xiphos, AndBible or Bible.
- All authorial words, note captions, original destination labels, identifiers, poetry, text order and punctuation are preserved. No published module has been altered.

### Unresolved original source cases — genuine questions, not test exceptions

Of the 9,751 notes, **359** are intentionally left without machine destinations:
- **305** labels remain unlinked due to open-ended or embedded shorthand syntax: 242 `etc.` forms, 54 embedded `v.` forms and 9 other forms. Their original printed labels are preserved.
- **54** complete-label attempts include at least one **source-absent** or contradictory target, such as `Jn 1:52` or `Ex 20:11, 31, 17`. A present-number/range mistake in the digital source or the printed edition must be independently checked; do not create an absent verse or omit the invalid part to make the link look complete.
- **37 additional notes** used the original eBible USFX spelling `Mal`, while the printed 1910 abbreviation table uses `Ma`. These are now linked under an **independently named source-provider variant**, pinned to the exact original USFX ZIP SHA-256 and verified against actual `xt` citation tokens. The source's literal `Mal` is preserved; the printed table remains unchanged. A provider alias can never override any historical printed alias.

The 359 remaining unlinked labels consist of **242** open-ended `etc.` strings, **54** embedded relative-verse strings, **9** other literal grammars and **54** strings with at least one nonexistent source verse. No remaining literal book-abbreviation mismatch was observed in the tested LSG corpus.

The candidate's JSON evidence includes a bounded set of exact `book` / `source_origin` / `printed_destination` / `reason` findings to resume the physical-edition review without repeating the audit.

### Three unresolved original introduction labels

| Book | Literal USFX label | Reason |
| --- | --- | --- |
| Philippians | `1:27-30, et` | Incomplete, mixed prose; do not assign a guessed partial target |
| Titus | `1:1-40` | `Titus.1.40` is **not** an attested source verse |
| 1 John | `1:1-4 (voir le prologue de l’évangile de Jn 1:1-18)` | Two embedded references and descriptive text |

These three texts were inherited from the original USFX, not introduced by source normalization. A historical-print correction needs a separate reviewed editorial dossier and source-preserving before/after decision.

## Earlier provider-variant-only checkpoint (superseded by full source-local pass)

The earlier [#45132279039](https://github.com/icfmp/Bible-Resources/actions/runs/45132279039) confirmed that the eBible-original `Mal` spelling could be recognized against the exact original USFX hash without changing the printed `Ma` abbreviation. At that intermediate stage, **9,345** destination labels were linked, **406** remained unlinked and no other native content changed. That is a historical intermediate result; the authoritative **9,392 linked / 359 unlinked** full-corpus result is recorded above.

## Independently verified per-passage presentation and source-local forms

A second candidate, generated by `scripts/segment_osis_reference_destinations.py`, retains the entire first normalized candidate and converts the 4,865 multiple-target notes to **15,052 independently addressed `reference` elements**, adding 10,187 link elements inside notes without adding or removing a single original character. All other original text, verse IDs, note source anchors, target sequences and source element order remain unchanged. Every byte outside the reviewed `reference` elements is preserved.

The whole-source XML source/individual comparison, official OSIS XSD, BRNP checks and **three isolated native SWORD compilations** all passed in [#45136656184](https://github.com/icfmp/Bible-Resources/actions/runs/45136656184). SWORD returned **32,426** ordered native entry frames, and **4,519** frames with altered reference markup were proven to contain **exactly the same compiled full text, note text, note origin and destination sequence**. An 81-frame trailing whitespace discrepancy discovered in the first experiment was repaired by preserving the literal original full stop and terminal blank inside the final reference element. The final trial has **zero** native note-text or unrelated markup differences.

The real libSWORD `OSISHTMLHREF` rendering filter was also executed: a reference element containing two `osisRef` tokens rendered one HTML anchor; two individually marked references rendered **two independently targeted anchors**. This is a stock SWORD rendering-engine check, **not** verification of actual Xiphos, AndBible or Bible user interactions.

The strict source-local citation rule also resolved **46** additional complete labels: 12 original `v. N.` forms with an attested source-note chapter, 18 named `Jud v. N.`/`Ab v. N.` forms within one-chapter biblical books, and 16 unambiguous `Lé 11.`-style whole-chapter references. No missing verse or ambiguous carry-over is inferred, and no historical authorial text has changed. The final normalized candidate has **9,392/9,751** linked cross-reference notes, **19,582** individual explicit destination tokens (including the single-target contextual forms), and 359 unlinked notes.

The remaining **359** original cases were fully classified and retained in the source-hash-pinned `lsg-source-citation-triage.json` artifact: 242 open-ended `etc.`, 54 mixed embedded `v.`, 9 other compound/chapter shorthand strings and 54 labels with unresolved or absent source addresses. Preserve the original source testimony; future partial markup of definitely attested explicit fragments must keep the `etc.` and other unresolved authorial qualifiers visible and unlinked, never invent an endpoint.

## Source-faithful correction to the apparent 55 missing-target findings

A fresh read of the original `fraLSG_usfx.zip` revealed one source-reference form that the earlier parser wrongly treated as a nonexistent verse. At `Gen 2.2`, the exact printed-digital label `Ex 20:11, 31, 17.` designates **Exod.20.11 and Exod.31.17** when disambiguated using the attested source versification. The initial parser wrongly interpreted the second group as `Exod.20.31`, which is absent. This exact unchanged label is also visible in a separate [LSG-hosted cross-reference display](https://www.bibliaonline.com.br/lsg+fmar/gn/2); it does not constitute an independent visual certification of the physical printed 1910 page.

The generic parser now recognizes comma-separated `chapter,verse` only when the same-chapter verse is genuinely absent, the alternate book/chapter/verse exists, and **the entire original citation label** is consumed and verified. If both alternatives are possible it retains the previous grammar rather than guessing a switch. The individual-link serializer preserves the exact source substring `31, 17`, including commas and spacing. Both candidates were compiled and compared in three isolated SWORD engines with source-authorial note text preserved. No original biblical text, original citation label or release is modified.

The [full source-native run #45144018694](https://github.com/icfmp/Bible-Resources/actions/runs/45144018694) confirms **9,392 linked notes, 359 unlinked notes**, **19,317** additive reference attributes and **19,582** resolved destination address tokens. It found no new XML or native structural regressions.

The **54 remaining source-addressability cases** (not 54 confirmed printed errors) have been preserved in the separate versioned and source-hash-pinned `UNRESOLVED_REFERENCE_LEDGER_2026-11-23.json`: each record carries the source USFM book, note verse, literal citation, source and original file hashes, and a pending historical-print review status; none has an approved correction. The LSG CI now checks all 54 records against the exact original archive and fails on any silent change or accidental editorial approval.

Several records may reflect genuine typographical mistakes **or historical versification differences**, not simply invalid text. In particular, source-unaddressable `Jon 1:17`, `Os 1:10` and `Na 1:15` appear with variant chapter/verse numbering in other published Segond representations. These are *candidates for printed-edition collation*, **not** authority to remap Scripture verses or invent references.

## Nine source-unaddressable labels with documented versification alternatives

Within the **54** source-digitization labels whose destination is still unaddressable in this cleaned source, **nine notes** contain one of three citation identities demonstrably numbered differently in another edition or representation:

| Digital citation token in preserved eBible note | 1910 facsimile-derived printed chapter-text numbering | Source-note occurrences | Evidence status |
| --- | --- | ---: | --- |
| `Jon 1:17` | `Jonas 2:1` (great-fish narrative) | 4 | Chapter-text comparison; printed **note** not collated |
| `Os 1:10` | `Osée 2:1` (children of Israel promise) | 3 | Chapter-text comparison; printed **note** not collated |
| `Na 1:15` | `Nahum 2:1` (messenger of peace) | 2 | Chapter-text comparison; printed **note** not collated |

Evidence: [1910 printed-derived Jonah text](https://fr.wikisource.org/wiki/Bible_Segond_1910/Jonas), [1910 Hosea text](https://fr.wikisource.org/wiki/Bible_Segond_1910/Os%C3%A9e), and [1910 Nahum text](https://fr.wikisource.org/wiki/Bible_Segond_1910/Nahum). The transcription directly associates the cited words with different verse identifiers; separate digital Segond texts support the alternate numbering. This **does not demonstrate how the reference appears in its original 1910 printed margin**, nor does it authorize automatic source-versification changes, citation rewrite, or target remapping. The nine exact source-origin entries are flagged, without editorial approval, in `UNRESOLVED_REFERENCE_LEDGER_2026-11-23.json`.

The distinction matters: **an unaddressable citation is not automatically an authorial transcription error**. Any cross-versification mapping must use source-specific versification tables and an independently checked correspondence of the actual verses, not a hardcoded exception based on the target label.

## Complete 54-note cross-host digital apparatus comparison — review, not print certification

All **54** remaining source-unaddressable USFX `x/xt` citation labels have now been checked against the *separately hosted digital* `La Bible Louis Segond 1910` reference apparatus on [Biblia.com](https://biblia.com/bible/lsg/genesis/28/12). The evidence is preserved, source-note by source-note, in `SECONDARY_DIGITAL_CITATION_COMPARISON_2026-11-23.json` alongside the original 54-case ledger.

- **22/54 original `xt` labels have identical reference text** on the second digital host. This establishes corroborated *digital circulation* of these particular labels (including several non-addressable labels), **not** agreement with a physical printed 1910 reference note.
- **32/54 `xt` labels differ** from the second digital witness. Examples of exact compared source citation tokens: `Gen 9.4`: eBible `Lé 3:27` versus Biblia `Lé 3:17`; `Gen 28.12`: `Jn 1:52` versus `Jn 1:51`; `2 Chr 35.7`: `2 R 30:24` versus `2 Ch 30:24`; `1 Jean 3.1`: `1 Jn 1:12` versus `Jn 1:12`. The comparisons are factual observations of separately hosted text, **not authorization to change any reference**.
- The secondary host's digital editing/transcription provenance is **not established as independent of the eBible family**. “Different host” is not “verified historical witness.” The underlying digital Bibles may share editorial ancestry.
- Original print scans with a *visible marginal-reference column* have been located in the 1,061-page [1910 Wikisource facsimile](https://fr.wikisource.org/wiki/Livre:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu); e.g. [facsimile page 29, Genesis 28](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/29). The scans, not the digital comparison above, are the next authoritative source for determining the printed marginal notes. The book transcription (OCR/Match & Split, acknowledged unfinished by Wikisource) is **not** itself a substitute for visual printed-note collation.

**Publication protection:** all 54 literal original USFX labels remain untouched and unlinked. After the original-print visual review documented below, **one** citation has an attested 1910 print reading and **53** still need reliable printed marginal-note collation. All 54 remain without any authorized text or link change (`authorized_change: null`). The GitHub CI verifies the exact original archive identity, labels, secondary comparison classification and continued absence of editorial approval. This is a complete **digital-to-digital audit**, not completion of the required **digital-to-1910-print collation**.

## Printed facsimile location and legibility checkpoint (2026-11-23)

The publisher's [original 1910 **Avertissement**, scanned page 3](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/3) gives essential provenance for the reference apparatus: the revision's parallel references were prepared substantially using the **1875 Ostervald/Mackenzie parallel Bible**, from which many symbols and abbreviations were borrowed. It explicitly distinguishes identical expressions (`*`), expressions identical in the underlying original but not in French (`**`), OT quotations (`†`), verbatim parallel text (`=`), comparison (`cf.`), grouped parallels (parentheses), and `voy.` redirects. This historical explanation, transcribed on a Wikisource page marked proofread against the facsimile, is **context about editorial convention**, not evidence that every later citation agrees with Mackenzie or that a given eBible reference is a printed typo. Preserve these distinctions in any future print-to-digital cross-reference comparison; no parser simplification is authorized by this discovery.

The **exact 1910 printed facsimile** is indexed at [Wikisource](https://fr.wikisource.org/wiki/Livre:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu) and [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu). Its currently listed scan is **802 × 1,104 pixels per page** (1,061 pages). The text's Wikisource transcription omits the marginal cross-reference apparatus and is not proof of a printed `xt` label.

Two *original print page locations*, verified by the visible **source verse text** in the Wikisource page transcription, are now pinned for the first conflicting cases:

| Case | Source verse physically located | Original 1910 scan page | Editorial evidence status |
| --- | --- | --- | --- |
| `LSG-CR-001` | Genesis 9:4 | [DjVu image page 13](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/13) | Page and source verse confirmed; tiny adjacent printed reference type **not confidently deciphered** from the available 500 px preview |
| `LSG-CR-002` | Genesis 28:12 | [DjVu image page 29](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/29) | Page and source verse confirmed; printed note **not confidently deciphered** from the available 500 px preview |

These are **page-location verifications only**, not two completed citation collations. No `historical_print_status` is cleared, no edit is approved, and the 54-record source registry remains untouched.

A distinct, potentially clearer **1911 printed edition of the 1910 revision** is also identified at [Commons: La Sainte Bible, 1911.djvu](https://commons.wikimedia.org/wiki/File:La_Sainte_Bible,_1911.djvu), currently listed at 1,423 × 2,001 pixels (1,043 pages); its Commons history also records an earlier 2,480 × 3,508 scan revision. It may become useful as an *additional independent printed witness*, provided its exact reference-apparatus edition and page/verse correspondences are checked first. **The 1911 printing cannot silently substitute for the requested 1910 witness.** No marginal reference has yet been certified from it.

To certify a case, record the exact 1910 print scan page, a legible transcription of the physical marginal citation, the exact source-note origin, whether the source and 1910 print match, and the distinction between textual typo, edition-level printed anomaly, and legitimate verse numbering. Maintain each `authorized_change: null` until that evidence exists and an editorial decision is approved.

## Actual printed 1910 marginal citation — first independently recovered case

The real original [1910 printed DjVu](https://commons.wikimedia.org/wiki/File:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu), not its lower-resolution preview or another digital Bible, was downloaded and rendered via native DjVu decoding in the [read-only evidence run #45150806613](https://github.com/icfmp/Bible-Resources/actions/runs/45150806613). The exact file download was **292,950,257 bytes**, SHA-256 `67854882ec0e88defa5fea2d76a53ef479d2173467cdfa9b57f94a91c470643b`; the rendered pages 13 and 29 measured 821 × 1162 pixels. The original page and extracted context images are retained in the [temporary review artifact #14806870281](https://github.com/icfmp/Bible-Resources/actions/runs/45150806613/artifacts/14806870281); permanent recovery rests on the source URI, printed page and hash. Image contrast/scale is for inspection only, not evidence alteration.

**LSG-CR-002, Genesis 28:12:** the original [printed page 29](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/29), at Jacob's ladder, visibly reads **`Jn. 1. 52.`** as its marginal cross-reference. It corresponds to the original eBible USFX `Jn 1:52.` and **disagrees with** the second digital host's `Jn 1:51.`. The nonexistent cited verse therefore occurs in the actual 1910 **printed reference apparatus**; it must not be misclassified as a mistake introduced only by eBible's digitization. The specific visual reading, page location, immutable scan hash, source and secondary labels, and the absence of approval for any change are recorded in `PRINTED_1910_REFERENCE_COLLATION_2026-11-23.json`.

**LSG-CR-001, Genesis 9:4:** printed [page 13](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/13) was decoded and examined, but the correspondence of the *complete* eBible citation list to the narrow printed margin is still uncertain; do **not** certify `Lé 3:17` or `Lé 3:27` from this incomplete alignment. The visual record remains pending.

The apparently clearer [1911 printing](https://commons.wikimedia.org/wiki/File:La_Sainte_Bible,_1911.djvu) was independently retrieved (77,627,179 bytes, SHA-256 `906b9628c88e795f4ab40bd008aa29e661bbe45dfdac55ba17a9068ca6a59591`), but the sampled Genesis pages display a two-column body rather than the required 1910 marginal parallel-reference layout. It is **not an authenticated substitute for the 1910 cross-reference apparatus** and has not been used to approve any citation.

A new source-specific, reproducible print-collation registry now contains **1 visually verified historical reading**, with the other **53 still pending**. The CI guards enforce that every changed printed-witness status corresponds to a case-identity-matched record tied to the original USFX and historical facsimile, and that no corrected destination or editorial alteration is silently authorized. This is a historical reading, **not a release or permission to update the printed wording**.

## Follow-up visual collation batch — context located, no second certification

A further 1910 native-image read-only extraction checked [Genesis 35:10 on printed image page 36](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/36), [Leviticus 10:18 on page 96](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/96), and [Leviticus 16:27 on page 103](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/103). The middle of [page 35](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/35) covers Genesis 34 and **must not be confused** with the Genesis 35:10 source verse on page 36.

The read-only outputs are retrievable in [run #45151836311](https://github.com/icfmp/Bible-Resources/actions/runs/45151836311) ([image artifact #14806831946](https://github.com/icfmp/Bible-Resources/actions/runs/45151836311/artifacts/14806831946)) for pages 35, 96 and 103 and [run #45151980581](https://github.com/icfmp/Bible-Resources/actions/runs/45151980581) ([image artifact #14806308434](https://github.com/icfmp/Bible-Resources/actions/runs/45151980581/artifacts/14806308434)) for pages 36 and 13. Both reuse the immutable 292,950,257-byte printed source fingerprint above. The full native page, its marginal strip and source verse context were inspected, **but the verse-to-marginal-symbol and full citation grouping could not yet be proved unambiguously for any of these additional entries**. No printed-reference text for these cases is claimed certified, and they remain pending in all source ledgers.

In particular, **do not conflate a single neighboring printed marginal token with the complete eBible `xt` label**. Printed reference apparatus entries can span several neighboring cross-reference pointers. Both original verse marker and original note symbol must be aligned before the text can be reported as an edition-specific witness. If the print truly differs from eBible, the separate collation ledger accepts the discrepancy as evidence, **without granting permission to rewrite the authorial words or to add a target**. The CI compares a declared agreement/disagreement outcome to the printed citation and independently verifies source labels and zero approved changes.

### Reproducing original-print image evidence without retaining a CI download job

The short-lived exploratory GitHub Actions workflow is **not a production normalization dependency**. Future independent reviewers can use the pinned original scan directly:

```sh
curl --fail --location --retry 3 \
  'https://upload.wikimedia.org/wikipedia/commons/1/17/La_Sainte_Bible%2C_trad._Segond%2C_ed._1910.djvu' \
  --output original-printed-lsg-1910.djvu
echo '67854882ec0e88defa5fea2d76a53ef479d2173467cdfa9b57f94a91c470643b  original-printed-lsg-1910.djvu' | sha256sum --check
ddjvu -page=29 -format=tiff original-printed-lsg-1910.djvu original-1910-page29.tif
```

The page image and original scan checksum must agree with the recorded witness; resized/contrast-enhanced regions help human inspection but are **not** replacement sources. This manual evidence command deliberately does not edit any original Bible text or write into `sources/cleaned`.

## Whole-corpus historical-print page screening — all 54 outstanding note origins (2026-11-23)

The original 1910 historical facsimile was retrieved once under SHA-256 `67854882ec0e88defa5fea2d76a53ef479d2173467cdfa9b57f94a91c470643b`. The full embedded DjVu transcription (1,061 pages) was used only to **locate the physical source verse and its printed margin**, not to certify the literal marginal reference numbers. All 54 exact source book/chapter/verse origins have now been processed as **one batch**, with native-page image extracts and URL locators recorded individually in `PRINTED_1910_PAGE_LOCATORS_2026-11-23.json`. There are 53 distinct original scan pages for the 54 origins, since two origins share one page.

A critical batch-control result: **splitting the whole-book DjVu text stream on form feeds produces incorrect image page indices in later books**, e.g. the global text stream position for Mark 1 points to a physical page displaying Matthew 27–28. The final batch uses **`djvutxt -page=N` and `ddjvu -page=N` together** against the exact same native page index, and rechecks the verse text from the source. No page/citation may be marked certified merely because the automatic OCR locator scored well. In addition, three very short source-verses and two repeated-text candidates were checked against the printed chapter headings instead of accepting an ambiguous fuzzy text match.

Full read-only batch [run #45156275006](https://github.com/icfmp/Bible-Resources/actions/runs/45156275006) and [54-case image and page-locator artifact #14808936190](https://github.com/icfmp/Bible-Resources/actions/runs/45156275006/artifacts/14808936190) preserve the initial visual-review material. The temporary workflow that downloaded the 293 MB historical source and generated the contact images was subsequently removed: it is **not part of the long-lived production normalizer**, and the permanent case locator file, source archive checksum and standard `ddjvu -page=N` reproduction recipe remain.

**Editorial distinction:** `page located` is not `entire printed reference note collated`. As of this checkpoint **1 original marginal citation reading is independently confirmed (Genesis 28:12)** and **53 have native-page evidence but await a reliable exact note-marker/citation alignment**. Several printed pages contain a dense marginal apparatus with cross-references that are **not presented as the same complete digital `xt` label**; one cannot conclude that a different digital value is a digitization typo simply from the physical page or from another hosted digital Bible. The source ledger retains its original labels, and no published resource or candidate text is changed by this screening.

The source-pinned CI now verifies all **54** case identities, historical page range and links, immutable source/scan digests, and the strict distinction between a merely located page and a separately verified marginal citation; no hidden approvals are accepted. The 53 remaining historical citations are not falsely certified or treated as edited.

## Batch print-to-source discrepancy findings — six physically attested individual reference tokens

After locating and visually screening the **54** original 1910 page contexts in one batch, a second read-only extraction enlarged the actual central reference columns for 13 priority case contexts. The original [focused printed-image run #45158131029](https://github.com/icfmp/Bible-Resources/actions/runs/45158131029) ([image artifact #14809073411](https://github.com/icfmp/Bible-Resources/actions/runs/45158131029/artifacts/14809073411)) used the immutable 1910 DjVu SHA-256 already pinned above. The previous full-page source scan/verses were also independently compared to each excerpt.

**Six additional case-specific printed reference tokens** are now readable and separately recorded in `PRINTED_1910_REFERENCE_TOKEN_COMPARISON_2026-11-23.json`. The printed note groups can be longer than the digital `xt` notes; **these are token-level historical testimonies, not certification that the entire digital note label matches the printed apparatus**:

| Case and verse | 1910 printed reference token | Original eBible digital token | Secondary digital token | Evidence |
| --- | --- | --- | --- | --- |
| `LSG-CR-008` Jos 5:13 | `Ex. 23. 23.` | `És 23:23` | `És 23:23` | [Printed p. 190](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/190) |
| `LSG-CR-009` Jos 14:6 | `No. 14. 24. De. 1. 36.` | `No 12:24. De 1:36` | `No 12:16. De 1:36` | [Printed p. 198](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/198) |
| `LSG-CR-011` 2 Chr 35:7 | `30. 24.` (*same book: 2 Chronicles*) | `2 R 30:24` | `2 Ch 30:24` | [Printed p. 394](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/394) |
| `LSG-CR-029` Mt 19:14 | `18. 3.` (*same book: Matthew*) | `Mc 18:3` | `Mc 18:3` | [Printed p. 814](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/814) |
| `LSG-CR-050` 1 Jn 3:1 | `Jn. 1. 12.` | `1 Jn 1:12` | `Jn 1:12` | [Printed p. 1022](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/1022) |
| `LSG-CR-052` Ap 7:3 | `Éz. 9. 4-6.` | `Ép 9:4` | `Ép 6:4` | [Printed p. 1031](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/1031) |

These corroborate **concrete digital-only reference token errors or changed digital reference identities** in a subset; the first original-print-certified `LSG-CR-002` at Genesis 28:12 conversely establishes that the wrong `Jn 1:52` **was already in the printed edition**. Thus neither blanket correction from Biblia, nor blanket trust in eBible, is editorially defensible.

The other **47** of the 54 cases do not yet have a print token independently certified and cross-walked to their exact source `xt` at this checkpoint; they remain individually located in `PRINTED_1910_PAGE_LOCATORS_2026-11-23.json` and untouched. The source and print ledgers deliberately count **1 full printed-note reading**, **6 additional individually attested printed *tokens***, and **53 full-note cases still unapproved**. The categories are **not additive as 54 fully certified notes**. All six corrections are *evidence-based proposals* for a future separately approved edited version, not silently applied changes to the original text, existing cleaned master, candidate OSIS or released binary.

The temporary scan-download and image/OCR forensics workflows were deleted after their evidence runs to avoid accidentally introducing large downloads into the regular production pipeline. The permanent image source URL, SHA-256, page positions and individual reference observations are in the editorial registry and can be reproduced using the documented native `ddjvu` command.

## Second print token batch — four more verified reference identities

The read-only [second original-margin image run #45159370757](https://github.com/icfmp/Bible-Resources/actions/runs/45159370757) ([artifact #14809543290](https://github.com/icfmp/Bible-Resources/actions/runs/45159370757/artifacts/14809543290)) checked 13 further original 1910 page contexts. Four additional *printed reference tokens* were readable with the source passage and distinct marginal sign:

| Case | Original 1910 reference token and note | eBible original digitization | Secondary Biblia |
| --- | --- | --- | --- |
| `LSG-CR-017` Isa 11:6, [p. 572](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/572) | contextual `65. 25.` (Isaiah) | `És 65:26` | `És 65:25` |
| `LSG-CR-020` Jer 1:3, [p. 619](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/619) | `2 R. 23. 34.` | `2 R 5:23, 34` | `2 R 5:23, 27` |
| `LSG-CR-023` Jer 41:1, [p. 663](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/663) | `2 R. 25. 25.` | `2 R 25:35` | `2 R 25:25` |
| `LSG-CR-045` 1 Th 4:9, [p. 989](https://fr.wikisource.org/wiki/Page:La_Sainte_Bible,_trad._Segond,_ed._1910.djvu/989) | `1 Pi. 4. 8.` | `2 Pi 4:8` | `2 Pi 3:8` |

**Combined, non-overlapping editorial evidence counts:** all **54 original cases** have original-print page locators; **10 cases** have a verified individual printed reference token that materially clarifies a problematic digital destination; **one different case** (Genesis 28:12) has a visually checked printed marginal citation agreeing with eBible but referring to an unattested destination. The remaining **43 cases** do not yet have a source-note-specific printed token verified. Only **one complete cited marginal label** has a separately documented verified reading; 53 cases remain pending *full apparatus-to-digital-note* collation. These different levels of evidence must not be equated.

The second printed-token sightings are appended to the same original-scan-SHA-256-pinned `PRINTED_1910_REFERENCE_TOKEN_COMPARISON_2026-11-23.json` with `editorial_change_authorized: null`. No digital `xt` is rewritten, no nonexistent verse is created, no inferred destination is added and no released or cleaned master changes. Apart from the ten recorded tokens, the second review did not certify the other examined page-column candidates because the exact note marker/group boundary was not securely established. The temporary 293-MB source-download CI is not retained as a standing production workflow.

## Remaining release/merge gates

1. **Individual hyperlink usability:** compare representative one-target, multi-target, ranges, chapters and implicit-context references in real Xiphos and AndBible (and if applicable Bible); preserve exactly the printed punctuation. The stock libSWORD HTML renderer already confirms two independent anchors for two separated source citations; this is still not proof of each graphical reader's click/navigation behavior. Do not relax BRNP to suppress reader defects.
2. **359 unresolved destination notes:** decide via print/editorial witnesses which are genuine malformed labels, non-linkable but faithful printed constructs, and independently verified technical alias variants. Maintain reversible decisions; no source text changes merely to lower a count.
3. **Three introduction pointers:** compare printed source for any actual correction; retain unlinked when no trustworthy proof exists.
4. **Publication and approved cleaned master:** only after the above plus complete source/native and reader checks and project-owner approval may a new edition-specific cleaned master be checked in and the accompanying source manifest/version be repinned. Existing release binaries must remain immutable.

This record is a source-backed technical review, **not** automatic BRNP certification, an editorial amendment to 1910, or permission to publish.
