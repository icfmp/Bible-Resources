# BRMHCC 0.1.1 — publication provenance, metadata and rights readiness (review only)

**Date checked:** 2026-11-15. **Status:** `PRIVATE_VERIFIED_CANDIDATE_NOT_PUBLICATION_APPROVED`. Source/metadata analysis is preparatory, not an approval to edit `main`, distribute a ZIP, modify the public catalogue or overwrite BRMHCC 0.1.0. See [publication gate #276](https://github.com/icfmp/Bible-Resources/issues/276), [draft PR #275](https://github.com/icfmp/Bible-Resources/pull/275), [editorial source erratum #277](https://github.com/icfmp/Bible-Resources/issues/277).

## Official reference evidence and attribution

| Claim | Evidence | Publication treatment |
| --- | --- | --- |
| CrossWire MHCC 2.0 revision dated **2021-02-14** | [Official CrossWire module record](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC); exactly pinned original SWORD ZIP SHA-256 `5599108faf01753864d51136a87f120d022e70867cc9df70206a0af3c3a5ef7d` | Keep the source revision/date and archive identity explicitly in `metadata.json.origin`, the source manifest and editorial audit. **Do not retain 2021-02-14 as the new BRMHCC 0.1.1 module revision date.** |
| `SwordVersionDate` indicates the date *that the module was changed*, `Version` gives its revision number and `History_X` records changes | [CrossWire official conf-file documentation](https://wiki.crosswire.org/DevTools:conf_Files) | The new **public** `SwordVersionDate` must be set to the **actual authorized release date** when that date is known, not a guessed preparation or upstream source date. No published date chosen in this document. |
| Original CrossWire `About` states the text matches a Moody Press 28th printing | [CrossWire MHCC module record](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC) and pinned original SWORD .conf | This is a **claim inherited from the upstream provider**, not an independently certified 1:1 print comparison. Preserve the entire original `About` unchanged *as an attributed upstream quotation*, preceded by a short clearly labeled Bible Resources edition notice. Do not delete or silently paraphrase original provenance. |
| CrossWire's source SWORD module declares **`DistributionLicense=Public Domain`** | [CrossWire official module record](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC), original shipped `.conf` and [existing BRMHCC 0.1.0 manifest](../../../../modules/mhcc-crosswire/metadata.json) | Preserve the original attribution, `DistributionLicense` and source module identification. The narrowly documented Ezekiel 3 numeric correction and 24 nav aliases change no underlying original exposition. **No new CC0 claim is attached to the original CrossWire text.** |
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

### Still explicitly blocked until release approval

- Final independent code/source and rights review, especially the new generic source-correction and final metadata guard.
- Editorial confirmation that the original CrossWire public-domain declaration is sufficient for the narrowly corrected derivative; verify the final about/source attribution remains accurate, without adding separately licensed CCEL annotations.
- Choose the **actual approved release day**, produce its final attributed `.conf`, update the curated version and source review fields, and build the **new final deterministic ZIP/size/hash**. The temporary private SHA cannot serve as the new public metadata-adjusted asset checksum.
- Create a versioned, source-pinned approved release plan matching the final package's exact SHA/byte length. Enforce the repository [single ordered publication workflow](../../../../docs/PUBLISHING.md), whose GitHub Release must exist and be download-verified *before* the Pages catalogue is deployed.
- Ask the project owner for **separate express authorization** for the GitHub Release, catalogue update and any merge, then verify genuine public ZIP download, catalogue install/update and unchanged 0.1.0 rollback.

**Not completed:** public date, public versioned ZIP/checksum, release plan, independent approval, GitHub Release, Pages catalogue verification. None is implied by CI tests or this document.
