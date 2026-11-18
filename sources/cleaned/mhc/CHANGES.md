# MHC — maintained OSIS change log

This is a **private source candidate**. No public edition, redistributed source
XML or released SWORD module has been approved. The exact original is fetched
from CrossWire's source revision, verified by SHA-256, and kept unmodified.

## 2026-11-18 — remove 11 empty superscript styling leaves

**Technical cleanup only. No editorial correction to the commentary's
words, punctuation, notes, biblical references or authorial divisions.**

- Original authoring OSIS source SHA-256:
  `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`
- Private cleaned source SHA-256:
  `ded53fe37e83609790433a01b2dabf0ea3a13e929bd3bded39262ce4a5b24016`
- Rule: remove only `hi` leaf elements with exactly `type="super"`,
  no text and no children; the generic cleaner supports other explicit
  display-only `type` values without changing non-empty markup
- **Original XML lines** (all inside paragraphs): 6451, 6850, 7895,
  12595, 15355, 15363, 15397, 15415, 15519, 111795, 113304
- Implementation: delete precisely the original XML byte spans, avoiding
  reserialization of the rest of the document; make no source-prose rewrite
- Source-wide exact visible Unicode text SHA-256, **unchanged**:
  `defe78fc9c56be07e0eeb577c73c52ac0c21a443342a5a10bd1c28d12e8029ff`
- No changes to XML notes, reference elements or their attributes
- Resulting SWORD: same **31,098 K**, **1,255 I**, **2 TOP** occupied
  native keys
- Full private source-cleaned vs independently recompiled pristine SWORD
  comparison: **73** raw entries differed; each changed solely by removing
  **one redundant space from an existing whitespace sequence**, with zero
  changed nonwhitespace characters, zero changes to notes/links and zero
  changes to non-style XML structures. No two words were joined.
- [Independent full native comparison — PASS](https://github.com/icfmp/Bible-Resources/actions/runs/44270721733)

**Reversibility:** restore the original authoring OSIS bytes at the original
SHA, or run the compiler on that pinned source. This change does not claim
independent validation against a printed MHC edition.

## Separate editorial text-collation stage — not yet executed

Compare the cleaned work against a **printed historical edition**, not merely
the supplier's electronic text. A potentially suitable independent witness is
the [1828 Towar & Hogan six-volume facsimile/index on Wikisource](
https://en.wikisource.org/wiki/An_Exposition_of_the_Old_and_New_Testament_(1828)),
which links scanned originals. Verify volume/page attribution and editorial
variants before treating any difference as an error; do not automatically
replace later edition choices with 1828 wording.

No source-text corrections are recorded or implied here. Digital-edition
redistribution rights still require explicit review before committing the
48 MB cleaned OSIS and publishing a module.
