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

## Byte-local cleaned candidate — technical native comparison PASSED

**Private technical cleanup validated on 2026-11-18:**

- Source SHA-256: `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`
- Action: remove exactly **11 empty superscript `hi` leaves**, preserving
  every unedited original source byte; notes, references and all text remain
  intact. Their actual original XML line numbers are listed in
  [CHANGES.md](CHANGES.md).
- Cleaned source SHA-256:
  `ded53fe37e83609790433a01b2dabf0ea3a13e929bd3bded39262ce4a5b24016`
- Exact source-wide visible Unicode text digest before and after:
  `defe78fc9c56be07e0eeb577c73c52ac0c21a443342a5a10bd1c28d12e8029ff`
- Cleaned SWORD native readback: **31,098 K**, **1,255 I**, **2 TOP**.
- Complete native comparison with a separately compiled **pristine original**
  revealed **73** affected native keys. At each key, the compiler no longer
  inserts **one redundant space into an existing whitespace run**.
  **0** changes to nonwhitespace Unicode, **0** word-separator losses,
  **0** note/reference changes, and **0** non-`hi` XML structure changes.
- [Real source + independently compiled dual-native proof — PASS](
  https://github.com/icfmp/Bible-Resources/actions/runs/44270721733)

**Technical scope accepted for private research.** This is not historical
text collation, a verified new scholarly edition, Xiphos/AndBible GUI approval,
a rights clearance, or publication of a cleaned OSIS/SWORD artifact.

## Source link triage — 25 non-canonical machine-reference forms

**Verified private source examination:**
[GitHub Actions #44272465420](https://github.com/icfmp/Bible-Resources/actions/runs/44272465420),
on the same pinned source and cleaned private candidate. Full native SWORD
comparison and repository validation also passed on this revision.

The generic `audit_osis.py` reports **25 syntactically unreviewed
`reference/@osisRef` values**. Their actual machine-reference strings
and enclosing source book were examined individually without exporting
commentary prose.

- **6** contain only chapter/verse numbers, missing the Bible book code:
  observed in source books Genesis (line 3108), Exodus (7237), Job (32130),
  Psalms (37835, 41584) and Proverbs (47698). A missing book code must
  **not** be inferred blindly from the containing commentary book:
  `18.24` at Job line 32130, for example, cannot be identified
  as Job 18:24 because that verse does not exist.
- **19** are multi-passage shorthand strings mixing book names,
  abbreviated chapters, verses and numeric ranges. They include
  source book aliases such as `Pr`, `2Ki`, `La`, `1Ti` and
  `2Pe`. These are source machine-address strings, not 19
  proven corrupt verses.
- No confirmed missing `osisRef` attribute or duplicate annotated
  commentary scope was reported by this diagnostic. The upstream
  source's visible prose has not been edited.

**Technical action:** do not automatically prepend the enclosing book
to a numeric target and do not convert composite strings by splitting on
spaces. A correction proposal must establish the intended Bible book and
range from the displayed original reference, compare against an independent
witness where possible, and verify each proposed endpoint against the
declared KJV versification. Keep the original source `osisRef`, exact
line, SHA-256 and proposed normalized target in a reversible private plan.
Only then compile and test each corrected link in a real SWORD reader.

This makes reference repair a distinct reviewed step from the already
proven no-word-loss mechanical OSIS cleanup.

## Exhaustive OSIS milestone-to-SWORD integrity audit — 2026-11-18

**Status: FAIL-CLOSED, not structurally approved.** The real MHC uses
`verse/@osisID`, `verse/@sID` and `verse/@eID` milestones, **not**
commentary `div/@annotateRef`. A first investigation of `annotateRef` therefore
found no applicable sections; it was **not** evidence of structural validity.
The audit was corrected to parse the actual source structure.

[Actual full-source/full-native diagnostic — deliberately failed on real
mismatches](https://github.com/icfmp/Bible-Resources/actions/runs/44276073483).

| Full corpus check | Result |
| --- | --- |
| Source verse-group opening/closing pairs | **4,256 / 4,256**; no unmatched milestone reported |
| Source chapter opening/closing pairs | **1,189 / 1,189**; no unmatched milestone reported |
| Source book divisions | **66** |
| Source book/chapter introduction IDs vs native I keys | **1,255 / 1,255, identical** |
| OSIS verse groups linked to multiple verses | **3,701** |
| Groups whose compiled linked bodies were compared | **3,698**; no mismatched group-body hash reported |
| Verse range `sID`, `osisID`, `n` consistency | **No malformed/comma notation detected in actual verse-group labels** |
| Source distinct assigned verse IDs | **31,115** |
| Actual compiled occupied native verse keys | **31,098** |
| Source IDs absent from SWORD | **17** |
| Groups with duplicate verse ownership | **7** (not yet established to be invalid authorial content) |

The **17** OSIS-identified but non-indexed verses are
`Acts.26.33`–`Acts.26.44` (12), `Isa.7.26`–`Isa.7.28` (3), and
`Prov.31.32`–`Prov.31.33` (2). These are out-of-range in the declared
KJV versification. Three prior **research-only** proposed endpoint repairs
already exist: `config/commentary-reference-plans/mhc-acts26-endpoint.json`,
`mhc-isaiah7-endpoint.json` and `mhc-proverbs31-endpoint.json`.
Those plans originate from the separately pinned CCEL ThML witness; the
present source is the CrossWire authoring OSIS. Cross-edition corrections
require confirming the actual OSIS `sID`, `eID`, `osisID` and `n` identities
before applying any byte-local repair. **No invalid verse has been invented
or deleted from a Bible; these are commentary *addressing* errors.**

The **7 duplicated ownership groups** require separate source-section/text
ownership examination before deciding whether two independent authored
comments must be combined, separately indexed, or represented differently.
Observed review anchors: `2Chr.1`, `Ps.95`, `Rom.4`, `Rom.7`,
`2Thess.2`, `2Pet.2` and `Rev.4`. Merely having the correct number
of compiled keys cannot prove that both original source passages survived.

**Next validation gate:** verify the three exact source ranges, propose
reversible attribute-only harmonization with original and candidate SHA
proof; then reconcile duplicated groups against the original authorial
text and actual native body selection. Rebuild and demand zero unexpected
index/ownership differences. Keep the 25 separate inline cross-reference
syntax cases on their own track.

## Private six-overlap reindex experiment — all source prose recoverable

**Private experiment executed 2026-11-18**, following the byte-local
endpoint-only three-range correction. No commentary words or notes were
edited, and nothing was exported or published.

- [Before/after full source-to-native report](https://github.com/icfmp/Bible-Resources/actions/runs/44280366837)
- First private endpoint-corrected source SHA-256:
  `dbf5aedadf7ef4f2f02ddedf8cc22de1ecc51b0b8ee2ece7c29acaf540a8d93c`
- Experimental reindexed source SHA-256:
  `95a12ad88decbfe975de747825492abb7944b8de6dd30176cc23afdc9d2daa5d`
- Plan: `config/commentary-osis-repair-plans/mhc-overlap-reindex-private-experiment.json`
- Exactly **six** original first-group range ends were shortened by **one**
  shared boundary verse; **24** original XML machine-attribute values
  changed (`sID`, `osisID`, `n`, paired `eID`). This is a private
  **navigation experiment**, not a conclusion about the original author's
  preferred section divisions. All source prose, notes, links and other
  markup remained identical by exact-byte guarded patching.
- With the original unmodified overlapping ranges, source word streams of
  **6/14** involved original authored groups could not be found in any
  of their native SWORD keys; no continuous 40-word source block was found
  for those six. This is strong evidence of an import/navigation loss.
- In the experimental nonoverlapping compilation, **all 14** original
  authored groups' *complete* word sequences were found in at least one
  of their related native verse entries; all 70 independently sampled
  24-word source shingles were also present. Of the 14, 8 were present
  at every originally claimed key and 6 at some original keys, as
  expected because their shared boundary addresses were reassigned.
- No original authorial group words were deleted, but **a formerly shared
  verse now maps to the later group rather than both groups**. This
  is a material navigation choice that needs editorial acceptance and
  explicit consideration of how Bible should display two distinct
  commentary sections both applicable to the same verse.
- The **only remaining machine-overlap case** is 2 Chronicles 1.1 versus
  1.1–12. Both source text streams were found intact in the compiled
  SWORD at every original claimed key; do not shorten or discard either.
- All 17 previously out-of-KJV source addressing IDs remain resolved in
  the private trial. The corrected full SWORD K/I/TOP index populations
  remain unchanged: 31,098 / 1,255 / 2.

**Gate remains blocking:** the real structural check intentionally fails
until all overlapping source claims have a reviewed, reproducible
representation. The experimental trim is not the final published choice:
the editor may instead select a transport retaining **both** original
commentaries at the shared verse. An authorial and independent historic
edition comparison, link/notes parity, actual Xiphos/AndBible GUI review,
digital-edition reuse rights and explicit publication approval remain open.

## Private reference harmonization and overlap rescue — 2026-11-18

The staged, **reversible and unpublished** source technical preview reuses
`scripts/repair_commentary_osis_milestones.py` with two independent
SHA-pinned plans:

1. `config/commentary-osis-repair-plans/mhc-endpoints-private-preview.json`
   updates **only 12 existing OSIS verse milestone attribute values**,
   repairing the three out-of-canon range endpoints and eliminating all **17**
   impossible source assignments. The rebuilt K/I/TOP index remains
   **31,098 / 1,255 / 2**.
2. `config/commentary-osis-repair-plans/mhc-overlap-reindex-private-experiment.json`
   makes **24 attribute-value updates** in six earlier groups whose ending
   verse was also the first verse of the next group. This is a
   **research-only addressing experiment**, not a settled editorial judgment
   about which authorial paragraph should cover the shared verse.

[Private recompiled two-stage experiment and native readback](
https://github.com/icfmp/Bible-Resources/actions/runs/44280366837)
proved the technical possibility with complete first/second group witness
checks (the workflow's final check deliberately failed only because it
still tested the *known flawed original* rather than the corrected preview):

- Six previously unindexable source prose bodies are now present, each at
  one or more intended passage locations; **zero** of the 14 original groups
  has a completely missing word stream.
- Of 70 independently selected 24-word source snippets, **70/70** occur in
  the rebuilt SWORD, covering all 14 authored source group bodies.
- The original 7 shared verse ownerships become **1**; the remaining
  `2Chr.1.1` source duplication already has both independent authored
  bodies findable in native SWORD. Do not falsely "correct" this without
  checking printed-section semantics.
- The private candidate's complete OSIS exact SHA is
  `95a12ad88decbfe975de747825492abb7944b8de6dd30176cc23afdc9d2daa5d`.
- **Neither the authorial wording nor notes, cross-reference targets,
  inline markup, titles or other original source bytes were changed.**
  All old and new machine attributes remain replayable from the two plans.

**Limits:** the overlap candidate's shared-verse display choice has not been
independently editorially approved; word-presence is not equivalent to
byte-identical native note/markup parity. Historical comparison, cross-reference
normalization, reader acceptance and digital-edition redistribution rights
remain separate gates. This is *not* a release claim.

## Complete authored-group word integrity — PASS in private, 2026-11-18

The reusable `source_commentary_overlap_witness(...,groups_out=...)` and
`compare_all_commentary_source_group_words` auditors now re-read **every
authored source verse group** against an independently compiled SWORD
native raw frame at its first assigned key. Repeated source text is **not**
mistaken for separate commentary sections; the counts are based on actual
source opening/closing milestones.

**Verified [private full reconstruction and complete group audit](
https://github.com/icfmp/Bible-Resources/actions/runs/44282290155):**

| Audit invariant | Verified result |
| --- | ---: |
| Original commentary source groups | 4,256 |
| Source group word tokens examined | 7,073,234 |
| Groups with their entire normalized word stream present contiguously in SWORD | **4,256 / 4,256** |
| Groups with missing 40-token text blocks | **0** |
| First-key original source group presence | **Every group verified** |
| Out-of-range original verse IDs repaired in private technical candidate | 17 |
| Authored overlap bodies restored in private technical candidate | 6 |
| Remaining boundary overlap with both prose bodies present | 1 (`2Chr.1.1`) |

This directly prevents the MHC/MHCC failure class where a module has an
apparently healthy verse index but the actual authorial text is not
recoverable at its passage. The comparison uses actual private SWORD raw
bodies, not a self-reported converter inventory.

**Scope limits:** normalized word-stream equivalence does not certify exact
punctuation, whitespace, each note caller, footnote markup, heading/poetry
topology, reference-link correctness, display in Xiphos/AndBible, or
equivalence to a historically authenticated printed edition. These remain
separate checks before editorial acceptance. The SWORD file and reconstructed
OSIS were not uploaded or released; the original OSIS remains untouched.

## Complete source↔native punctuation, genuine introductions and links — 2026-11-18

**Source-aware full-corpus audit:** [private SWORD reconstruction #44286709497](
https://github.com/icfmp/Bible-Resources/actions/runs/44286709497) passed.
The source-derived classification follows CrossWire's documented
[OSIS2MOD introduction/pre-verse boundary semantics](
https://wiki.crosswire.org/Osis2mod): after a chapter starts, a section
`div` or non-introductory `title` can correctly assign following prose to
the first verse, not the chapter-zero introduction. An earlier naive
pre-first-verse census had falsely attributed 85 pre-verse passages and
their notes/references to chapter introductions. This **was an audit
classification defect, not demonstrable SWORD data loss**; the canonical
scanner has been corrected, tested and re-run on the pinned complete OSIS.

| Verified scope | Result |
| --- | ---: |
| Original authored verse-group prose | 4,256 / 4,256 full word streams |
| Source group Unicode text with exact punctuation after NFC/whitespace normalization | 4,250 / 4,256 |
| Remaining groups requiring punctuation/edge review | 6 |
| Source-authored reference nodes within verse groups, including label/target metadata | 61,421 / 61,421, all present at their first native keys |
| Genuine source book/chapter introductions (including empty) | 1,255 / 1,255 |
| Genuine introduction text with identical normalized Unicode | 1,111 / 1,111 nonempty |
| Source intro keys with no visible text | 144 |
| Source-authored reference nodes within genuine introductions | 6,710 / 6,710, full body/metadata match |
| Source-authored notes within genuine introductions | 0, so no missing source intro note to repair |

The six exceptional verse-group spans are `Deut.34.9-12`,
`Esth.10.1-3`, `Song.8.13-14`, `Mal.4.4-6`,
`John.21.20-25`, and `Rev.22.20-21`. Their original
word streams are complete; every **inter-word** punctuation gap was
checked by aligned token positions and **no changed nonwhitespace
punctuation character was found between words**. Two cases are
whitespace-only at the boundaries; four require investigation of
extra/differing nonwhite symbols **after the final word**. No
source punctuation has been edited or silently dropped.

**Reference navigation remains a distinct open technical issue:** 25
source `reference/@osisRef` values use unsupported abbreviated or
bookless machine addressing. All 25 original targets are conserved in
the compiled module, but retained bytes do **not** guarantee usable
click navigation. A short visible original reference label even
disagrees with a machine target in an Ezra 8 citation; repair requires
checking the original displayed citation and canonical verse limits,
then a reversible machine-attribute-only plan. Keep original English
commentary, note text and displayed reference labels unchanged.

This is NOT printed-edition collation, note/caller rendering acceptance,
editorial authorization for a changed reference scope, or redistribution
rights clearance. The complete original/edited OSIS and compiled zCom4
remain on isolated private runners only.

## Book-end suffix attribution and two explicit cross-link contradictions — 2026-11-18

[Complete private source/native book-end trial](https://github.com/icfmp/Bible-Resources/actions/runs/44290514885)
checked the **66 authored final verse groups** against their compiled first-key
native entry, using original source text *after each final `verse/@eID`*.
The results are:

- **60**: compiled final visible text ends at the same authorial word/punctuation
  boundary as the original final verse group.
- **6**: the native suffix equals the final group punctuation **plus original
  authored post-verse book-closing material**, allowing for whitespace.
  Exact source-word and symbol ordering remains intact.
- **0**: newly invented final-book wording or unexplained suffix differences.

The six are `Deut.34.9-12`, `Esth.10.1-3`,
`Song.8.13-14`, `Mal.4.4-6`, `John.21.20-25`,
and `Rev.22.20-21`. No textual repair is appropriate: the question is
whether the reader should show closing material attached to a final verse or
in a separate section. Test with actual Xiphos/AndBible before deciding.

The **25 nonstandard original `reference/@osisRef` machine links** were
independently matched to their original short *visible biblical citation*
labels in [private source review #44290514885](
https://github.com/icfmp/Bible-Resources/actions/runs/44290514885).
Two source-internal contradictions are immediately evident:

| Original XML line | Machine value (not a valid canonical destination) | Original visible citation | Technical review candidate |
| --- | --- | --- | --- |
| 7,237 (source book Exodus) | `15.1` | `Jer. xv. 1` | `Jer.15.1` |
| 57,059 (source book Isaiah) | `Ezr 1.7 8.23` | `Ezra i. 7; viii. 24` | `Ezra.1.7 Ezra.8.24` |

These are **proposed machine-only corrections**, not claims that an
independent historical edition has validated the printed citation. Confirm
against an independent reliable witness and actual KJV/SWORD endpoint
addressability before patching. Preserve both original values, XML line,
source SHA and visible label digest in a reversible plan; never alter the
displayed author's label merely to match the faulty target.

The remaining nonstandard references (bookless numeric locators and
compound citation lists with inherited chapters) must be resolved using
their **actual displayed text**, not by assuming the current commentary
book or blindly splitting on whitespace. In particular, original Job
`18.24` is not the canonical `Job.18.24` (which does not exist).

## Next review, kept separate

1. Investigate *actual* source-structure anomalies using source-defined
   scope/markup evidence, including duplicate headings, presentation-only
   formatting, erroneous reference links and meaningful asterisk callouts if
   discovered. A proposed correction must name an original anchor, rule,
   before/after hashes and source proof. No blanket regex on paragraphs.
2. Compare the cleaned text against an **independent**, authenticated historic
   edition. Record text repairs separately from structural cleanup and make
   them reversible.
3. Extend the now-verified complete **group word** comparison to exact
   punctuation, notes/callers, references, ordered divisions and graphical
   reader proof before accepting a final SWORD.

## Public source/redistribution rights remain a gate

CrossWire [advertises the MHC module 2.2 as Public Domain](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHC),
but credits CCEL and Logos for the electronic text. The
[CCEL copyright policy](https://www.ccel.org/about/copyright.html) explicitly
asks people to contact them about republishing CCEL editions. Whether the
specific authored OSIS may be mirrored, modified and publicly distributed
is not yet independently cleared. No 48 MB original, cleaned prose, compiled
payload, or edited transcript has been committed here or uploaded as an
Action artifact. Keep the edited candidate private until this is resolved.
