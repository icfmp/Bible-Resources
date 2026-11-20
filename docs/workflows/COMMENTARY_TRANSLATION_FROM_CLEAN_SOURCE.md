# Reusable commentary translation workflow — from an accepted clean source

**Purpose:** produce a faithful, readable translation or language modernization of an **already cleaned, structurally validated and reader-tested** commentary. The translation and the relocation of existing cross-references are the work. **Do not restart source acquisition, source repair, source-link correction or historical reconstruction.**

**Relationship to other policies:** this is the **translation sub-workflow** used within [Commentary onboarding](COMMENTARY_7_STAGE_WORKFLOW.md) and the [source-first editorial pipeline](SOURCE_FIRST_EDITORIAL_PIPELINE.md), not an alternative publication path. [Commentary policy](../policies/COMMENTARY_POLICY.md), [editorial rules](../policies/EDITORIAL_RULES.md), [rights](../policies/RIGHTS.md) and [publishing](PUBLISHING.md) continue to apply. The historical [HMCC Modern English production protocol](../../sources/cleaned/commentaries/en/hmcc-modern/editorial/HISTORICAL_PROTOCOL.md) records edition-specific discoveries and experiments, **not steps to repeat for every next translation**.

## 0. Entry contract: accept a finished, verified source

Before translating, require one explicit, approved **clean-source handoff**:

- Exact work/edition and upstream identity; language; canon, versification, commentary boundaries and scope.
- Immutable **clean editable source** (prefer standard OSIS where appropriate), its SHA-256 and provenance. Keep it read-only; translate into separate files.
- Passing source structure/schema and native SWORD/index/reader evidence, including introductions, headings, verse/range associations, notes, quotations and references.
- Source reference inventory: every link's **source occurrence identity** and correct, validated destination(s), including notes and references in titles, lists and introductions.
- Existing editorial decisions (including excluded, deliberately unlinked or intentionally ambiguous citations), plus the original rights and the **separate** rights for distributing a translation.
- A declared destination-language/style brief and a named source of authority for editorial review.

**Gate:** source integrity, source-link accuracy and redistribution/derivative rights are resolved **upstream of this workflow**. If any of these inputs is missing or an actual source defect is discovered, stop and return a **source handoff issue**. Do not silently repair the source inside the translation branch, invent a target or redo the full source-cleaning pipeline.

The input contract is generic; a CrossWire SWORD `K` entry or an HMCC 0.1.1 module ID is **not** required for other works. The source-specific importer is responsible for yielding a canonical inventory of ordered editorial units and reference occurrences.

## 1. Freeze a translation manifest and editorial brief

Create a new independent translation/edition identity; do not overwrite the validated source edition. Pin:

| Field | Required meaning |
| --- | --- |
| `source_id`, `source_revision`, `source_sha256` | Exact accepted clean source; immutable throughout the run |
| `source_units` | Book introductions, chapters, commentary entries, ranges, paragraphs, headings, lists, quotations and notes, in source order |
| `source_link_occurrences` | Stable source unit ID + source element path/ordinal + normalized destination set + source visible label |
| `target_language`, `edition_name`, `style_brief` | Target audience and intended translation register |
| `rights`, `editorial_decisions` | Source and derivative permissions, approved policy on adaptation |
| `pipeline_revision` | Reproducible tooling and validation version |

Do not identify a cross-reference solely by its destination: the same passage can be cited several times in different contexts. Track the **individual source occurrence**, not just the set of distinct URLs.

An original range association such as `Gen.1.1-Gen.1.5` identifies where an exposition belongs in the reader; an inline `osisRef` identifies where an authorial citation points. **These are different links and must not be conflated.**

## 2. Translate in bounded, complete editorial units

Use the **chapter** as an understandable review/checkpoint unit, but translate **each original commentary exposition** as an independent, traceable semantic unit. Include introductions, passage-level titles, tables, quotations and authorial notes in their own appropriate source units; do not assume all source material is attached to verse 1.

A chapter may contain multiple original expositions, one exposition shared by many verses, or a chapter-only comment. Respect that structure and the source's versification. Do not duplicate or split expositions just to populate otherwise empty SWORD verse keys. Reader-specific fallbacks belong to the reader or separately reviewed mapping policy.

For every bounded batch:

1. Read the entire clean source unit **in context** (preceding/following expositions, book and chapter). Capture source unit ID, original position and associated passage key(s).
2. Draft natural target-language prose with theological meaning, argument progression, modality, qualifications, authorial voice, emphasis and Scripture quotations intact.
3. Preserve the distinction between the author's statement and an editor's statement. Translate the source's theological claims; do **not** silently correct, soften, expand, harmonize or update its doctrine.
4. Keep every source content unit represented exactly once. Do not summarize, invent conclusions or omit redundancies solely for stylistic elegance. A translation may naturally change sentence length and paragraphing **when the declared modern edition policy permits it**, but must preserve all meaningful logical divisions, headings, lists, quotations, notes and scope.
5. Save the draft in its native target editorial unit, with stable source-to-target correspondence; keep the input unchanged. Distinguish `draft`, `meaning-reviewed`, `structure-verified` and `reader-tested`—none implies another.
6. Review complete batches in order; preserve the ability to resume from committed accepted units, not the last assistant message.

