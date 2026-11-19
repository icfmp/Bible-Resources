# UBS Hebrew ↔ MACULA WLC v1.0 — technical release readiness

**Status:** v1.0.0 publication authorized by the project owner after source
validation. The [exact approved public ZIP manifest](v1_publication_authorization.json)
pins the reviewed private candidate and deterministic public archive SHA-256.
An independent GitHub Actions publication job releases **only** on protected
`main` once all required source/lexical CI checks pass. This readiness
document is not evidence that a GitHub release has already occurred; verify
the [actual release tag](https://github.com/icfmp/Bible-Resources/releases/tag/bsi-ubs-hebrew-v1.0.0)
and its attached ZIP checksum separately. The historical canonical
`index.json` and Bible application remain unchanged.

## Final independently reviewed v1.0-rc2 (current technical candidate)

The prior **v1.0-rc1 / 273-word / 99.021%** results remain immutable,
source-pinned historical review checkpoints, **not the final candidate**.

The final source-word audit in [#393](https://github.com/icfmp/Bible-Resources/pull/393)
inspected the original MACULA TSV word by word against the original UBS Hebrew
EN/FR 0.9.4 headwords: **25** previously unsupported original tokens in 16
single-candidate families, plus the separately held **2 Sam 21:22** giant/Raphah.
Eight other words in a shared source family were already linked and deliberately
excluded from the 25-word unresolved inventory.

**Exactly two additional identity decisions were accepted:**

1. **Joshua 19:13** original WLC word `o060190130101`, lemma `רִמּוֹן`,
   original Strong `7417a`, UBS headword `רִמּוֹנוֹ` / `006826000000000`.
   BDB specifically cross-identifies this Zebulun Rimmon with Rimmono in
   1 Chronicles 6:77, while the distinct southern Rimmon and Rock of Rimmon
   occurrences are **not** silently linked.
2. **1 Samuel 17:39** original WLC word `o090170390072`, lemma `אלה`,
   original Strong `2974a`, UBS headword `יאל` /
   `002740000000000`. The original Hebrew word `וַיֹּאֶל`,
   source English 'tried' and morphological gloss 'he undertook' are
   independently cited under the same H2974 verb in BDB. The original MACULA
   lemma and source reading are **not rewritten** or conjecturally emended.

The source-specific evidence and exact unmodified source fields are in
[v1_final_word_specific_approvals.json](v1_final_word_specific_approvals.json),
regenerated and independently checked by
[audit_final_lexical_uncertainties.py](audit_final_lexical_uncertainties.py)
and [build_final_reviewed_candidate.py](build_final_reviewed_candidate.py).
**All other 24** individually audited original words remain unlinked, including
the 2 Samuel 21:22 giant/Raphah source word: source ambiguity does not
authorize a generic family-wide link.

**Final private v1 candidate:** original **248,680** selected lexical WLC
occurrences; **240,373** linked; **242,747** UBS edition-specific indexed
headword denominator; **99.022%** of that narrow source-word/headword scope;
**2,374** remain unlinked in scope. Total accepted reviewed original WLC
word-ID-only headword links **275** (273 + 2), inferred contextual senses **0**.
The remaining 2,374 comprise 1,863 independently rejected nonidentities,
458 multiple-headword choices, 27 grammatical fragments, 23 singly plausible
but unsupported word matches, 2 preserved composite-Strong annotations
and 1 Raphah/giant choice. **5,933** more source words are outside the pinned
UBS 0.9.4 indexed-headword inventory; none are dropped from source.

Private final index SHA-256:
`42f2ac19d981e924cff760708adeda71e3f2b183e969e11c27fd6df687badf65`.
Pinned in [v1_final_candidate_manifest.json](v1_final_candidate_manifest.json).
GitHub Actions builds **v1.0-rc2** only as a temporary internal/review artifact,
with exact hash, CC BY-SA 4.0 rights notice and original attribution.
**Public standalone v1.0.0 release is authorized for the exact final verified bytes.** No unrelated canonical-index change, source rewrite, SWORD catalogue publication or Bible application integration is authorized.

## Locked edition and source rights

- UBS Dictionary of Biblical Hebrew **0.9.4 EN/FR**, pinned `a15a96cfaa4ca18a6c0339016645ba1e534db3c8`, CC BY-SA 4.0; original lexical definitions and prose are not in the crosswalk.
- MACULA Hebrew WLC, pinned `47db250bd55d0d8577f2a94fba114ef16c35b23c`, CC BY 4.0; original WLC words, Bible text, source TSV and English gloss sentences are not distributed.
- Adapted index license **CC BY-SA 4.0**, with `ATTRIBUTION.md`, `LICENSE.txt`, source revisions, changes notice and no-endorsement language in its deterministic ZIP.

## Historical v1.0-rc1 technical candidate (superseded)

- Source-original selected lexical WLC occurrences: **248,680**, unchanged.
- Original linked lexical occurrences: **240,098**, baseline `index.json` unchanged.
- Private candidate linked lexical occurrences: **240,371** (**273 extra individually attested source-word headword-only links**, no contextual sense decisions).
- Original UBS indexed-headword scope denominator: **242,747**.
- Private candidate coverage of that *edition-specific headword scope*: **99.021%**, leaving **2,376** unmatched in scope. This is NOT a semantic accuracy rate.
- Independent lexical-family editorial dispositions: **202/202** families accounted for; do not re-link rejected/ambiguous/grammar-only/out-of-edition candidates merely to increase coverage.
- An original WLC word in 2 Samuel 21:22 (`רָפָה`, English “giant”) remains deliberately unlinked against the UBS Raphah personal-name headword.
- Private candidate JSON SHA-256: `7c2e386a07d0dede3bcb836f64db66a5779b7e4c9d8f6d20ec76e06d156c1b35`.

## Independent build, source and API gates

1. The baseline bilingual `build_index.py` run from the exact pinned UBS EN/FR and MACULA source must match the committed original `index.json` exactly.
2. The original 202-family editorial partition and first 139 individually witnessed WLC lexical word IDs must re-verify against those exact originals.
3. The 135 remaining words must be re-enumerated in original MACULA, and the 134 approved word-specific entry-only lexical identities separately re-verified against original UBS glosses; the ambiguous 135th must stay unresolved.
4. `build_private_reviewed_candidate.py` must reject source drift, existing-link collisions, missing source words or UBS headwords, preserve existing direct/Strong/word mappings and re-audit **all 475,911 original WLC word records**.
5. The resulting private JSON must match the frozen candidate SHA-256; all 273 new links must return only exactly one UBS headword and zero inferred contextual senses via `lookup_word`.
6. The candidate ZIP must be byte-for-byte deterministic, carry original index JSON, source credits, license, full manifest with entry SHA-256, no original content, and a separate ZIP SHA-256. Its manifest must say `publication_authorized=false`.
7. The repository Validate, UBS source-pinned crosswalk, independent entity index and script registry consistency workflows must all succeed on the actual merging head.

## Publication authorization and independent release verification

The project owner approved the **standalone, exact source-verified UBS Hebrew lexical v1.0.0** publication after the 2026-11-19 editorial closeout. The owner approval is recorded explicitly in [v1_publication_authorization.json](v1_publication_authorization.json). It authorizes neither changes to the original `index.json` nor implicit consumer/application migration.

The public package contains a **publication metadata-only transformation** of the pinned index, with all original lexical link maps unchanged and independently tested. The public release ZIP SHA-256 is pinned separately: `e448c7e4b6c0cb892789d78b487a3afe3dbe18cfb8c0b13be5fd910deabf640f`. The protected-main job compares the exact archive against this immutable digest, uploads it as a new GitHub Release tag and reads the remote attached bytes back without permitting overwrite. A staging artifact is not a publication; independently check the actual GitHub release URL and issue #366 after the publishing workflow succeeds.

**Known limitation:** Generic `lookup` results based on identical Strong-family corroboration do not independently establish that every contextual SDBH/UBS sense corresponds. Marketing 99.021% as semantic accuracy or 100% lexical completeness would be misleading.
