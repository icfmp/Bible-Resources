# Strict SWORD commentary source policy

Commentaries have the same **fail-closed** source-validation rule as Bibles, but
their reference mappings require separate validation. This is not a second XML
dialect: use the **official OSIS 2.1.1 XSD**, with the source-specific commentary
conventions documented by CrossWire.

Primary reference: [CrossWire — OSIS Commentaries](https://wiki.crosswire.org/OSIS_Commentaries).

## Official markup for a commentary entry

    <div type="section" annotateType="commentary" annotateRef="Gen.1.1">
      <title>An author's heading</title>
      <p>The author comments on the passage and quotes it when needed.</p>
    </div>

CrossWire uses \`annotateType="commentary"\` and \`annotateRef\` to map a
commentary **entry** to a biblical reference. The \`type\` on \`div\` does **not**
determine entry identity. A section can comment on one verse, an uninterrupted
range such as \`Gen.1.1-Gen.2.3\`, or several references separated by spaces.
Non-entry \`div\` elements are legitimate wrappers for book groups, books
and hierarchy; they are **not** assigned to a verse by proximity.

The recorded original reference, its bounds, and the grouping must be retained
exactly. The checked, intentionally narrow parser handles straightforward book,
chapter, verse identifiers, in-book ranges and discontinuous lists. Work prefixes
in commentary \`annotateRef\` are rejected because CrossWire's current
commentary importer does not support them. Any unusual but legal reference,
ambiguous range, possible introduction key, or cross-book range is **blocked**
for standards review rather than guessed or silently truncated.

A line in the source might fail with:

    sources/mhc.osis.xml:812: [COMMENTARY_REFERENCE_UNREVIEWED]
    Unreviewed commentary reference 'Gen.1.1@special'; do not guess a verse.

## Preservation rules

- The author's exposition, doctrinal argument, original emphases and division
  structure are content, not formatting noise.
- Quoted Scripture **inside** the commentary is not removable boilerplate.
  It may be essential to the interpretation and may intentionally differ from
  the reader's currently selected translation. Detect suspected duplicate
  quotations for **human editorial review only**.
- Preserve scriptural citations as citations (\`reference osisRef\`), not
  invented anchors for the commentary entry.
- Preserve headings, paragraphs, nested citations, lists, notes, quotations,
  typography and their relationships. Some structures are not yet in our
  reviewed generic OSIS allowlist; these **stop** processing until a rule and
  regression tests are agreed upon. No silent flattening of headings, lists
  or poetic passages is permitted.
- Never merge, discard or reorder independent commentary entries just because
  they annotate the same verse. No automatic rearrangement by verse position.
- Preserve attribution, rights statements, the full original textual content
  and the exact editorial record.

## Reader-oriented navigation is not source-text alteration

An upstream SWORD author's section can be indexed at only its first verse,
even when its actual, independently reviewed editorial scope is a whole
passage or chapter. Source-byte fidelity is **not** a requirement to perpetuate
an inferior index/navigation choice in a separately tracked Bible Resources
correction edition. We prefer discoverability at **every verse actually covered**
while preserving the **one authorial unit** (and displaying it once, not once per
verse). This is a navigational/editorial improvement, not proof that the author
composed distinct comments on each verse.

- For verified chapter-level commentary, keep the label and semantics
  **chapter commentary** and make it discoverable from any verse of that chapter.
- Use **standard OSIS commentary** annotated continuous/discontinuous ranges
  and native SWORD linked verse keys; do not invent a proprietary format.
- Preserve discontinuous sets and all separate commentary sections, and refuse
  to overwrite already occupied, different-payload original keys.
- If the original scope is ambiguous, **do not** infer it from the presence of
  only the chapter's first native key or from a citation `scripRef` alone.
- All alias proposals require reviewed section bounds, independent actual
  versification keys, immutable raw text hashes, an explicit delta, real
  reader deduplication verification and a reversible rollback receipt.
- Keep the exact upstream source and original release untouched; publish any
  corrected edition only after normal rights, editorial and owner publication
  gates.

Generic read-only proposal logic is in
`scripts/commentary_navigation_link_plan.py`; the initial use case,
limitations, and the owner's approval of this **direction only** are documented
in `docs/evidence/mhcc-274/reader-oriented-indexing-decision.md`.

## Current gate

The **read-only** command \`scripts/guard_commentary.py\` first uses the
reviewed-XSD OSIS guard, then checks each annotated section. It records:
- \`source_kind: commentary\`
- original source SHA-256, official schema and generic OSIS policy SHA-256
- commentary policy SHA-256
- annotation count and ordered reference-mapping SHA-256
- either \`validated\` or \`blocked\`, with the exact source file and line

Run (when the official OSIS XSD is reviewed and pinned):

    python scripts/guard_commentary.py sources/commentary.osis.xml \
      --schema path/to/reviewed/osisCore.2.1.1-cw-latest.xsd \
      --report modules/example/SOURCE_VALIDATION.json

An **approved commentary** is blocked by \`scripts/validate.py\` if the
report is missing, generated by the generic Bible-only guard, uses a stale
commentary policy, or includes no reviewed commentary entries.

The official CrossWire OSIS 2.1.1 XSD and its single W3C xml.xsd
dependency are now SHA-256 pinned and verified with strictly local
dependency resolution. This makes the schema gate usable for real source
checks, but **no real MHC source has been validated, normalized or approved**.
The offline unit tests continue to use synthetic test-only XSD fixtures.

## Boundaries and next work

The script does **not** convert or normalize commentary text. It does not
inspect compiled \`RawCom\`/\`RawCom4\`/\`zCom\` modules or generate binaries.
When only compiled SWORD data are available, the future extraction adapter
must identify provider/module/entry key instead of inventing an original XML
line number.

SourceType=ThML, plaintext, and TEI are **not** automatically treated as OSIS:
each needs a standards-based importer and its own rules. The type and exact
line/entry of an unknown source construct must be reported and its handling
reviewed before any future normalization.

The eventual production pipeline still needs a source-to-SWORD round-trip
comparison, reference coverage checks, verified permissions for derivative
editions, and a real SWORD reader smoke test. Passing the **current** source
gate is necessary but not sufficient for publication.

See also [NORMALIZATION_POLICY.md](NORMALIZATION_POLICY.md) and
[EDITORIAL_RULES.md](EDITORIAL_RULES.md).