### Semantic review: very good, not pretend-perfect

Review the translation **against the actual source**, not only against English/French fluency. Check for:

- Negation, conditionals, obligation/possibility, tense/aspect and who does what to whom.
- Causes, contrasts, chronology, pronoun antecedents, comparisons and rhetorical questions.
- Scriptural allusions, quotation boundaries, doctrinal distinctions and theological terminology.
- Qualifications and limitations that change the author's claim; the distinction between the author's words and embedded biblical text.
- Missing source paragraphs, tables, sentences, headings or clauses; any additions introduced for clarity.

A fluent sentence with altered meaning **fails**. Use consistent terminology where context supports it, but do not rigidly force one rendering when it changes the meaning. Fix substantive discrepancies in the target draft, then recheck that whole affected unit. Prefer sampling independent human/editorial comparisons and high-risk passages over pretending an automated checker can certify every nuance. Record any unresolved ambiguity transparently.

**Calibration:** review a small, diverse pilot (narrative, argument, poetry/allusion, a long entry, an introduction and a reference-dense section); agree on register and level of modernization, then use the same principles across the entire translation. Do not change style ad hoc per chapter.

## 3. Put every existing link back at the right target-language location

**Critical principle:** translate the **visible citation wording**, but preserve its source-attested navigational target. A successful translation must not merely retain the count of links: each one must point to the right passage **and be attached to the right words or editorial context**.

### Link-transfer algorithm (source-neutral)

1. **Extract before translation:** from the clean source, enumerate each reference occurrence with stable ID, containing unit, type (inline `reference`, editorial `note`, title/list/intro citation, etc.), visible text, exact source token/span or element anchoring, ordinal/context, and normalized `osisRef` destination set. Record the intended destination language's verse naming separately from canonical OSIS IDs.
2. **Translate content before inserting link markup:** produce the target prose including translated or localized citation labels, while keeping explicit occurrence placeholders/anchors in the intermediate draft. Placeholders are **editorial metadata**, never visible published text.
3. **Align semantic anchors, not character offsets:** locate where the original cited concept, quotation or explicit Bible reference appears in target-language prose. Sentence order and length change during translation; do **not** reuse byte offsets, inject the link into the nth occurrence of a common word, or assume the original citation label remains verbatim.
4. **Reinsert the exact link into the target structure:** an inline source reference stays on the translated citation or clearly corresponding phrase; a source footnote stays a footnote at the same **semantic attachment point**; a title/list/introduction reference stays with the corresponding translated element. Preserve authorial vs editor-added note types and accessibility/visibility semantics.
5. **Verify one-to-one occurrence mapping:** for each source occurrence, record **one verified target occurrence**, preserving the expected destination set. Compare multiplicity (including repeated identical references), section ownership, type, label semantics and target. No duplicate, missing, dangling or unexpectedly introduced link.
6. **Treat uncertain alignment as a review item:** if the cited phrase no longer exists because the translation accidentally omitted its meaning, repair the translation **before** placing the link. If the source has a legitimate citation with no natural in-prose anchor, retain it in the corresponding source-attested note or editorial element according to the **approved edition policy**; do not manufacture authorial prose to accommodate it. If there is no approved location, block the affected unit for review.

**Allowed:** a translated reference label such as “Hebrews 11:8” instead of “Heb. xi. 8”, still pointing to the **same** OSIS destination; layout/placement adjusted to the translated clause.  
**Not allowed:** inventing a link, assigning a different target on an interpretive hunch, silently dropping a citation because its words changed, attaching all unattached links at the end of a chapter, or correcting the clean source's destination during translation.

### Example — occurrence identity and semantic placement

```xml
<!-- Source-clean, validated: hypothetical excerpt -->
<p>See <reference osisRef="Heb.11.8">Heb. xi. 8</reference> for his faith.</p>

<!-- Target language: wording/order changes, link belongs to translated citation -->
<p>Sa foi est présentée en <reference osisRef="Heb.11.8">Hébreux 11.8</reference>.</p>
```

This is illustrative markup, **not** text extracted from Matthew Henry. Both target and attachment are checked; preserving `Heb.11.8` alone would not prove a correct placement.

### Reference classes to test deliberately

- Inline authorial references and multiple references in the same sentence.
- Citations in headings, book introductions, lists, tables, quotations and notes.
- Whole-chapter, verse-range and discontinuous references.
- A repeated destination with **multiple original occurrences**.
- A source link whose visible reference label is paraphrased in the target translation.
- A note marker attached to a translated phrase rather than to the original character offset.
- Right-to-left or other target scripts when relevant; escape/normalize safely without changing the underlying reference identity.

