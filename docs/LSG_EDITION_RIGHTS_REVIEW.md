# Louis Segond 1910 — edition and rights checkpoint

Status: **unreviewed, no module publication authorized**.
Resource: eBible 'fraLSG' (Louis Segond 1910), custom stock-SWORD
candidate assembled from immutable publisher source in PR #24.

## Official source and reproducibility

- Publisher catalogue: https://ebible.org/details.php?id=fraLSG
- Publisher copyright notice: https://ebible.org/fraLSG/copyright.htm
- eBible explicitly calls the **Bible edition** "Public Domain" and
  supplies source USFM, USFX and SWORD downloads.
- Original USFM ZIP SHA-256:
  64c4fe2a84d92f958deb0d1add4247d126a21c8a51e5b3058338f661a42d4900
- Original USFX ZIP SHA-256:
  fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e
- Extracted USFX SHA-256:
  90a53c3a61f0c07a329d8fc19c593b8c353f2b3e5a6830dbf4c53d2b08fd2141

These statements support the public-domain **translation**. A publisher's
general label must not automatically be treated as separate proof of rights
or attribution for every later editorial and lexical enrichment.

## Items requiring a separate redistribution decision

| Component | Existing evidence | Release status |
| --- | --- | --- |
| Original Louis Segond 1910 text | eBible Public Domain statement | Edition declaration recorded |
| Original note/heading/cross-reference data | Supplied with pinned eBible USFM/USFX | Confirm whether the source statement covers all ancillary material |
| Word-to-Strong alignments | 705,728 ordered lexical attributes verified against source in compiled SWORD | Identify origin and rights of the alignment separately; **not cleared yet** |
| Machine-readable reference links | No source-authored OSIS osisRef targets; 2,493 SWORD-generated refList suggestions | Do not misrepresent derived suggestions as editorially verified links |
| Printed versus digitized edition | Mark 10:53 and Job 34:37 discrepancies documented in UPSTREAM_LIMITATIONS.md | Print witness review remains pending |

The special, **owner-approved only** SWORD index compromise is combining
the unchanged original source Mark 10:52 and 10:53 bodies into the stock
Segond reader slot Mark 10:52. Its source-bound manifest is
config/lsg-reviewed-verse-merges.json. No other verse merges or synthetic
verse bodies are permitted. Source Job 34:37 remains absent; never invent it.

## Text and layout fidelity gates

Existing stock-SWORD CI verifies the book-wide relative word positions of
all 9,751 notes and all structural opening/closing markers, note types and
callers, lexical attribute order, and source-authored reference markup.

**Do not equate normalized text equality with typographic identity.**
The source USFX-to-OSIS note audit reports raw note component spacing and
pre-note separator changes. The existing source-bound separator-restoration
tool is a dry run only.

The real stable-SWORD whitespace classification in GitHub Actions
[run 42600072255](https://github.com/icfmp/Bible-Resources/actions/runs/42600072255)
found **681/9,751** OSIS-to-compiled notes with a consistent pattern:
**2,043 shortened whitespace segments**, comprising **1,362 boundary
segments** and **681 internal segments**. Every changed segment contained
a newline in the generated OSIS but none in the compiled note. No altered
Unicode spaces, tabs, words or punctuation were detected, and all the
2,043 segments became shorter rather than longer. **9,070 note texts were
raw-identical at this stage**. This evidence alone does not establish that
all line breaks were merely converter formatting; the source USFX-to-binary
comparison must establish the publisher's intended layout separately.

The new publisher-USFX-to-compiled-SWORD audit runs before package testing:
its direct note-body equality and original whitespace results are a
separate check, **not yet an editorial waiver**. Neither stage rewrites
the original source or implicitly approves spacing changes.

## Before publishing an installable SWORD module

1. Review both source USFX-to-OSIS and OSIS-to-compiled note whitespace
   differences; record explicit editorial decisions and retain the original.
2. Resolve the rights and source attribution of lexical alignments and other
   additions, or explicitly exclude unlicensed material after an approved,
   reversible transformation.
3. Check a reliable 1910 printed witness for the Job 34:37 ambiguity
   without retroactively altering the publisher source.
4. Reconcile the generic stock-SWORD gate in PR #23 with exactly one
   approved, documented adjacent-verse reader-key merge.
5. Create a reproducible ZIP with the standard mods.d/ and modules/
   structure in isolated storage, validate file hashes, and exercise an
   actual stock reader and Xiphos without installing over user resources.
6. Obtain final human editorial and rights approval before releasing any
   binary or adding an entry to the public resource catalogue.

A passing CI check is implementation/test evidence, **not a declaration of
rights clearance, editorial approval or actual publication**.
