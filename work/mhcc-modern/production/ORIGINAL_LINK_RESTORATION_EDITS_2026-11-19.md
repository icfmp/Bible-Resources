# MHCC Modern English — source-faithful citation and omitted-clause restoration (editorial proposal)

**2026-11-19 — private draft PR #272 only. Editorial approval and release are NOT granted.**

This is a documented, reversible editorial amendment to **three accepted modern-English chapter manuscripts**, prompted by comparison with original compiled **MHCC 0.1.1** source K/ordinal references (pinned native-corpus SHA-256 `2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e`). No edits were made to the published original MHCC, to its source link literals, to verse divisions or to the Bible reader.

## Manuscript amendments

| Modern manuscript | Original native source K / link ordinal | Original literal target | Restored displayed citation or meaning |
| --- | --- | --- | --- |
| `accepted/matthew-01.md` | `Matt.1.1` #1 | `Gen.12.3` | Genesis 12:3, on the already-modernized promise to Abraham |
| Same | `Matt.1.1` #2 | `Gen.22.18` | Genesis 22:18, same Abrahamic promise; kept as a distinct verse target |
| `accepted/matthew-03.md` | `Matt.3.1` #1 | `Heb.12.13` | Hebrews 12:13, on preparing a straight path |
| Same | `Matt.3.7` #1 | `Acts.2.4` | Acts 2:4, on extraordinary gifts to the apostles |
| Same | `Matt.3.7` #2 | `Luke.11.13` | Luke 11:13, on the Spirit's ongoing graces and comforts |
| Same | `Matt.3.7` #3 | `John.7.38` | John 7:38, first distinct verse of the printed range |
| Same | `Matt.3.7` #4 | `John.7.39` | John 7:39, second distinct verse of the printed range |
| Same | `Matt.3.7` #5 | `Acts.11.16` | Acts 11:16, original concluding cross-reference |
| `accepted/hebrews-11.md` | `Heb.11.32` #1 | `Heb.11.39` | Hebrews 11:39, on the rejection of the faithful |

### Substantive Matthew 3 restoration

The original Concise commentary distinctly teaches **(1)** Christ granted extraordinary gifts of the Spirit to the apostles and **(2)** he grants the Spirit's graces and comforts to those who ask. The latter sentence was absent from the modern manuscript, not merely missing a hyperlink. A faithful modern sentence now restores that second assertion, together with all four directly associated source references.

This is a **meaning-affecting amendment**, not a mere technical hyperlink repair. It must undergo **explicit editorial approval and independent source-meaning review** before publication, despite passing source K/ordinal identity and software tests.

The other changes restore original printed citations adjacent to their already-translated corresponding thoughts, not new commentary interpretations. No speculative source target correction has been applied.

## Full-canon technical checks

On [actual source-native CI #44481658491](https://github.com/icfmp/Bible-Resources/actions/runs/44481658491), **SUCCESS**, both [Validate #44481658412](https://github.com/icfmp/Bible-Resources/actions/runs/44481658412) and [registry #44481658393](https://github.com/icfmp/Bible-Resources/actions/runs/44481658393) passed. The pipeline verified the exact unchanged **28,792 K keys** through real compiled SWORD and readback, plus the original literal targets of recovered links.

The newly rendered citations make **nine** previously source-note-only references directly navigable. Of those, **six** are recovered in the initial original-link reconciliation and **three** in the generic compact-citation pass. The full private candidate has **165/176** formerly unplaced original hyperlink occurrences navigable (counting editorial heading/outline/preface transport explicitly as *transport*), while the remaining **eleven** are **individually source-pinned digital/printed target anomalies** described in `ADDITIONAL_ORIGINAL_LINK_TARGET_ERRATA_2026-11-18.json`, without approved replacement.

Important: source fidelity checks and executable tests **do not substitute for independent editorial assessment** of the modernized meaning, and private native SWORD rendering does not constitute GUI reader acceptance. PR remains a draft; no release, merge or distribution is authorized.
