# Strict source normalization contract (OSIS-first)

## Sources of truth

- [CrossWire OSIS Bibles](https://wiki.crosswire.org/OSIS_Bibles): OSIS 2.1.1, poetry/quotations, container versus sID/eID milestones, and the official SWORD import process.
- [CrossWire OSIS/TEI validation](https://wiki.crosswire.org/Validate_OSIS_or_TEI_text): XML must be **well formed** and **valid against its real XSD**.
- [CrossWire module format guidance](https://wiki.crosswire.org/DevTools:Modules): OSIS preferred for Bible/commentary sources; TEI is the preferred format for dictionaries. Legacy ThML/plaintext remains a separate format, never silently labelled OSIS.
- [CrossWire SWORD module configuration](https://wiki.crosswire.org/DevTools:conf_Files): \`SourceType\`, \`ModDrv\`, \`Versification\` and other module properties must describe the actual payload.

**The official XSD is authoritative.** Our allowlist is an additional, deliberately conservative *review policy*, not a modified or invented OSIS schema.

## Non-negotiable behavior

1. Preserve original source bytes separately, with SHA-256 and rights/provenance. Never alter the authoritative original.
2. Validate the original against a **locally available, reviewed and SHA-256-pinned official XSD**; no remote XSD downloads during processing.
3. Check every element against our explicitly reviewed subset. Unknown but valid OSIS elements must stop the job, with exact file/line. We do not drop, flatten, reinterpret, or silently default them.
4. Preserve meaningful structural constructs, including \`lg\` stanza groups, \`l\` lines and \`level\` indentation, \`q\` quotations, \`title\` elements, \`hi\` editorial emphasis, \`divineName\`, \`transChange\`, notes, word attributes, verse references, and overlapping milestone boundaries.
5. No automated removal of quotes of Scripture from commentaries, no invented verse splitting, no converting poetry into prose, no guessed paragraph breaks, no blanket uppercase/lowercase replacement, and no generic formatting resets. These may be *audit findings*, but not automatic transformations.
6. Each future transformation requires a documented mapping of **specific standard source constructs to specific standard target constructs**, with golden examples. If mapping is absent or ambiguous, stop without emitting any transformed module.
7. A future normalizer must stage **all** its output and commit nothing until source, structure, text fidelity, and actual SWORD reading validations succeed. If any file fails, abort the whole module.
8. Do not “fix” an unexpected structure by extending a parser's permissive fallback. Review the original edition and official specification, add one explicit rule and its regression fixture, and rerun.
9. Keep theology, original readings, numbering, canons, versification, publisher attributions, and rights notices intact.
10. A compliant XML source is **not** proof the compiled SWORD module matches it; text and structure round-trip comparison plus a real SWORD smoke test remain separate release requirements.

## Readability improvements backed by another edition

When the exact print edition is unavailable, a verified **different edition of the same work** may legitimately guide a cleaner paragraph, stanza or commentary-section layout. This is a reviewed **reader-optimized editorial adaptation**, not evidence of the original source formatting. Use the matching edition first where possible, but never retain a clearly unreadable or malformed structure merely to avoid consulting a related edition.

Preserve every word, punctuation mark, verse/entry association, note and meaningful authorial structure from the module actually being normalized. Record the reference edition and pages, explain deviations, obtain derivative rights, and add tests for the approved transformation. A proposed reflow still must be accepted before a deterministic script applies it; unknown or ambiguous structures remain blocking. This does not relax the official OSIS XSD or source-integrity gates. See [EDITORIAL_RULES.md](EDITORIAL_RULES.md).

## Current implementation versus future transformation

\`scripts/guard_osis.py\` is the **read-only first gate**. It checks XML parsing, the pinned official XSD, our explicitly approved OSIS element subset, poetry levels, reviewed emphasis types, and correctly paired sID/eID milestones. It produces either:

- \`validated\` + source/schema/policy checksums (no transformed content), or
- \`blocked\` + precise source file, line, optional column, error code and reason.

It **does not** rewrite, rearrange, convert ThML/TEI, remove quotations, repair broken markup, or generate SWORD binaries. In particular, a successful test of the validator is **not** a claim that source normalization is implemented.

Only a reviewed OSIS source with a valid \`SOURCE_VALIDATION.json\` check report may support an **approved** compiled Bible/commentary under current gates. This report records validation provenance, but is not a cryptographic attestation of unpublished original bytes. If rights prevent publishing original sources, maintain them and the actual validation proof in controlled review storage.

TEI dictionaries and other source formats require their *own* schema-pinned, tested adapters before approval. An unreviewed input source type must fail, even if SWORD can open its compiled binary.

## Pinning the official schema

\`config/osis-policy.json\` currently contains the documented CrossWire OSIS 2.1.1 schema URL, but its digest is intentionally \`null\` and \`schema_status\` is not \`reviewed\`. **Until a maintainer retrieves, inspects and pins the real official schema, all real source processing and module approvals are blocked.** The test suite uses a clearly labelled **synthetic** XSD only to test the guard, never to claim real-world OSIS conformance.

To enable the official schema:

1. Obtain \`osisCore.2.1.1-cw-latest.xsd\` from the CrossWire URL recorded in policy through an authorized workflow.
2. Inspect and record its actual SHA-256 in \`config/osis-policy.json\`, change \`schema_status\` to \`reviewed\` after human review, and record its fetch date and upstream revision in the pull request.
3. If that XSD references auxiliary XSDs, pin the **entire** dependency set and extend the validator to support it explicitly; current code refuses unreviewed imports/includes.
4. Do not silently substitute an ad-hoc XML schema, Internet-hosted live schema, or “best effort” validation.

Then run (the XSD is supplied locally, not fetched by the tool):

    python scripts/guard_osis.py path/to/original.osis.xml \
      --schema path/to/reviewed/osisCore.2.1.1-cw-latest.xsd \
      --report path/to/SOURCE_VALIDATION.json

The command returns exit code **0** on success and **1** on a stop condition. A blocked report replaces any prior success report so CI cannot misread a stale result.

## How to handle a new special case

Typical diagnostic:

    sources/psalms.osis.xml:214: [UNREVIEWED_ELEMENT] <someElement> has no reviewed normalization rule

Do not modify the source to make the test pass. Instead:

1. Record the source path, exact line, module ID/version, surrounding XML (subject to copyright), and relevant standard clause.
2. Decide whether the content is **valid but unreviewed**, **invalid according to OSIS**, or **legitimate material in another supported source format**.
3. Agree on an explicit, minimal rule; never silently flatten a standard OSIS structure.
4. Add tests exercising valid structure, unexpected variants, source-to-output fidelity, and exact failure locations. Store only licensed/minimal synthetic examples in the public tests.
5. Extend the approved policy *and* transformation implementation (when it exists), version the rule, record rationale and reviewer, and rerun the entire module validation.

The allowlist in \`config/osis-policy.json\` will grow only this way.

## Compiled SWORD modules without an original XML source

A downloaded \`zText\`, \`zCom\`, or other compiled SWORD module is **not** the original OSIS/TEI source file. There is no reliable original source **line number** inside its binary indexes. Never invent one. The raw module must be accessed through SWORD, not parsed by guessing the private binary layout.

If the publisher's authoring source is available, validate that actual file and report \`file:line[:column]\`. If only a compiled module exists, the discovery/extraction step must identify the **provider, module ID, and SWORD key/verse or entry** where an unexpected structure occurs. If a reviewed intermediate XML export is created, report its generated filename/line *as such*, never as an original-source line. Stop and request a real source or an explicitly reviewed importer before normalizing anything.

This is also why the current source guard is only one prerequisite: a proper SWORD-to-structured-source extraction adapter and a fidelity/round-trip validator still need to be built.

## Publication gate

\`scripts/validate.py\` refuses an approved module if:
- the authoritative schema checksum/review state is missing;
- the SWORD source format has no corresponding approved structural validator;
- the source validation report is missing, blocked, mismatched, or stale.

The actual SWORD payload still needs the standard metadata, legal review, editorial log, layout validation, and reader smoke test. Existing draft modules are unaffected.


## Commentary entry mapping

Commentaries also use the official OSIS XSD, but require a separate check of `<div annotateType="commentary" annotateRef="...">` entries rather than treating them as Bible verses. The policy and its dedicated validator are in [COMMENTARY_POLICY.md](COMMENTARY_POLICY.md). This preserves references, independently authored sections, embedded quotations and intentional formatting, with file-and-line diagnostics for unreviewed annotations. A generic OSIS validation report alone is **not** sufficient to approve a commentary.
