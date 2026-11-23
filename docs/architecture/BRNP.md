# Bible Resources Normalization Profile (BRNP) — working specification v0.1

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
| Poetry | `lg` for evidenced groupings; `l` and `level` when attested, keeping order | Convert poetry to prose or invent stanzas/indentation |
| Titles | `title` at the documented semantic location and type permitted by the official schema | Promote provider UI headings to authorial headings |
| Tables and lists | Preserve evidenced `table`/`row`/`cell` and `list`/`item` content and order, including historically meaningful apparatus | Flatten structured content to prose or call it "noise" simply because a digital source uses tables |
| Header metadata | Preserve standard `identifier`, `description`, `date`, `rights`, `type`, `refSystem`, `revisionDesc` and their provenance separately from authorial content | Present a provider revision log as a title/note written by the biblical author |
| Quotes and emphasis | Preserve `q`, `hi`, `transChange`, `divineName` and intended extent | Infer quotation marks, italicization or divine-name conventions |
| Notes | `note` with original meaningful type and association | Merge, re-anchor or delete content notes merely to simplify layout |
| References | `reference` with reviewed `osisRef` where the target is independently established; unresolved targets must be reported | Invent a destination or turn plain prose into a guessed link |
| Lexical alignment | `w` with verifiable lemma/morph associations and exact word extent | Invent Strong/MACULA mappings or split joined words heuristically |
| Commentary | Dedicated `div` with `annotateType="commentary"` and reviewed `annotateRef`; preserve authored scope and introductions | Duplicate chapter-level commentary across verses in source or fabricate a verse-level scope |

OSIS permits more than one representation for certain overlapping structures. BRNP chooses a deterministic representation **only after** equivalence has been proved with positive/negative fixtures and relevant real editions. Unknown, ambiguous or otherwise schema-valid constructs are reported for review, never auto-flattened. No edition-specific hidden exceptions.

## Validation is layered

1. Pin immutable upstream data, historical edition witnesses, rights and provenance.
2. Validate **official OSIS 2.1.1 XSD** (pinned at `config/osis-policy.json`) and XML syntax. A document cannot pass BRNP by skipping the schema.
3. Run the independent, read-only BRNP structural checker. Its currently recovered v0.1 subset checks identity, reviewed element names, verse pairs and commentary annotations; **it does not yet prove all hierarchy, target resolution or semantic conditions in this specification**.
4. Review source-to-cleaned differences and, separately, historical edition-to-cleaned evidence. Record normalized markup, deleted digital-only artifacts, and every unresolved editorial case.
5. Check clean-to-native SWORD text, notes, structure and key parity, then multiple readers; document unavoidable renderer differences.

For each stage record input/output SHA-256, schema and checker version, diagnostic paths/locations (without copying copyrighted source prose), exact transformation plan and independent evidence. Failure at any mandatory existing gate blocks release. BRNP-specific enforcement requires acceptance of issue #451 and owner approval.

## Deterministic normalizer requirements

A future write-mode normalizer must (1) write to a separate output, (2) never mutate the original, (3) be idempotent, (4) accept only source-hash-bound reviewed rules, (5) preserve meaningful content and semantics with automated comparison, (6) report every operation and its rationale, (7) block unfamiliar structures instead of guessing, and (8) offer reproducible reversal from the original and declared transformation plan.

**Do not run a normalizer on already released OSIS just because this spec exists.** Existing editions require an impact report and individually approved migration/republication.

## Adoption criteria

Issue #451 remains open until: XSD evidence, a fully specified and independently tested hierarchy validator, synthetic positive and negative fixtures, real-corpus audits of LSG/Darby/MHCC/MHC, source/historical-witness assessment, clean-to-SWORD proof, reader checks, and explicit owner adoption decision. An unexecuted or partial pilot is not certification.
