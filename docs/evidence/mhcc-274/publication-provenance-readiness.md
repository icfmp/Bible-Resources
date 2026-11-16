# BRMHCC 0.1.1 — publication provenance, metadata and rights readiness (review only)

**Date checked:** 2026-11-15. **Status:** `PRIVATE_VERIFIED_CANDIDATE_NOT_PUBLICATION_APPROVED`. Source/metadata analysis is preparatory, not an approval to edit `main`, distribute a ZIP, modify the public catalogue or overwrite BRMHCC 0.1.0. See [publication gate #276](https://github.com/icfmp/Bible-Resources/issues/276), [draft PR #275](https://github.com/icfmp/Bible-Resources/pull/275), [editorial source erratum #277](https://github.com/icfmp/Bible-Resources/issues/277).

**Updated 2026-11-16.** Current private full-authenticated rebuilt source candidate includes **24 reviewed navigation keys and two source corrections**: Ezekiel 3 (11 original linked K) and one original `1Chr.7.1` prose spelling error `Dn` → `Dan` (1 K). [Actual complete source/native/Xiphos 4/4 CI](https://github.com/icfmp/Bible-Resources/actions/runs/43851252431) **PASS**, private ZIP SHA-256 `aeebadbc57d5a891d10ddb3dec520dcc8abd49e7cdd733c4a3542c77765282c4` (**not** the eventual publicly attributed/date-adjusted package). Neither original stock nor catalogue/public 0.1.0 changed; approval remains pending. The Ezekiel-only private hash `2022c52a8fed69e25d0efaf00fba0ddda17dd492e8567fd95922f31306c70047` cited in older checkpoints is **superseded as the current candidate but retained as a control**. [Source spelling issue #279](https://github.com/icfmp/Bible-Resources/issues/279).

## Official reference evidence and attribution

| Claim | Evidence | Publication treatment |
| --- | --- | --- |
| CrossWire MHCC 2.0 revision dated **2021-02-14** | [Official CrossWire module record](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC); exactly pinned original SWORD ZIP SHA-256 `5599108faf01753864d51136a87f120d022e70867cc9df70206a0af3c3a5ef7d` | Keep the source revision/date and archive identity explicitly in `metadata.json.origin`, the source manifest and editorial audit. **Do not retain 2021-02-14 as the new BRMHCC 0.1.1 module revision date.** |
| `SwordVersionDate` indicates the date *that the module was changed*, `Version` gives its revision number and `History_X` records changes | [CrossWire official conf-file documentation](https://wiki.crosswire.org/DevTools:conf_Files) | The new **public** `SwordVersionDate` must be set to the **actual authorized release date** when that date is known, not a guessed preparation or upstream source date. No published date chosen in this document. |
| Original CrossWire `About` states the text matches a Moody Press 28th printing | [CrossWire MHCC module record](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC) and pinned original SWORD .conf | This is a **claim inherited from the upstream provider**, not an independently certified 1:1 print comparison. Preserve the entire original `About` unchanged *as an attributed upstream quotation*, preceded by a short clearly labeled Bible Resources edition notice. Do not delete or silently paraphrase original provenance. |
| CrossWire's source SWORD module declares **`DistributionLicense=Public Domain`** | [CrossWire official module record](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC), original shipped `.conf` and [existing BRMHCC 0.1.0 manifest](../../../modules/mhcc-crosswire/metadata.json) | Preserve the original attribution, `DistributionLicense` and source module identification. The narrowly documented Ezekiel 3 numeric correction and 24 nav aliases change no underlying original exposition. **No new CC0 claim is attached to the original CrossWire text.** |
| CCEL digital editions and enriched content are **not automatically freely redistributable** | [CCEL copyright policy](https://www.ccel.org/about/copyright.html) | CCEL's independently pinned ThML was used for **comparison only** (section/evidence validation). **No CCEL source prose, XML, separate reference annotations or digital markup is imported** into BRMHCC; do not broaden scope to those digital additions without a distinct rights review/permission. The valid original CrossWire/CCEL citation overlap establishes a correction candidate, not a license to copy CCEL markup. |

## Verified private corrected source edition

The exactly pinned CrossWire original is the starting source. The reviewed source-change plan authorizes a narrowly scoped **private source-reference correction** from `Ezek.3.12-2` to `Ezek.3.12-21` in a displayed section-summary link and its existing `reference/@osisRef`. It is reversible to the original exact raw bytes; precisely **11 linked original K entries** carry that one original body.

The independent standard full rebuilt SWORD edition additionally links **24** formerly inaccessible K verse positions to the previously authored sections; total **28,742 K**, **1,255 I**, **2 TOP**. The source-corrected private compiled edition has been compared against the separately reconstructed *index-only original-source* baseline at **every** native key, every existing native adjacent linked section boundary and three real Xiphos selected passages. [Full CI #43738365208](https://github.com/icfmp/Bible-Resources/actions/runs/43738365208) **SUCCESS**, with follow-up source-delta and metadata regression checks retained in PR #275.

- **Corrected-source private ZIP (not published)**: SHA-256 `2022c52a8fed69e25d0efaf00fba0ddda17dd492e8567fd95922f31306c70047`.
- **Older index-only private comparison ZIP (not the proposed release)**: SHA-256 `233c0fdec19ca5d7aa2394fb05be18953c508b8495094fca77d0d47b610c7c5a`.
- **Released version 0.1.0** stays immutable. Prior public packages, tags and catalogue are untouched. Private CI packages are temporary, auto-cleaned, not downloadable release artifacts.

## Proposed public metadata transformation: explicit, reversible and generic

A source-neutral **read-only metadata preparation function** `prepare_provisional_public_commentary_conf` in `scripts/commentary_public_metadata_preflight.py` takes the private candidate `.conf` and a **proposed actual release date** plus reviewable edition summary. It permits *exactly two* metadata field changes, with byte-for-byte restoration of every other key/comment/value:

1. `SwordVersionDate`: original CrossWire 2021-02-14 → **actual future approval/release calendar date**, to be set only when the release is authorized. Do not hardcode 2026-11-15 just because private tests run on that day.
2. `About`: prepend an explicit editorial description of the **Bible Resources edited module**, state that the print-identity claim has **not** been independently verified, then reproduce the **full original upstream About verbatim**, explicitly attributed to the source provider.

Original SWORD fields `DistributionLicense`, `TextSource`, `Version=0.1.1`, accurate `History_0.1.1`, `DataPath`, `BlockType=CHAPTER`, compression, filters, description and all other values must be unchanged from the independently verified private candidate. This preflight **creates no asset**, has **no publication side effects**, and **never** reports editorial or release permission; synthetic negative tests reject invalid dates, original licence/claims drift and metadata injection.

## Repository release-path discovery — distinct from a successful private compilation

**16 November 2026, read-only check of the actual repository:** the existing `modules/mhcc-crosswire` is the **published, strictly stock-identical 0.1.0**, and its approved metadata selects `index_audit.mode=stock_reader_keys`. The [current generic stock-commentary validator](../../../scripts/compiled_stock_commentary_proof.py), called by [`scripts/validate.py`](../../../scripts/validate.py), **requires** the following exact source assertions:

- `SOURCE_VALIDATION.json.source_kind=compiled_sword_stock`;
- `all_original_compressed_files_byte_identical=true`, `all_native_original_keys_byte_identical=true`, `no_original_source_text_edited=true`;
- `only_source_metadata_relabelled=["section_id","DataPath","Version"]`;
- the six original compressed module members match their pinned stock-source member checksums.

This is correct and essential for 0.1.0. **It MUST reject the separately rebuilt 0.1.1**, which intentionally has 24 added original-section navigation links, one source-citation change affecting 11 native linked addresses, **new compression data**, `BlockType=CHAPTER`, an editorial `History_0.1.1` and appropriately attributed `About` and revision-date metadata. Updating only `metadata.json.version` and the `.conf` would therefore be invalid. **Never forge old stock-identical flags or repin original source member hashes to make it pass.**

The normal [`scripts/build.py`](../../../scripts/build.py) builds the public SWORD ZIP **from committed** `modules/mhcc-crosswire/payload/`, while our corrected-source compiled ZIP currently exists **only in temporary, auto-deleted GitHub Actions private test scratch**. Its fingerprint `2022c52a8fed69e25d0efaf00fba0ddda17dd492e8567fd95922f31306c70047` proves the private build, **not** existence in the repository or validity of a public release plan. The published module's `SOURCE_VALIDATION.json`, stock `EDITORIAL.md`, `metadata.json`, release plan `config/release-plans/mhcc-0.1.0.json` and previous GitHub release must remain intact as a historical baseline, not be silently rewritten to describe an edited stock release.

**Generic integration path to review before implementing a public update (structural decision, not yet authorized):**

1. **Preserve an independent original baseline.** Keep the CrossWire pinned ZIP, 0.1.0 source/member/native hashes and the 0.1.0 release asset immutable and independently recoverable. Create a separate attested `reviewed_compiled_commentary_rebuild` validation mode for this *class* of resource; do not weaken or bypass `stock_reader_keys`.
2. **Require comprehensive source-to-candidate proof.** A versioned, reproducible verification record must connect the original source/archive digest, exact source-edited fragment digest, independently reviewed allowed per-key changes and alias map, complete reconstructed I/K/TOP corpus identity and native SWORD link topology, compiled member SHA-256s and the final `.conf` hash. Explicitly distinguish authorial text, original citation corrections, navigational aliases and compiler-produced wrapper/byte differences. Never merely trust a user-supplied Boolean such as `all_original_...=true`.
3. **Fail closed on partial or mismatched evidence.** Check the actual committed candidate payload against its exact compiled file hashes, installed native counts, unchanged original entries and independently pinned permitted deltas; require a valid source-rights/owner-review decision specifically for the new edited version. A current 0.1.0 stock proof must not be reused to approve edited bytes.
4. **Only when the owner approves public release and the architecture**: materialize the exact reviewed corrected native files into a **separate protected release-preparation change**, set the actual release-date `SwordVersionDate` and prefixed attributed `About`, update module version and source validation evidence, then produce and check a deterministic `BRMHCC-0.1.1.zip` with its *new* hash and byte size. Record `docs/releases/MHCC-0.1.1.md` and `config/release-plans/mhcc-0.1.1.json` using the real new hashes and explicit authorization link; update the committed catalogue snapshot only through the reviewed build.
5. **Use the existing ordered publishing workflow.** The exact GitHub Release must be created and independently downloaded/verified **before** GitHub Pages exposes the updated catalogue; after deployment independently check public ZIP, catalogue update/install and unchanged 0.1.0 rollback. **No public release path is functional merely because a private ZIP passes Xiphos.**

**Current implementation:** Steps 1–2 have verified **private SWORD research evidence**, not a production attestation schema, committed final payload or approved new validation strategy. Steps 3–5 are not complete. Do not claim publication readiness, invent final SHA or rely on a not-yet-chosen calendar date.

### Still explicitly blocked until release approval

- Final independent code/source and rights review, especially the new generic source-correction and final metadata guard.
- Editorial confirmation that the original CrossWire public-domain declaration is sufficient for the narrowly corrected derivative; verify the final about/source attribution remains accurate, without adding separately licensed CCEL annotations.
- Choose the **actual approved release day**, produce its final attributed `.conf`, update the curated version and source review fields, and build the **new final deterministic ZIP/size/hash**. The temporary private SHA cannot serve as the new public metadata-adjusted asset checksum.
- Create a versioned, source-pinned approved release plan matching the final package's exact SHA/byte length. Enforce the repository [single ordered publication workflow](../../../docs/PUBLISHING.md), whose GitHub Release must exist and be download-verified *before* the Pages catalogue is deployed.
- Ask the project owner for **separate express authorization** for the GitHub Release, catalogue update and any merge, then verify genuine public ZIP download, catalogue install/update and unchanged 0.1.0 rollback.

**Not completed:** public date, public versioned ZIP/checksum, release plan, independent approval, GitHub Release, Pages catalogue verification. None is implied by CI tests or this document.

## 2026-11-16 — real native attestation draft completed

On [private full original and rebuilt SWORD CI #43867004627](https://github.com/icfmp/Bible-Resources/actions/runs/43867004627), the actual standard-compiler rebuild and libSWORD readbacks **PASSED**, including the six `BlockType=CHAPTER` `.cz*` members (no missing or extra native files), 24 previously vacant K aliases, 12 original K addresses changed only in the two source-corrected groups, all 1,255 original I and two TOP and four real Xiphos passage matches. The complete source audit was emitted into the existing time-limited, **metadata-only** GitHub Actions artifact, with no original commentary text or public ZIP.

- Pinned original native corpus digest: `8abd8bedb4eb0ff425999a9435e18d3c302d3a4f47863e3af5b1de36dfd538e6`.
- Separate original-source **index-only recompile** native digest: `badb234e2c36543d8d5cb536ef8b722c31ccb02944177bc043a14e7b1eb0e045`.
- Current **two-correction private compiled** native digest: `2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e`.
- Exact metadata-only `SOURCE_AUDIT` draft SHA-256: `e51358a9b10185f2a45bbb63a38d6ccf063e8f492905f8519bf4ed9d54aaa7e4`.
- Exact compiled private ZIP (CI scratch only): `aeebadbc57d5a891d10ddb3dec520dcc8abd49e7cdd733c4a3542c77765282c4`.

The three corpus digests are **not interchangeable**: the original source bytes differ from the standard compiler's output. Native source/section semantic parity and the edited-source-versus-index-only exact compiled delta are separately checked. The attestation remains `private_draft_not_owner_authorized_for_release`; the production proof must be regenerated against the eventual **final versioned package**, including the owner-approved date and provenance config, before release. No owner authorization is inferred from a checksum.
