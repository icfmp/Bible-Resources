# Cleaned source editions

This folder is for **maintained, auditable source editions**, independent of the
format used to distribute them. SWORD modules are generated outputs, not the
editorial source of truth.

Each source lives in `sources/cleaned/<resource-id>/`, regardless of its
language or its original provider. Prefer official formats such as OSIS and
USFM. Do not create a proprietary text format.

## Separation of responsibilities

- **Original witness:** always preserve the exact provider/edition identity,
  immutable download location, checksum and size in the resource's provenance
  manifest. The original file can be kept privately or, only if its
  redistribution rights are confirmed, committed separately as an immutable
  reference. Do not assume that a public GitLab repository permits mirroring.
- **Cleaned working source:** contains *our* reviewed, reproducible source
  state. Record its original source checksum, each approved transformation,
  tool version and resulting checksum. A cleaned source must not silently
  acquire new words, lose notes, alter biblical references or redefine a
  section.
- **Compiled distribution:** standard SWORD output is rebuilt from the
  cleaned source and independently checked, never manually edited in place.

## Workflow

1. Independently pin the original and verify the edition/license.
2. Produce a cleaned candidate **in private**. Remove machine/presentation
   artifacts when their lack of textual meaning is demonstrated; classify
   ambiguous asterisks, note callouts and spacing for review instead of
   applying blanket regular expressions.
3. Validate the source structurally, compare its actual text against an
   independently selected reliable edition, and record corrections separately
   from mechanical cleanup.
4. Generate SWORD with standard tools and read back the complete native
   contents. Verify source-to-module coverage, notes, links and divisions.
5. Commit any cleaned textual data here **only after** confirming the source
   edition's modification and public redistribution rights. Publication of
   an actual SWORD module is a separate explicit decision.

No copyrighted source body, private compilation output or inferred CC
license is authorized by this README. All review, cleanup and build tools
must remain usable with French and other languages, not just English.
