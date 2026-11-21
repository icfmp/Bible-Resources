# OSIS paragraph and poetry rendering — general QA

**Purpose:** preserve the source's genuine typographical and structural distinctions through OSIS, SWORD and independent reading applications.

## Diagnose before changing

For a rebuilt edition, compare the exact original, cleaned OSIS/USFM, compiled native SWORD output and reader rendering. For byte-identical upstream stock where no source master exists, inspect the original compiled markup and any independently available edition witnesses; **do not invent cleaned OSIS**. Record all source structures: paragraphs, paragraph spacing, poetic lines, indentation, headings, quotations, notes, milestones, verse labels and literal punctuation. A visual mismatch alone cannot establish a source defect.

Do not globally strip leading whitespace, asterisks or unusual punctuation. Determine whether each character is authorial text, an editorial layout convention, an input-format artifact, or a renderer effect. Asterisks may encode legitimate translator annotations, not decorative noise.

## Review sequence

1. Pin the exact original and cleaned master hashes.
2. Inventory each distinct paragraph/poetry construct and the reference keys in which it appears.
3. Evaluate a **source-attested** structural OSIS encoding, preserving authorial content and important layout meaning.
4. Produce a full source-versus-cleaned structural and textual difference report. Every exception requires a reversible rule and cited editorial approval.
5. Compile a candidate with documented toolchain options, then run native readback over the corpus.
6. Verify representative high-risk cases in at least one independent SWORD reader. Document text/structure vs reader-only differences.
7. Attach the evidence and decisions to the edition's `editorial/` folder and only approve when the broader [production contract](../PRODUCTION_PIPELINE.md) is met.

## Reject these shortcuts

- Do not transform every whitespace cluster into a paragraph or every asterisk into a heading.
- Do not conflate SWORD's native markup with a reader's CSS/layout behavior.
- Do not silently change published source wording, annotated labels, verse mapping or note destinations.
- Do not generalize a single publisher's formatting conventions into global cleanup behavior.

The source-specific case study from which this QA grew has been preserved in [the Darby import retrospective](../../sources/cleaned/bibles/fr/darby-jnd-2024/editorial/history/DARBY_2024_IMPORT_POSTMORTEM.md). It is **evidence**, not the general rule.
