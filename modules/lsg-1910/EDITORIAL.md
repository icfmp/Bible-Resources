# Louis Segond 1910 — Bible Resources 0.1.0

**Status:** source and compiled SWORD payload accepted for the **first, explicitly provisional** edition on 2026-11-09 by the project owner. This editorial approval permits initial publication; it does not claim exhaustive typographical comparison against a printed edition.

## Precise source / transformation chain

- Publisher source: eBible `fraLSG` (Louis Segond 1910).
- USFM ZIP SHA-256: `64c4fe2a84d92f958deb0d1add4247d126a21c8a51e5b3058338f661a42d4900`.
- USFX ZIP SHA-256: `fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e`.
- Candidate built with pinned reviewed USFM→OSIS converter and official schema; full-corpus source and stock SWORD evidence: [run #42632394004](https://github.com/icfmp/Bible-Resources/actions/runs/42632394004).
- Three previews tested by the owner in AndBible. The final version reuses all **four** Preview 3 binary text/index files, with **no content change**.
- Release asset: [BRLSG1910-0.1.0.zip](https://github.com/icfmp/Bible-Resources/releases/download/lsg-0.1.0/BRLSG1910-0.1.0.zip), SHA-256 `af2f80ea84f40a6bf62993c9e65c2e2061e1ec20b34b0772a4eb775dd47723c1`.

## Reviewed structural decisions

1. **Versification:** stock `Segond`, to preserve source verse accessibility more closely than the publisher's differently indexed NRSV SWORD binary.
2. **Mark 10:52–53:** the source contains two separate verses, but the stable Segond registry ends at 52. Preserve both complete source bodies in the one available SWORD entry 52, reversible and explicitly approved by the owner. See source-bound manifest in [research PR #24](https://github.com/icfmp/Bible-Resources/pull/24).
3. **Job 34:37:** no independently authored original source verse; do not invent it.
4. **Unresolved heading references:** convert only **2,786** targetless parallel-title references and **25** targetless scope-title references to standard semantic, non-clickable segments, with source text preserved and proven canonical-XML inverse reconstruction. Do not rewrite note references or fabricate machine targets.
5. **Note spacing and introductions:** semantic note text, punctuation, callers, ordered word anchors and structural boundaries validated, but original USFX whitespace differs. Three literal formatting residues in introductory material await a subsequent reviewed update.

## Acceptance and remaining limitations

- Reviewed full SWORD build: [successful CI](https://github.com/icfmp/Bible-Resources/actions/runs/42632394004).
- Independent isolated SWORD package readback: [successful release run](https://github.com/icfmp/Bible-Resources/actions/runs/42657055723).
- Companion full evidence: `lsg-stable-segond.json` in the release and retained as `SOURCE_AUDIT.json` for this catalogue entry.
- Actual Xiphos GUI rendering remains unverified. Bible's mixed-versification parallel alignment problem is separately tracked at [icfmp/Bible#252](https://github.com/icfmp/Bible/issues/252). This is not evidence of lost standalone text.
- The publisher's Public Domain translation declaration is https://ebible.org/fraLSG/copyright.htm ; independently authored future enrichments will require their own rights evidence before inclusion.

This is an **initial reading edition**, not a final textual-critical or print-edition certification. All changes and discovered anomalies must be documented and reversible. The full source and binary audit remain separate from the GitHub publication.
