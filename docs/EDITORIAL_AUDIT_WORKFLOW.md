# Reversible OSIS editorial audit and normalizer

**Purpose:** find concrete defects without modifying Scripture or commentary
text. Approved transformations only restore reviewed *layout boundaries*.
This is not an AI rewriting pass and not a replacement for SWORD/OSIS validation.

## Stage A — Inspect a REAL original source

An original OSIS source is not the same thing as SWORD's \`zText\` or \`zCom4\`
compiled data. Obtain a source from the publisher and record its edition,
language, license, source URL, original bytes/SHA-256 and version. Never
fabricate original XML source lines from a SWORD binary.

Run the independent **read-only diagnostic** first:

    python scripts/audit_osis.py original.xml --kind bible \
      --report reports/bible-structure.json

For commentary use \`--kind commentary\`. It reports potential long bold
spans, all-caps blocks, unusual headings, long paragraphs, presentation-only
styling, possible introductory Biblical quotations, syntactic cross-reference
problems, duplicate verse identifiers and suspicious source key order.

These are **candidates**, not commands. Genuine authorial emphasis, separate
commentary entries, translation notes and historical spellings may look odd.
Nothing is removed automatically. A syntactically valid reference is **not**
proof it exists in the module's SWORD versification; canonical validation
must be performed separately.

The diagnostic's \`source_schema_validated\` is always **false**. To validate
the real source against the *official reviewed* CrossWire OSIS 2.1.1 schema:

    python scripts/fetch_reviewed_schema.py --directory /tmp/reviewed-osis

    python scripts/guard_osis.py original.xml \
      --schema /tmp/reviewed-osis/osisCore.2.1.1-cw-latest.xsd \
      --report reports/osis-validation.json

For commentary additionally use \`scripts/guard_commentary.py\` with the
same schema. Malformed/unknown structures **block** approval with a source
file and XML line. They are not guessed or silently corrected. TEI and USFM
require their own standards-based source handlers, not OSIS repackaging.

## Stage B — Explicit reviewed plan, never free-form rewriting

A normalizer plan is a JSON file. It must contain:

- exact \`source_sha256\` and \`kind\` (\`bible\` / \`commentary\`);
- \`edition\`: \`faithful\` if a matching source proves the restoration, or
  \`reader_optimized\` for an editorial adaptation;
- explicit \`approved_for_structural_edits: true\` **after a real reviewer
  has checked the change**; \`review.reviewed_by\`, a meaningful decision,
  and \`review.evidence_url\` documenting the editorial source;
- confirmed \`rights.redistribution_allowed\` and source URL; for a
  \`reader_optimized\` derivative, also \`rights.derivatives_allowed: true\`;
- one or more **specific** \`edits\`, each with a real \`source_reference\`,
  reason, exact positional \`node_path\`, and SHA-256 for the original
  selected subtree. Keys and paths are obtained from the actual original
  XML; do not copy a path from a different edition.

Only the following operations are currently reviewed:

1. **\`split_paragraph\`** — split one plain, unannotated OSIS \`<p>\` at
   exactly one occurrence of \`right_starts_with\`. Never strips punctuation,
   adds words or breaks through an inline note or Strong marker.
2. **\`split_before_child\`** — split a paragraph at a direct inline child
   index, moving the entire child subtree and all following siblings to
   the next paragraph. Only reviewed OSIS inline elements may move;
   citations, Strong tags, note content and references remain complete.
3. **\`group_poetry_lines\`** — group 2–100 consecutive, unannotated
   \`<p>\` elements as one \`<lg>\` with one \`<l>\` per source paragraph.
   The line text, inline markup and original whitespace are preserved.
   The grouping requires explicit review of stanza/verse meaning; no
   automatic splitting at verse boundaries or guessing from indentation.

For \`split_paragraph\` and \`split_before_child\`, the anchor is the SHA-256
of \`etree.tostring(node, encoding="UTF-8", with_tail=False)\`.
\`node_path\` is the zero-based list of XML child positions from the root,
available from \`normalize_osis.element_address(node)\`. For
\`group_poetry_lines\`, \`expected_element_sha256\` is the SHA-256 of the
selected paragraph serialization concatenated with NUL bytes. See the
synthetic, runnable examples in \`tests/test_editorial_pipeline.py\`.

The reviewer field is an **assertion stored in the plan**, not a cryptographic
signature. A release auditor must independently verify it, the rights URLs,
and the original edition metadata. Never claim that GitHub CI independently
attested the identity of the reviewer.

## Stage C — Apply into a DIFFERENT local file, inspect diff

    python scripts/normalize_osis.py original.xml --kind bible \
      --schema /tmp/reviewed-osis/osisCore.2.1.1-cw-latest.xsd \
      --plan reviewed-plan.json \
      --output pilot-work/reader-optimized.osis.xml \
      --diff pilot-work/private-before-after.diff \
      --report reports/normalization.json

The tool refuses overwriting any source/output. It checks original SHA-256,
the evidence/rights plan, each original subtree checksum, and semantic
integrity; performs only the explicitly listed operations; then validates
the **serialized output** against the official, pinned XSD and reviewed OSIS
subset. Commentary also passes the commentary annotation validator.

**Exact character data is compared**, including spaces and original
punctuation. All non-layout semantic elements and their attributes remain
in sequence, including \`verse\`, \`w\`, \`note\`, \`reference\`, \`hi\`,
\`transChange\`, \`q\` and annotated commentary sections. The tool records
original/output SHA-256, text SHA-256, edition, reviewer assertion, reference
keys, operations, diffs and proof hashes. The source file is the rollback;
it must remain available with its checksum. The unified diff contains
copyrightable text: **keep it private** until cleared for publication.

This is NOT sufficient to publish a new SWORD module. The later source-to-
compiled module round-trip, SWORD versification/index review, complete
source notes and reference correspondence, Bible GTK visual inspection,
actual derivative permissions, sign-off and publisher approval are distinct
required gates. No unverified report can authorize distribution.

## Actual first-source observations (2026-11-07)

Read-only GitHub Actions evidence:
[LSG and MHC structure fingerprints](evidence/normalizer-3/real-pilot-source-signals.json).
The exact publisher ZIPs were downloaded into temporary storage and scanned
with key-scoped \`diatheke\` requests. After correcting an initial flag-order
bug, LSG **Psalm 23 already contains poetry markup signals** and full
MHC **Genesis 1 contains paragraph markup signals**. Do not flatten or
rebuild them merely because the Bible UI looks wrong; verify rendering first.

This is **neither** a complete verse/text identity check nor proof that
every paragraph is correct. No automatic source edits, original MHC OSIS
reconstruction, SWORD recompilation or public resource release has occurred.
Evidence from the earlier accidentally unbounded \`diatheke\` queries is
explicitly invalidated; only the corrected bounded-reader run is cited.

The OSIS editor cannot work directly on an opaque compiled SWORD archive:
if the original source cannot be obtained, the future extraction adapter
must reconstruct a clearly *generated* intermediate with SWORD entry keys,
never assert that generated lines are original source lines.

See also [the full quality policy](QUALITY_POLICY.md), [editorial rules](EDITORIAL_RULES.md),
and [pilot issue #12](https://github.com/icfmp/Bible-Resources/issues/12).
