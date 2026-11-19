# Complete MHC (CrossWire 2.2) — private technical closeout

**Status:** SOURCE-FIDELITY TECHNICAL PASS / READER PRESENTATION PARTIAL / PUBLICATION HOLD.  
**Scope:** [Issue #285](https://github.com/icfmp/Bible-Resources/issues/285), [draft PR #286](https://github.com/icfmp/Bible-Resources/pull/286). No changes to the separate `icfmp/Bible` application.

## Accepted as complete and reproducible

1. Original CrossWire author's OSIS bytes, upstream commit, exact source version and SHA-256 are pinned independently in `config/commentary-intake/mhc-crosswire.json`; the original is never overwritten.
2. OSIS cleanup / structural placement / 25 attested target-attribute corrections preserve source prose, word order, punctuation, section title text, original notes, and links' printed labels. The private native zCom4 compiler/readback accepted **4,256 source commentary bodies** and **32,355** occupied native entries (**31,098 K + 1,255 I + 2 TOP**). The source-to-native ownership checks are fail-closed. [Run #44501242523](https://github.com/icfmp/Bible-Resources/actions/runs/44501242523).
3. The final source-SHA-and-line-gated reclassification puts the authentic **2 Chronicles 1 preface into native chapter I**, while preserving its separate chapter 1 verse exposition. The exact 330 other-key XML deltas are uniquely generated, bijective and balanced `pvN` div start/end renumberings, not source-word/notes/reference changes. The erroneous earlier `title type=x-ms` title context was explicitly reviewed and changed to `type=chapter`. [Run #44517068698](https://github.com/icfmp/Bible-Resources/actions/runs/44517068698).
4. Real Xiphos **rendered three independently sourced substantive passage samples 3/3** and real markup demonstrated 9/9 and 3/3 component links, respectively, for two source-attested multi-target labels. The real GUI step, not merely the overall workflow, was successful. [Run #44517068698](https://github.com/icfmp/Bible-Resources/actions/runs/44517068698).
5. A separate real Xiphos **2Chr 1:1** probe displayed independently verified following-verse exposition, but **did not expose the chapter I preface in the copied verse-pane clipboard**. Its absence is an **unresolved client/presentation observation**, not a loss from the native module. The generic mock regression test fails if only verse text is copied yet intro display is claimed. [Run #44528250861](https://github.com/icfmp/Bible-Resources/actions/runs/44528250861).
6. Pinned AndBible release JSword source built and read real private index aliases successfully. This is an **index/parser test**, not an Android app GUI test. [Run #44528218903](https://github.com/icfmp/Bible-Resources/actions/runs/44528218903).
7. Source text, compiled binary and 48 MB original OSIS were **not committed/published/uploaded as Actions artifacts**. Compiled comparison candidates live only in the ephemeral GitHub Actions runner. A safe metadata-only [candidate receipt](private-release-readiness-2026-11-19.json) captures provenance and gate status.

## Reader presentation: precise acceptance boundaries

The following checks are **not** claimed passed and are not conditions that justify changing the original commentary:

- A real reader mouse click from the original reference label into the intended Scripture destination, especially the **Psalm 60 superscription**; exact compiled OSIS targets have already been independently verified.
- Real chapter-introduction visibility and presentation in a reader's **chapter heading/introduction context**, rather than assuming verse-1 selected text necessarily contains native chapter I.
- Representative rendered authorial paragraphs, titles, notes and section breaks, and additional Android/AndBible presentation when there is a real review environment.
- Exact historical text-edition equivalence of CrossWire authoring OSIS and alternative CCEL six-volume transcription: the independent CCEL witnesses are not grounds for silent CrossWire-text substitution.

A reader that cannot display a legitimate native introduction is a **reader limitation**, not authority to duplicate the preface into verse commentary. Do not change the `icfmp/Bible` app or the source to make a specific UI check pass.

## Publication safety gate

- **Blocker:** the current CrossWire MHC 2.2 listing asserts *Public Domain* and credits CCEL and Logos; the CCEL current policy requires contact before republishing its digital works and a prior Debian packaging effort recorded legal ambiguity. The historical authorial prose being public-domain does not automatically prove permission for *every electronic editorial addition*.
- Written [CrossWire and CCEL inquiry drafts](rights-clarification-letters-UNSENT.md) are prepared, **not sent**. Until evidence on the exact electronic edition and derivatives is obtained and assessed, the [rights review](rights-review-2026-11-19.md) remains on **HOLD**.
- Owner/editorial approval to publish, release version/catalogue entry, actual production SWORD artifact and final packaging attestation are **not** granted or performed.
- The draft PR is **diverged from main** (at this checkpoint, 619 upstream commits behind, 78 branch commits not on main). Reconciliation/revalidation is a **merge-stage task**, not a reason to silently merge while content publication permission is unconfirmed.
- A later `pull_request edited` workflow attempt #44529037290 failed in `apt` installation *before obtaining source*, while the complete [source and real GUI test #44528250861](https://github.com/icfmp/Bible-Resources/actions/runs/44528250861) succeeded at the same source SHA. Do not report that infrastructure failure as a source-data regression.

## Final decision boundary

**Technical reconstruction is complete, but publication is not authorized.** No more sweeping commentary rereads are warranted without a new source-origin defect. Work left is a **small independent real-reader acceptance** (specific navigation/presentation questions), rights-holder response/documented permission, then owner approval and controlled final packaging/merge. If derivative rights cannot be established, propose exact source fixes upstream or withhold the full independent derivative; do not publish it on an assumption.

This file is a status checkpoint and must not be construed as a release approval, exported corrected text or final artifact.
