# HMCC Modern 0.1.0 — Henry's Modern Concise Commentary

An independently packaged modern-English Matthew Henry concise commentary for SWORD readers, with standard KJV versification and native zCom chapter compression. It uses a distinct SWORD identity `HMCCModern` to avoid overwriting original `MHCC`.

**Scope:** 1,189 canonical chapters, 15 owner-approved editorial reference corrections with 28 targets, and two restored historical authorial sections. Original text/translation witnesses are tracked separately, and the six binary data members are bound to a verified private reader-workflow artifact. This release changes the modern English text, not the original CrossWire module.

**Manual follow-up:** In Xiphos, open Numbers 29:1 and activate the corrected note marker leading to Leviticus 23:24; confirm the destination verse is selected in the sidebar. Other note-linked destinations have verified SWORD markup but have not all been individually clicked in Xiphos. The owner chose post-release manual verification rather than treating an inaccessible CI GUI harness as a textual failure.

The primary Matthew Henry edition is public domain according to CrossWire. The modern rendering and separately recorded derivative editorial elements are not presented as a new copyright in Matthew Henry's original prose. See [the editorial record](../../../../../../../modules/hmcc-modern/EDITORIAL.md).

## Publication verification

The release-candidate staging workflow [#44698186428](https://github.com/icfmp/Bible-Resources/actions/runs/44698186428) completed successfully with the exact reviewed binary, source/rights validator, the full unit suite, deterministic ZIP/catalogue generation, actual SWORD smoke tests, versioned release-plan coverage and dry-run release authorization verification. The payload's original six compressed members remain unchanged from [the separately tested QA module](https://github.com/icfmp/Bible-Resources/actions/runs/44695710957). The committed release plan pins the new public ZIP SHA-256 and length; only publication by the protected main-branch workflow makes the GitHub Release and Pages URL public.

The specific Xiphos footnote-marker click remains explicitly **not verified by automation**. It must be tested manually after installation; this distinction is not a waiver of source integrity, licensing or release checks.
