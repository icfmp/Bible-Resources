# UBS Hebrew ↔ MACULA WLC v1.0 — technical release readiness

**Status:** release candidate assembled in GitHub Actions; NOT published or approved as v1.0.

## Locked edition and source rights

- UBS Dictionary of Biblical Hebrew **0.9.4 EN/FR**, pinned `a15a96cfaa4ca18a6c0339016645ba1e534db3c8`, CC BY-SA 4.0; original lexical definitions and prose are not in the crosswalk.
- MACULA Hebrew WLC, pinned `47db250bd55d0d8577f2a94fba114ef16c35b23c`, CC BY 4.0; original WLC words, Bible text, source TSV and English gloss sentences are not distributed.
- Adapted index license **CC BY-SA 4.0**, with `ATTRIBUTION.md`, `LICENSE.txt`, source revisions, changes notice and no-endorsement language in its deterministic ZIP.

## Frozen technical candidate

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

## Remaining nontechnical release gate

Before creating a public GitHub release, moving the canonical index, or adding the module to the application catalogue, the project owner must explicitly validate the **editorial release scope, source rights and v1.0 publication**. The original index stays available and there is no implicit consumer migration.

Once approved, publish only the exact previously source-verified ZIP bytes (or independently rebuild and verify their digest), plus the companion `.sha256`. Preserve the immutable pinned sources, the audit and the candidate SHA. Publishing a release is not the same as merging the code or staging an Actions artifact. Track the release decision in [issue #366](https://github.com/icfmp/Bible-Resources/issues/366).

**Known limitation:** Generic `lookup` results based on identical Strong-family corroboration do not independently establish that every contextual SDBH/UBS sense corresponds. Marketing 99.021% as semantic accuracy or 100% lexical completeness would be misleading.
