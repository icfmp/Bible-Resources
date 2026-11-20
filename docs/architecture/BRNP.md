# Bible Resources Normalization Profile (BRNP) — version 0.1

**Status: proposed canonical-target contract; validation pilot, not yet a publication gate.** The owner approved the principle of structural normalization on 2026-11-20. This version describes the representation to target for **new, reviewed cleaned OSIS Bible and commentary masters**. It does **not** retroactively certify or rewrite existing modules. Promote to a mandatory gate only after the independent schema, source-fidelity, native SWORD and reader tests below pass on representative real editions.

## Goal and authority

Normalize *how* existing authorial information is represented so imports are predictable across sources. Never normalize *away* content or editorial distinctions. The official [OSIS 2.1.1 schema](https://wiki.crosswire.org/OSIS), [CrossWire Bible guidance](https://wiki.crosswire.org/OSIS_Bibles), [commentary guidance](https://wiki.crosswire.org/OSIS_Commentaries) and approved SWORD configuration remain normative. BRNP is a **strict, versioned implementation profile**, not an invented XML namespace, new OSIS dialect, or substitute for the official XSD.

A normalization is permitted only if it is:
1. **Meaning-preserving:** same words, punctuation, sequence, authorial notes and their locations, annotations, references and targets, verse/entry identity, passage coverage, emphasis, paragraph and poetry boundaries, and edition metadata.
2. **Evidence-based:** source and target are pinned; every structural mapping is in an approved, reversible ledger with independent verification.
3. **Deterministic and idempotent:** a second normalization has no semantic or structural changes. Byte-level stability must be tested separately against the chosen serializer.
4. **Fail-closed:** unrecognized but schema-valid constructs, ambiguous overlapping boundaries and unrepresentable authorial structure are *blocked*, never silently flattened.
5. **Reader-verified:** passing OSIS and BRNP structure checks does not establish native SWORD parity or identical behavior across SWORD readers.

## Layers and accepted output

| Layer | Role | Evidence |
| --- | --- | --- |
| Original (OSIS, USFM, USFX, compiled SWORD, etc.) | Immutable source, **never** forced into BRNP | Exact edition, format, rights and SHA-256 |
| Cleaned canonical target | **OSIS 2.1.1** for Bibles/commentaries, retaining source-attested structure | Official XSD, `guard_osis.py`, `guard_commentary.py` where applicable, BRNP report, source/target diff |
| Compiled module | SWORD compatible driver and `.conf`, preserving native semantics | Full readback, native key/annotation audits and independent readers |
| Other resources | TEI dictionaries / general books | **Not specified in v0.1**; independently versioned profiles required, no fictional support |

**Not every source can be converted without loss.** BRNP is a target for representable source structures, not a license to reflow authored works. Existing source-only modules may remain outside the profile until explicitly migrated.

## Common hierarchy

- One `osis` document containing an `osisText`, with documented `osisIDWork`, `osisRefWork`, language and validated `header/work` metadata appropriate to the actual edition. Do not fabricate bibliographic evidence or change `canonical` status for convenience.
- Bibles: hierarchy of **book** `div type="book" osisID="..."`, `chapter` and numbered `verse` elements/milestones following *the resource's real versification*. Normalized XML does not impose the KJV scheme or a fixed canon.
- Commentaries: `div annotateType="commentary" annotateRef="..."` is the mapping unit, with any appropriate `type` and surrounding authorial hierarchy. Its passage scope can be single, ranged or discontinuous. Multiple distinct entries for one passage remain distinct.
- For Bible paragraphs that **cross verse boundaries**, prefer balanced `p` containers around paired `verse sID`/`verse eID` milestones when the source's boundaries can be preserved. Do **not** force nested container `verse` elements through paragraph boundaries, or invent paragraph ends at verse boundaries. For source structures that cannot be represented unambiguously under this convention, block pending review.
- Source-authored book/chapter introductions, headings, title positions, and verse-zero material are not numbered Scripture and must remain distinguishable.

## Semantic constructs: representation invariants

| Information | Standard representation | Invariant / prohibited shortcut |
| --- | --- | --- |
| Numbered verses | `verse osisID` or correctly paired `sID/eID` | One exact source identity; no invented/moved/deleted verses; no automatic KJV mapping |
| Paragraphs | `p` boundaries | Only source-attested paragraphs; never infer from screen width or verse count |
| Poetry | `lg` / `l` and reviewed `level` | Preserve line/stanza membership, order and indentation |
| Headings | `title` in its authenticated context | No promotion of editorial title to canonical verse text |
| Notes | `note`, preserving `type`, `osisRef`, `n` and source content where present | Keep body, caller, anchor, ordering, and note identity |
| References | `reference osisRef` when authorially present | Preserve visible label and literal destination; do not guess targets |
| Emphasis/quotation | `hi`, `q`, `transChange`, `divineName` where source-attested | Preserve semantic distinctions; do not turn quote/emphasis into plain text |
| Lexical markup | `w lemma morph` and associated attributes | Preserve token position, Strong/lemma/morph pairs, RTL ordering |
| Commentary coverage | `div annotateType="commentary" annotateRef` | Preserve original scope and distinct entries; no per-verse duplication of chapter prose |

Attributes absent in the original **must not be invented** (including `osisRef`, note callers, `level`, `lemma`, `morph` or publication metadata). A verified equivalent encoding may replace a source representation only with an approved transformation and tests.

### Example: paragraph extending across two verses (illustrative synthetic text)

```xml
<p xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
  <verse osisID="Gen.1.1" sID="Gen.1.1"/>Example one.
  <verse eID="Gen.1.1"/>
  <verse osisID="Gen.1.2" sID="Gen.1.2"/>Example two.
  <verse eID="Gen.1.2"/>
</p>
```

### Example: one commentary on a range (illustrative synthetic text)

```xml
<div xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace"
     type="section" annotateType="commentary"
     annotateRef="Gen.1.1-Gen.1.2">
  <title>Example heading</title>
  <p>One authorial comment on the whole passage.</p>
</div>
```

These are **fragments illustrating representation**, not complete XSD-valid OSIS documents. Validate complete real files using pinned official schemas and SWORD tooling.

## Normalization transaction and checks

1. Detect and pin original format, source edition, SHA-256, authorial semantics and rights.
2. Inventory *every* source unit and markup relation; classify unsupported structures.
3. Build a **proposed** rule mapping using valid standard constructs and synthetic positive/negative fixtures.
4. Review the rule's text/structure/reference preservation and record approval.
5. Generate a **separate** cleaned target, never overwrite original. Produce entry-level and structural before/after reports.
6. Run pinned official XSD, existing OSIS/commentary guards, BRNP structural checks, exhaustive source/target comparison and **idempotence** checks.
7. Compile independently; compare native content, links and keys; test multiple readers.
8. Only after editorial/rights/owner release approval can the target become a published module.

A failure at any gate leaves original and previously approved releases unchanged. No profile-conformant report can override textual or reader QA failure.

## Pilot implementation and limitations

Run the pilot without modifying the input:

```sh
python scripts/check_brnp.py /path/to/cleaned.osis.xml --kind bible --report /tmp/brnp-report.json
# For commentaries: --kind commentary
python -m unittest tests.test_brnp -v
```

The read-only `scripts/check_brnp.py` checks a **small subset** of the invariants (namespace, source category, verse marker pairing, basic commentary reference presence and unknown structures). It is intentionally **not** a converter, full XSD validator, comprehensive note/link verifier or a release gate. Continue to use `scripts/guard_osis.py`, `scripts/guard_commentary.py` and [production contract](../PRODUCTION_PIPELINE.md).

### Versioning

Any rule changing canonical structure, allowed markup or failure behavior requires a reviewed BRNP version bump, synthetic tests, a corpus migration plan and actual reader validation. Existing approved modules keep their prior proof; do not rewrite previously published bytes under a new profile silently.