If the clean source deliberately contains an unlinked or unresolved reference, **inherit that reviewed classification**. It is not permission to add new destinations during translation.

## 4. Validation gates — meaning, structure and navigation are separate

| Gate | Observable pass condition | What it does **not** prove |
| --- | --- | --- |
| **Source pin** | Original clean source SHA and source-unit/occurrence inventory exactly match the accepted handoff | Translation quality |
| **Coverage** | Every original translatable unit and required introduction/heading/note has one traceable target unit; no unexplained missing units or new material | Correct wording |
| **Semantic comparison** | All high-risk discrepancies resolved, sampled independent review documented, translation decisions recorded | Full automatic semantic equivalence |
| **Link identity** | Exact **multiset** of source occurrence IDs and destinations equals the target multiset; no phantom link | Correct visual attachment |
| **Link placement** | Every target occurrence is in the right target unit, component type and **semantic location**; reviewable source→target anchor receipts | GUI click behavior |
| **Standard markup** | Target OSIS/other standard is schema-valid; correct `annotateRef` section scopes; no dangling placeholders or invalid references | Actual SWORD compilation |
| **SWORD roundtrip** | Build distinct native module; all expected K/I/TOP mappings and representative full annotation/reference content independently read back; no unexplained losses | Third-party GUI behavior |
| **Actual readers** | Install in isolated SWORD reader(s), inspect prose/layout and click a representative set of **inline and footnote** links | That every link was manually clicked |
| **Release** | Human editorial/rights authorization; final immutable ZIP SHA, version, metadata and catalogue/release verification | Retroactive acceptance of pending editorial cases |

For a complete handoff, produce a machine-readable **link relocation receipt** with at least:
`source_occurrence_id`, `source_unit_id`, `source_type`, `source_label`, `source_destinations`, `target_unit_id`, `target_type`, `target_label`, `target_destinations`, `target_semantic_anchor`, `placement_review_status`. The source/target mapping must have a unique source occurrence ID and a unique target attachment per occurrence; keep a bounded exception list with real editorial dispositions. Do **not** hard-code HMCC-specific verses or counts as universal validation rules.

Inspect the structured target **before** compilation, the compiled OSIS/XML **after** SWORD readback, and actual reader interactions separately. A `diatheke` result can prove native accessibility, but not Xiphos click behavior. If GUI automation is inconclusive, label it `INCONCLUSIVE` or `NOT TESTED`; a human manual check may be explicitly scheduled or authorized separately, without relabeling it PASS.

## 5. Batches and reproducible handoff

Use small, meaningful batches (whole chapters or consecutive chapter groups as appropriate), with automatic coverage and source-link checks in every batch. A logical chapter batch must not fragment an individual commentary entry. Prefer sustained batch processing once the pilot is calibrated rather than one manual chat exchange per verse.

Suggested persisted records:

```text
translation/<edition>/
  README.md                         # Style brief, source pin, rights and decisions
  manifest.json                     # Units and reference occurrence inventory
  target/                            # Editable target standard sources
  audits/                            # Per-batch semantic and structural reports
  links/                             # Occurrence-to-anchor relocation receipts
  build/                             # Reproducible build config, no private original
```

This is an **illustrative organization**, not a mandatory proprietary data format. Prefer existing repository directories and source standards. Never upload restricted input to public workflows or logs. Keep checksums and concise receipts public only when rights permit.

A meaningful checkpoint records: accepted source SHA, precise target coverage, link occurrence coverage and placement status, substantive translation ambiguities, native/reader outcomes, current commit, and next unprocessed batch. A single unreviewed draft is not an accepted translated chapter.

## 6. Completion and publication

The translation is editorially complete only when **all** accepted source units are represented, translation-level review has passed at the declared standard, **all inherited links are accounted for and correctly located**, and no unresolved source/target mapping remains silently hidden.

Build under a **new SWORD module ID and version**, preserve the original unchanged, include an edition/translator attribution and independently reviewed redistribution rights for the new translated text. Confirm the compiled module's real reader index and the release-plan/catalogue binding. Use the repository's existing [single Release-before-Pages publisher](PUBLISHING.md); never introduce a translation-specific shortcut.

**Lessons retained from HMCC Modern:** produce readable text while protecting doctrinal nuance; use stable source units, not verse-by-verse guesswork; restore citation markup according to the translated **meaningful anchor**, not the source's character position; keep cross-references auditable by individual occurrence; distinguish automated structural proof from human semantic acceptance and actual reader navigation. The source-cleaning, original-source error correction, historical restoration and unusual HMCC-only source experiments were preparation for that particular edition, **not part of this reusable translation procedure**.

**Reusable definition of done:** `source accepted → translated in accountable units → meaning reviewed → links reattached one-to-one at correct semantic anchors → standard/native roundtrip passed → real-reader checks recorded → owner/rights/release gates passed`.
