# Resource presentation and evidence policy

## Scope

Bible Resources curates selected, rights-cleared editions, not the entire inventories of CrossWire, eBible or other upstream providers. Initial active language priorities are French (`fr`), English (`en`), Spanish (`es`) and Portuguese (`pt`, preserving edition-specific `pt-BR`/`pt-PT` distinctions). Other languages remain accessible from the application's independent providers; this is a curation priority, not a technical language ban.

Each published Bible, commentary, dictionary or general book must have an accurate, attractive reader-facing description **and** a traceable editorial record. Descriptions are separate from the immutable source text and never alter, reinterpret, fill or suppress any Scripture, note or reference.

## Reader-facing information architecture

1. **Identity:** exact work and edition title, common abbreviation(s), language, translator/editor, edition date, category, scope/canon and documented versification if relevant.
2. **Brief introduction:** one or two factual paragraphs: historical context, intended audience and distinctive features. Avoid advertising language, unsourced superlatives and claims that the edition is identical to a different publication.
3. **Strengths / points of attention:** concise, optional items that aid selection rather than assigning a doctrinal score. Each visible item links to an evidence record; if none is adequately supported, show no item rather than invent one.
4. **Source and rights:** identify separately (a) original author/translator and edition/publisher, (b) acquisition provider, module ID and original downloadable source, and (c) Bible Resources' own curated edition, version, changes and reviewer. Show exact redistribution/derivative permissions and mandatory attribution.
5. **Details:** format, notes, references, available apparatus, limitations, changelog, last reviewed date and links to the source documents. Keep verbose technical and legal details behind a secondary view, but never hide mandatory attribution.

An app presentation may abbreviate these fields, but links must lead to the complete, accessible provenance and evidence. A downloaded resource retains its attribution and source information offline.

## Evidence rules for strengths and cautions

**No public caution without a verifiable justification.** Apply the same factual standard to positive claims.

Every claim must record:

- An immutable local claim identifier; the exact edition and revision to which it applies; claim category (`textual_variant`, `translation`, `historical`, `linguistic`, `editorial`, `technical` or `interpretive`); and short reader-facing wording.
- The relevant biblical verse(s) or other exact source location(s), where applicable. Record original and comparison editions accurately; do not conflate different revisions.
- The observation and method (e.g. comparative transcription, Greek manuscript reading/critical apparatus, grammar, source-to-SWORD markup audit, or reader rendering). Separate a directly observable fact from an interpretation.
- Traceable references: full bibliographic identity and page/section or exact stable URL/locator, and where feasible primary text evidence. Do not rely on a bare assertion, a non-identical edition or an unattributed secondary opinion. Record what the evidence actually supports.
- A source-qualified explanation of competing interpretations when the matter is disputed. Explain if a difference results from textual criticism, translation grammar, editorial policy or an application rendering defect.
- Review status (`candidate`, `substantiated`, `disputed`, `withdrawn`), reviewer, review date, and an audit/change history or link. Only `substantiated` claims with evidence and editorial approval can be displayed as established observations; contested conclusions must be labelled as such and fairly explained.

An allegation about the **translator's intention, systematic bias, religious motives or deliberate suppression** is especially strong: a set of differences or a later critic's accusation is not by itself proof of intent. Quote the critic as a historical criticism if relevant, identify their position, test representative counterexamples, and refrain from stating intention as fact without direct evidence. A manuscript reading that differs from the Textus Receptus does not, by itself, prove hostility to Christ's divinity.

Keep reader-facing text neutral, concise and non-polemical. Include the original passage and references only to the extent legally permissible. Prefer a small number of well-evidenced claims to a longer speculative list. Claims can be revised or retracted without modifying the biblical resource.

## Review and publication gate

- Draft profiles and claim candidates may be kept in the repository while evidence is gathered, visibly marked **DRAFT — NOT FOR PUBLICATION**. Their statements must not be automatically added to a public catalogue or app.
- A reviewer verifies factual accuracy, edition identity, source fidelity and legal attribution; contentious theological claims need appropriately qualified source review.
- No profile or caution is approved solely because an automated test passes. The project owner approves consequential editorial characterizations before publication.
- Publish profile revisions with provenance, date, reviewer and changelog, independently of SWORD module version where the underlying text has not changed.
- A published claim must offer an evidence link and a correction path; if substantiation breaks, unpublish the claim until it has been reviewed again.
- Software/build pipelines must not treat an incomplete profile as an authorization to publish unapproved texts, modules or derivative annotations.

## First application: Louis Segond 1910

The [Louis Segond 1910 profile](profiles/fr-segond-1910.md) is a **reader-presentation draft**, separate from the independently owner-approved and [published LSG 0.1.0 SWORD module](../modules/lsg-1910/EDITORIAL.md). The [release notes](releases/LSG-0.1.0.md) disclose the actual source and known rendering/versification limits. The profile must not claim that print-edition comparisons or disputed theological explanations have been certified. Prior source research in PRs #18 and #24 is historical evidence, not a substitute for source citations or approval of reader-facing interpretations. No change to the published Bible text or module is authorized by this policy.

**Implementation boundary:** the policy and draft are documentation, not a machine-enforced catalogue display contract. The current JSON catalogue still publishes the reviewed module metadata; an approved editorial profile and its provenance must be explicitly reviewed before the application surfaces additional reader-facing strengths or cautions. Do not infer approval from `quality.status=approved` alone.
