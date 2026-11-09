# Louis Segond 1910 — standard Xiphos reader acceptance test

Status: **prepared, not executed or editorially approved**.

A successful SWORD compiler and diatheke readback is not equivalent to a
successful visual Xiphos test. This plan covers a *private* package produced
after the source, rights and fidelity gates have passed. No real module ZIP
has been published or uploaded by the current CI.

## Prerequisites and safety

- Use a released, stable Xiphos build and the normal system SWORD engine.
- Test in a **separate SWORD_PATH installation root**, without copying
  files into /usr/share/sword or overwriting ~/.sword.
- The source eBible module ID 'fraLSG1910eb' may already be installed.
  The privately staged module must not overwrite any existing module.
- Only test a ZIP whose SHA-256 is recorded in the verified candidate
  report; do not use this document as proof that a ZIP currently exists.
- Keep the publisher original USFM/USFX archives and exact hashes immutable.

An approved private ZIP will contain mods.d/ and modules/ as its two top
level directories. The internal build self-test confirms extracted bytes
and independent diatheke output before any manual Xiphos session.

## Reader acceptance matrix

| Passage | What to inspect | Required result |
| --- | --- | --- |
| Genesis 1:1 | Normal verse text and chapter navigation | No markup or empty display, punctuation preserved |
| Psalm 23:1-6 | Poetry and superscription/title | Source-based line grouping visible, no displaced poetry |
| Mark 10:50-52 | End of chapter with source Mark 10:53 | Reader slot 52 contains both entire verse bodies in order; editorial 52–53 notice is discoverable; no invented verse 53 key or text |
| Job 34:35-37 | Source has no authored Job 34:37 | Reader slot 37 must be empty/not pretend to contain new verse content |
| Acts 8:1 | Two notes affected by interverse word storage | Callouts and note text attached to correct words |
| John 12:47-48 | Multiple note callouts | Correct, distinguishable notes and Unicode punctuation |
| Matthew 12:15 | Note near interverse markup | Callout located at the correct source word |
| Revelation (poetic/paragraph sample) | Titles, quotations, paragraph closure | No unexpected paragraph continuation or suppressed ending |
| Note-heavy chapter (e.g. Luke or Matthew) | Spaces and note-body formatting | Explicit review of converter/newline normalization; do not infer exact fidelity from word equality |

## Reproduction evidence

Record the precise test package ZIP SHA-256, the original publisher source
archive digests, OS and Xiphos/libSWORD versions, a list of inspected passage
references, and any visual discrepancies. Note whether the displayed verse
number shows '52' or '52–53' instead of assuming noncanonical labels work.

Do not accidentally install a module under the same ID as an existing
personal SWORD translation. For native Xiphos packages that honor SWORD_PATH,
an isolated test root can be passed through the application environment;
other packaging formats may require their own isolated access permissions.

## Mandatory release decision

A successful engine test validates installed package and rendering mechanics,
not manuscript provenance, lexical-annotation redistribution rights, or the
print-edition issue. The publisher note-whitespace reviews, one approved
Mark merge, source document identity and final human editorial approval
must be recorded before publication or addition to the public catalogue.
