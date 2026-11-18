# MHC source cleanup — baseline, 2026-11-18

## Source and scope

- Resource: Matthew Henry's **Complete** Commentary (MHC), not MHCC
- Provider file: CrossWire's authored `mhc.osis.xml` (OSIS, English)
- Verified source revision: `537591a94c991941877b47a06666b6a7812e05d8`
- Original 48,020,985-byte SHA-256:
  `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`
- Proof: https://github.com/icfmp/Bible-Resources/actions/runs/44264543712
- Generic source tool: `scripts/clean_source_osis.py` (no edition name,
  book list, English-only word tokenizer or CrossWire-specific rules)

## Actual verified private-run outcome

The runner re-downloaded the pinned authoring OSIS, verified its original Git
revision, size and SHA, parsed it without external entities, created a separate
private cleaning candidate, recompiled standard SWORD `zCom4` from **that
candidate**, and independently enumerated every occupied native record.
These tests and the CLI smoke passed.

- Original literal standalone asterisks: **0**
- Original literal double/triple asterisk sequences: **0**
- Original escaped asterisk sequences: **0**
- Original U+200B zero-width spaces: **0**
- Safe, automatically applicable whitespace edits under the initial strict
  plain-paragraph/plain-title rules: **0**
- Resulting cleaned-candidate SHA-256:
  `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`
  (**identical to the original**; do not claim the prose was cleaned)
- Rebuilt numbered commentary keys: **31,098**
- Rebuilt introduction keys: **1,255**
- Rebuilt anonymous TOP keys: **2**

### Follow-up source typography census

The later metadata-only profile was verified in
[private run #44266026639](https://github.com/icfmp/Bible-Resources/actions/runs/44266026639).
It confirmed the same **zero edits**, the same original candidate SHA and the
same native key counts. It also identified:

- **122** nonbreaking spaces: 85 in direct `hi` text ownership, 23 in
  `reference`, and 14 in `l` poetry lines; changing them without examining
  their contextual purpose could affect citation or line layout
- `hi` emphasis types: **160,448 italic**, **29,218 superscript**,
  **9,326 small caps**, **1,113 bold**, and **1 underline**
- Most `hi` ranges are short (175,877 with 1–40 visible characters);
  **8** exceed 500 characters and warrant targeted inspection, not blanket
  deletion of emphasis

These are genuine source-structure observations. They do **not** establish
which emphasis is authorial, which is editorial, or which is harmless layout
noise. None was automatically removed; a full textual comparison is still
pending.

This is a completed **mechanical baseline**, not evidence that the entire OSIS
is editorially pristine. In particular, source markup, heading placement,
reference-link correctness, repeated source scopes, meaningful punctuation,
formatting inside non-leaf paragraphs and real reader rendering still need
source-specific review. No source words, quotations, note markers or references
were removed.

## Next review, kept separate

1. Investigate *actual* source-structure anomalies using source-defined
   scope/markup evidence, including duplicate headings, presentation-only
   formatting, erroneous reference links and meaningful asterisk callouts if
   discovered. A proposed correction must name an original anchor, rule,
   before/after hashes and source proof. No blanket regex on paragraphs.
2. Compare the cleaned text against an **independent**, authenticated historic
   edition. Record text repairs separately from structural cleanup and make
   them reversible.
3. Repeat complete source-to-compiled text, references, notes, divisions and
   reader proof, not just native key counts, before accepting a final SWORD.

## Public source/redistribution rights remain a gate

CrossWire [advertises the MHC module 2.2 as Public Domain](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHC),
but credits CCEL and Logos for the electronic text. The
[CCEL copyright policy](https://www.ccel.org/about/copyright.html) explicitly
asks people to contact them about republishing CCEL editions. Whether the
specific authored OSIS may be mirrored, modified and publicly distributed
is not yet independently cleared. No 48 MB original, cleaned prose, compiled
payload, or edited transcript has been committed here or uploaded as an
Action artifact. Keep the edited candidate private until this is resolved.
