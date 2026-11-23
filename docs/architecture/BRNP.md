# Bible Resources Normalization Profile (BRNP) — working specification v0.2-draft

**Status:** implementation under review in [#451](https://github.com/icfmp/Bible-Resources/issues/451). **Not a mandatory publication gate.** This document specifies conventions for reviewed *cleaned* masters, not for immutable source archives. The official OSIS 2.1.1 XSD remains authoritative for XML legality. A BRNP passing result alone never certifies an edition.

## Authority and fidelity

The governing editorial target is the **identified historical work and edition**, not the digital provider's arbitrary rendering. The provider supplies evidence and provenance, not editorial authority. Retain original upstream bytes separately. Distinguish (a) text and authorial intent, (b) historical edition apparatus and meaningful editorial choices, (c) third-party digital presentation, and (d) converter artifacts. Only (c)/(d) are potential cleanup candidates, with explicit evidence; never assume that a paragraph, punctuation mark, note, verse gap, title, quotation, italic or reference was invented by the digital provider.

When historical authorial intent or edition evidence is insufficient, mark the case **unresolved**, not silently removed. Preserve verbatim words and punctuation and the reviewed edition's textual variants, intentional omissions, versification, note anchors and semantically meaningful markup. A correction against the historical edition must have an independent witness, explicit before/after review, authorization and an audit trail. A source-to-cleaned comparison is a conversion-integrity check, **not** proof of authorial fidelity.

## Canonical representation contracts

These conventions describe *how* to encode a given meaning. They do not require different editions to have the same paragraphs, headings, notes or verse ranges.

| Construct | Common convention | Do not do |
| --- | --- | --- |
| Document | One OSIS namespace `osis` root, one `osisText`, documented work identity and `header` | Mix XML namespaces or fabricate an edition identity |
| Books | `div type="book"` with unique canonical `osisID`; book order follows approved canon | Merge or invent books |
| Chapters | `chapter` with precise chapter `osisID`; milestone pairs use matching `sID`/`eID` and correct scope | Mix container and milestone representations for the same chapter or silently rearrange boundaries |
| Verses | Unique `osisID`; when milestones are needed across paragraphs or other structures, a unique matching `sID`/`eID` pair (the pair key may differ from the canonical `osisID`) | Treat an OSIS-valid milestone as text, infer missing verse IDs or force an edition into another versification |
| Paragraphs | `p` only for evidence-supported paragraph units; milestones when needed to represent overlapping boundaries | Automatically insert paragraphs based on verse count |
| Poetry | `lg` for source-attested stanza/group boundaries; every normalized `l` has an `lg` ancestor, with original line ordering and attested `level` | Convert poetry to prose, invent stanzas or leave an unscoped poetic line |
| Titles | `title` at the documented semantic location and type permitted by the official schema | Promote provider UI headings to authorial headings |
| Tables and lists | Preserve evidenced `table`/`row`/`cell` and `list`/`item` content and order, including historically meaningful apparatus | Flatten structured content to prose or call it "noise" simply because a digital source uses tables |
| Header metadata | Preserve standard `identifier`, `description`, `date`, `rights`, `type`, `refSystem`, `revisionDesc` and their provenance separately from authorial content | Present a provider revision log as a title/note written by the biblical author |
| Quotes and emphasis | Preserve `q`, `hi`, `transChange`, `divineName` and intended extent | Infer quotation marks, italicization or divine-name conventions |
| Notes | `note` with original meaningful type and association | Merge, re-anchor or delete content notes merely to simplify layout |
| References | `reference` with evidence-supported `osisRef`; a missing/blank target is an explicit review finding, including where the original only contains a human-readable label | Invent a destination or silently suppress an unresolved link |
| Lexical alignment | `w` with verifiable lemma/morph associations and exact word extent | Invent Strong/MACULA mappings or split joined words heuristically |
| Commentary | Dedicated `div` with `annotateType="commentary"` and reviewed `annotateRef`; preserve authored scope and introductions | Duplicate chapter-level commentary across verses in source or fabricate a verse-level scope |

## Canonical hierarchy: normative target, distinct from XSD legality

**Bible target** (for source-derived, reviewed *cleaned* masters): one `osisText`, then one `div type="book"` per canonical book in the chosen versification. Book divisions are not nested or repeated; chapters and their verse scopes belong to the correct book. A chapter container cannot contain canonical IDs from another chapter. For milestone-based verses spanning paragraphs, `sID`/`eID` must pair uniquely, in order; the canonical `osisID` is unique independently of the pairing key. A different pairing key is **not** a relaxation of canonical reference requirements. Compound IDs remain edition-specific and must be checked member by member. No missing verse is synthesized.

**Commentary target:** one logical book division per book and source-attested commentary units represented by `div annotateType="commentary" annotateRef="…"`. One entry may cover a book, chapter, verse or reviewed passage range; it is not redistributed or duplicated to individual verses just to suit a reader. Cross-book references require explicit versification/review. Unnumbered introductions remain distinct. The MHC verse-milestone encoding is a **source representation to be migrated and proved equivalent**, not a second unconditionally accepted canonical target. The repeated MHCC book divisions are **noncanonical** and need a reversible structural grouping proof, preserving entry ordering, references, and authored titles.

**OSIS-valid but BRNP-noncanonical structures:** classify the discrepancy; retain it in the immutable original, do not hide it in a validator allowlist. A new representation may be approved only by changing this common contract with a standard-based rationale, positive/negative tests and all affected real-corpus regression results. Do not introduce exceptions keyed to a resource ID or a fixed diagnostic count.

**Minimal mandatory validation invariants:** correct document/work identity, no nested/repeated Bible books, no nested canonical commentary book segments in the cleaned target, correct book/chapter ownership of references, unique canonical verse IDs **including individual members of compound IDs**, separately unique chapter/verse milestone keys, proper pairing and closure, evidence-backed paragraphs/poetry/notes, explicit reporting of unresolved reference targets, reviewed commentary range associations, and correct containment for `table/row/cell` and `list/item`. The XSD enforces XML-level grammar **in addition**, not in place of these controls. Unknown reference grammar or unverified authorial structure blocks a certification claim.

OSIS permits more than one representation for certain overlapping structures. BRNP chooses a deterministic representation **only after** equivalence has been proved with positive/negative fixtures and relevant real editions. Unknown, ambiguous or otherwise schema-valid constructs are reported for review, never auto-flattened. No edition-specific hidden exceptions.

## Decision order: editorial meaning before XML convenience

Apply these rules in order. A later step must never override an earlier one simply to make an OSIS validator or SWORD reader happy.

1. **Identify the work and exact edition.** Record the original author/translator, edition, canon, versification and independently checked historical witnesses. Source-provider OSIS is evidence of a digital transmission, **not** proof of authorial structure.
2. **Build an editorial structure inventory.** Record every evidenced book/chapter/verse unit, introduction, section, paragraph, poetry line and grouping, title, table/list, note, cross-reference label and target, quotation, emphasis and lexical association. Distinguish authorial text, historical publisher apparatus, provider-only metadata, and rendering artifacts. If attribution is uncertain, preserve and flag it.
3. **Select the single canonical logical hierarchy** described below. Prefer semantic containers when the unit's boundaries can be represented without overlap; use OSIS milestones **only when structural overlap or source-attested boundaries require them**, not merely because upstream used milestones. Convert equivalent encodings only with a recorded, tested transformation.
4. **Preserve all semantic associations.** A change of representation must not re-anchor a note, merge commentary scopes, reshape poetry, add a heading, relocate a verse, invent an `osisRef`, silently lose a cross-reference label, or change the authorial/publisher distinction.
5. **Validate the output independently.** Official OSIS XSD establishes legality only. BRNP establishes the reviewed technical hierarchy. Historical-witness comparison establishes editorial fidelity. SWORD whole-corpus readback and independent readers establish native usability. None substitutes for the others.

## Canonical representation selection and ambiguities

| Question | BRNP target | If source evidence is insufficient |
| --- | --- | --- |
| Chapter/verse fully contained in a single logical parent? | Container representation where the official standard and downstream importer permit it; no unnecessary pairing keys | Report the unresolved overlap; do not force a container or insert a missing boundary |
| Boundaries cross authorial paragraphs or poetry? | Matched `sID`/`eID` milestones with unique keys, exact starts/ends, canonical `osisID` and reviewed ownership | Preserve original boundaries and flag any missing pair; never fabricate a new verse |
| Is a title/paragraph/poetic stanza from the reviewed edition? | Preserve exact structure, position, order and meaningful type | Do not derive it from the digital provider's headings or line wrapping |
| Is a note content or a provider navigation instruction? | Retain authorial/historical content and its anchor; isolate provider-only controls in provenance/transport, not authored body | Leave unchanged and flag for editorial review |
| Is a visible cross-reference only a label, with no verified destination? | Preserve its original literal label and scope. Require evidence before encoding a navigable `osisRef`; unresolved targets remain explicitly reported | Never synthesize a target from matching words, and never delete the label or disguise the missing destination |
| Are repeated or nested book wrappers merely segmentation artifacts? | One logical book container, child commentary units preserved and ordered with original scope and headings | Keep the raw source and report nonconformity; no resource-specific allowlist |
| Can a commentary section be mapped from verse milestones to `annotateRef`? | One section per **authored unit**, with exact reviewed book/chapter/verse/range association and introductions kept separate | Do not guess or duplicate the commentary across verses |

The *same* mapping rules apply to all editions. Differences in authorial paragraphing, canon, versification, note apparatus or section extent are retained as genuine differences between editions, not normalized away. If a client needs fallback display (e.g. chapter-only commentary shown while viewing a verse), implement it in the reader; do not rewrite the underlying resource.

## Checks that must be independent of the corpus under test

The validator must include positive and negative synthetic fixtures for: noncanonical book wrapping, duplicate canonical/compound IDs, reuse of milestone keys, missing/reversed boundaries, incorrect book/chapter ownership, title/paragraph/poetry scope, note-anchor retention, malformed/missing/unverifiable reference targets, commentary book/chapter/verse/range mapping and loss of authorial scope. Include a case that is valid under the official OSIS XSD but **rejected by the BRNP canonical target**, and a case that is BRNP-shaped but XSD-invalid. This prevents reducing BRNP to a synonym for OSIS validity.

For every migration, capture a pre-approved transformation plan with pinned input hash and historical evidence; compare **all** original and proposed textual tokens, punctuation, canonical keys and omissions, section/paragraph/poetry boundaries, note and reference labels/anchors/targets, commentary spans, lexical associations and metadata. Validate idempotence, reproduce the same output hash, and retain the original bytes for reversal. Any difference not explicitly described in the reviewed ledger blocks the candidate, even if BRNP diagnostic counts decrease.

A lower diagnostic count is **never** proof of greater fidelity. A BRNP result can become a publication gate only when these checks and real-corpus/native-reader parity are implemented and independently accepted.

## Severity and evidence policy

A diagnostic is not automatically an error in the historical source. It is a **failure to demonstrate conformity of the cleaned representation** until resolved. Distinguish: (a) malformed OSIS/XSD-invalid input, (b) a proven BRNP structural violation (such as duplicate canonical IDs or unmatched milestones), and (c) an **unresolved semantic/editorial association** (such as a visible cross-reference label without an independently established target). Do not suppress (c) to obtain an empty report, but do not invent destinations merely to satisfy BRNP either.

An OSIS-valid source representation may be different from the canonical cleaned target. The original remains immutable. Migration requires a reviewed and SHA-bound operation, a text/markup/reference-preserving equivalence proof, and correct native SWORD readback. The BRNP inspector remains a partial, read-only diagnostic until the complete profile and independent evidence are accepted.

## Validation is layered

1. Pin immutable upstream data, historical edition witnesses, rights and provenance.
2. Validate **official OSIS 2.1.1 XSD** (pinned at `config/osis-policy.json`) and XML syntax. A document cannot pass BRNP by skipping the schema.
3. Run the independent, read-only BRNP structural checker. Its current v0.2-draft subset checks identity, reviewed element names, unique canonical IDs, book/chapter scope, compound verse membership, verse pairs, commentary reference grammar, poetry grouping and unresolved cross-reference targets; **it does not yet prove all hierarchy, target resolution or semantic conditions in this specification**.
4. Review source-to-cleaned differences and, separately, historical edition-to-cleaned evidence. Record normalized markup, deleted digital-only artifacts, and every unresolved editorial case.
5. Check clean-to-native SWORD text, notes, structure and key parity, then multiple readers; document unavoidable renderer differences.

For each stage record input/output SHA-256, schema and checker version, diagnostic paths/locations (without copying copyrighted source prose), exact transformation plan and independent evidence. Failure at any mandatory existing gate blocks release. BRNP-specific enforcement requires acceptance of issue #451 and owner approval.

## Deterministic normalizer requirements

A future write-mode normalizer must (1) write to a separate output, (2) never mutate the original, (3) be idempotent, (4) accept only source-hash-bound reviewed rules, (5) preserve meaningful content and semantics with automated comparison, (6) report every operation and its rationale, (7) block unfamiliar structures instead of guessing, and (8) offer reproducible reversal from the original and declared transformation plan.

**Do not run a normalizer on already released OSIS just because this spec exists.** Existing editions require an impact report and individually approved migration/republication.

## Adoption criteria

Issue #451 remains open until: XSD evidence, a fully specified and independently tested hierarchy validator, synthetic positive and negative fixtures, real-corpus audits of LSG/Darby/MHCC/MHC, source/historical-witness assessment, clean-to-SWORD proof, reader checks, and explicit owner adoption decision. An unexecuted or partial pilot is not certification.
