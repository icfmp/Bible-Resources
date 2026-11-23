# Louis Segond 1910 — source-witnessed OSIS reference structure

**Status:** reproducible private cleaned-master candidate, under review. Neither a modification of the existing approved cleaned source nor a publication authorization.

## Exact input identity

- Source to normalize: `sources/cleaned/bibles/fr/lsg-1910/lsg-1910.osis.xml` (29,686,495 bytes, SHA-256 `d6abd7416d026c86ce2e9577e3bfe7a10159c5c78d236913359c7fab013449d0`), the exact source recorded in `CLEANUP_MANIFEST.json` for released LSG 0.1.0.
- Independent digital authoring witness: `sources/original/bibles/fr/lsg-1910/fraLSG_usfx.zip` (SHA-256 `fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e`). Its `fraLSG_usfx.xml` has 66 books, 9,751 `x/xo/xt` annotations and 177 `ior` introduction spans. This is **not** proof of exact agreement with every 1910 printed page.
- Book identifiers: independently reviewed `config/standard_usfm_osis_66.json`. All original and cleaned book IDs/order and all note and introduction labels must agree before changing any XML.
- **Existing release contents and original archives remain immutable.** No source-text alteration or new editorial section is authorized by this technical normalization.

## Normalization policy for these source-attested structures

1. An original USFX `x/xo/xt` represents one cross-reference note with a specific callout, an origin location and its printed destination-label text. Preserve all three, and pair each original note to the cleaned OSIS note within the correct independently identified book.
2. When the source's original `xo` origin label is an exact chapter/verse and the canonical verse exists, add an `osisRef` target **only to that existing** `reference type="annotateRef" subType="x-origin"`. This records the note **origin**, not a guessed cross-reference destination.
3. Original `xt` text may contain several printed references, abbreviations or implicit chapter carry-over. Preserve it exactly in the cleaned `reference` element. Do **not** create guessed `osisRef` destinations or pretend it is linked merely because it is inside a `note type="crossReference"`.
4. Match each original `ior` introduction span to its cleaned counterpart. Add a navigable `osisRef` only when the **entire** label's grammar unambiguously identifies existing source verses or a chapter. Reviewed representations include `1:1–2:23`, `1:57—2.40`, `5` for a chapter, and verse-only ranges in a book with exactly one attested chapter. Preserve the literal label and original list/item/section hierarchy.
5. When a printed section label includes narrative prose or a nonexistent endpoint, **do not** infer a partial target, revise the text, or fabricate a verse. Leave the original `reference` unlinked and record the exact unresolved label separately.
6. Generate a new candidate by inserting only source-witnessed `osisRef` attributes in original reference start tags. Byte-preserve all other XML, then parse both files and compare every element, tail, text node, unchanged attribute, callout, reference, note and structural order. Hash-pin both inputs; refuse an output path equal to any input.

These operations are a reusable *technical* representation mapping for USFX-style input, not an LSG-specific exception and not a grant of permission to change historical authorial content.

## Executed full-corpus evidence

[GitHub Actions #45127641897](https://github.com/icfmp/Bible-Resources/actions/runs/45127641897) built an **unpublished** candidate and stored the complete OSIS plus JSON provenance and before/after diagnostics as [artifact #14795963122](https://github.com/icfmp/Bible-Resources/actions/runs/45127641897/artifacts/14795963122). The original cleaned master remains unchanged.

- Candidate SHA-256: `8b1dad299151a9753644aaf7d83275e566156b317be8de97b531e942e05b951d` (29,884,946 bytes).
- Additive attributes: **9,925**, consisting of **9,751** exact note origins and **174** fully resolved introduction spans. No existing attribute changed.
- Source labels retained without guessed navigation: all **9,751** `xt` destination bodies and **3** introduction spans.
- Before BRNP: 9,751 noncanonical origin markers, 177 unresolved introduction spans, 9,751 destination labels without machine links.
- Candidate BRNP: **3** unresolved introduction spans plus **9,751** destination labels without machine links. No increased or newly introduced finding category.
- Both the exact source and candidate validated against the reviewed, SHA-256-pinned official OSIS 2.1.1 schema; **15/15** offline negative/idempotence tests passed.
- All XML content/text/tails, element order, note callouts and existing attributes are provably unchanged. **No published SWORD package or reader has been rebuilt/tested with this candidate**.

### Three original introduction labels that must not be silently changed

| USFM book | Label from original USFX | Reason for no `osisRef` |
| --- | --- | --- |
| `PHP` (Philippians) | `1:27-30, et` | Label is an unfinished mixed-language fragment, not an unambiguous complete passage target |
| `TIT` (Titus) | `1:1-40` | `Titus.1.40` is not a source verse; never synthesize it |
| `1JN` (1 John) | `1:1-4 (voir le prologue de l’évangile de Jn 1:1-18)` | Contains a main range and a separate prose parenthesis; cannot assign one inferred source target to the whole label |

These are **inherited from the upstream USFX witness**. An editorial repair requires an independently verified reference or historical edition witness, a separate before/after decision, and preservation of the original wording in provenance.

## Non-goals and next acceptance gates

- Do **not** claim that the remaining 9,751 printed destination labels are corrupted. They preserve source meaning but currently lack machine navigation. An optional future *link-enrichment* pass requires citation-by-citation book-name/abbreviation parsing, context handling, canonical target validation and independent gold fixtures — not mere automatic guessing.
- Do **not** close the BRNP profile work or call LSG wholly certified based on a zero XSD error: this normalization is about identified reference structures, not the entire editorial parity requirement.
- Before replacing this released cleaned-master identity: obtain owner approval for the new edited master and manifest/version, prove clean-to-native SWORD verse/word/note/references and reader behavior **over the entire corpus**, and preserve the old 0.1.0/0.1.1 artifacts. The candidate must be built reproducibly and reviewed in an isolated branch.
