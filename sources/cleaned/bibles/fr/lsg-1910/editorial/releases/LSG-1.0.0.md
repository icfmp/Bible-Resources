# Louis Segond 1910 — Bible Resources 1.0.0

The owner selected **version 1.0.0** for the consolidated LSG editorial and navigation improvements. This release is derived from the public-domain **eBible fraLSG** transcription of the Louis Segond 1910 and is distributed as a SWORD `zText` module.

## Improvements

- Added source-attested clickable destinations for **9,440 of 9,751** original eBible parallel-reference notes; **311** deliberately remain visible but non-clickable rather than guessing unsupported destinations.
- Individually clickable passages where one source note cites multiple biblical passages, without suppressing the original visible source citation wording except for the explicitly approved replacements.
- Corrected **12 exact electronic reference fragments** where independently recorded printed 1910 marginal callout evidence supports the correction. The whole original digital apparatus is **not** represented as a verbatim transcription of the printed margin.
- Resolved all three previously ambiguous introduction references: precise link fragments in Philippians and First John (source prose unchanged), and the publisher's **Titus 1:1-40 → Titus 1:1-4** introduction heading typo corrected.
- Visible module name **Louis Segond 1910** and abbreviation **LSG1910**. Internal SWORD identity **BRLSG1910** remains stable for existing readers.
- Fresh native `zText` compiled from the reviewed edition: this release does **not** recycle the earlier RawText binary or the canceled 0.1.1 metadata-only proposal.

## Text, editorial provenance and known limitations

The edited OSIS retains **31,170 source-authored verse IDs across 66 books and 1,189 chapters**. Independent source-versus-native testing verified identical non-whitespace Scripture text for **all 31,169 indexed SWORD verse entries**, and matching note type, callout and non-whitespace note text for **all 9,751 notes**. No biblical wording was edited or supplied by Bible Resources.

**Marc 10.52–53:** the eBible 1910 source numbers both verses independently, but the stable standard SWORD `Segond` registry ends chapter 10 at verse 52. The original content of 10.53 is **retained in the native Mark 10.52 entry**; readers cannot navigate directly to a separate Mark 10.53 slot. This is a documented, reviewed and reversible indexing compromise, **not** full source-native verse-address parity. The underlying reviewed OSIS preserves the independent source ID.

**Job 34.37:** this verse is absent from the exact eBible source. It was not fabricated or restored for the SWORD registry.

Some notes have open-ended `etc.` or source-ambiguous citations. Their wording is preserved and such citations remain unlinked. The project documents the distinction between the modern digital eBible cross-reference apparatus and the verified reference tokens in the 1910 printed edition. No claim is made of complete page-by-page print equivalence. Typography and navigation behavior may differ among SWORD applications; **Xiphos** is the project owner's accepted provisional reader, not independently GUI-certified for this release.

## Exact reproducible package identity

| Field | Value |
| --- | --- |
| Edition | Bible Resources Louis Segond 1910, version **1.0.0** |
| SWORD technical module | `BRLSG1910` |
| Visible abbreviation | `LSG1910` |
| SWORD driver | `zText` |
| Standard SWORD versification | `Segond` (one documented Mark 10:53 indexed merge) |
| Original USFX SHA-256 | `fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e` |
| Reviewed cleaned OSIS SHA-256 | `1eb474496bef0388da403528ea080da489d8b4d980d4b11397ffd8cfe2398a4d` |
| Deterministic ZIP SHA-256 | `cc3b57ab0b61476a77b42fa19004956085d7608a974724c770cc2211adc67499` |
| Deterministic ZIP size | **4,267,040 bytes** |
| Versioned tag | `lsg-1.0.0` |
| Source rights | eBible `fraLSG`, **Public Domain** |

All **seven native package members**, source and compiled text/index metadata are bound to exact per-file hashes in [the 1.0.0 source import manifest](../../../../../../../config/catalogue-import-lsg-1.0.0.json). The [reviewed electronic correction ledger](../REVIEWED_REFERENCE_AND_INTRO_OVERLAY_2026-11-23.json) records the reversible replacements and printed witnesses. Full reference/navigation and native-verse validation are documented in [PR #544](https://github.com/icfmp/Bible-Resources/pull/544) and [release PR #546](https://github.com/icfmp/Bible-Resources/pull/546).

## Historical releases and publication controls

The **0.1.0 historical GitHub release and Pages package remain immutable**; their previously known different fingerprints are retained in [the archived 0.1.0 legacy binding](LSG-0.1.0-LEGACY-BINDING.json). The superseded 0.1.1 proposal was closed without publication.

The new release ZIP, OSIS, profile, catalogue snapshot and release plan must pass the official validation and protected GitHub Pages publication workflow. A PR containing these files is **not itself proof that the public 1.0.0 release exists**; public distribution is confirmed only by verifying the exact tagged asset and live HTTPS catalogue after authorized merge.
