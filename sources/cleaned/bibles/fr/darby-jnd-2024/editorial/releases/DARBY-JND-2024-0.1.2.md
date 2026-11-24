# Bible J. N. Darby (2024) — 0.1.2

**Configuration-only maintenance update.** Source, annotations, versification and compiled biblical content are unchanged from 0.1.1.

## Scope

- Correct the unregistered `GlobalOptionFilter=OSISXRefs` to the registered `OSISScripref` (#553, PR #554).
- Display name: Bible J. N. Darby (2024); abbreviation: `DARBY2024`. The installed module ID `BRJND2024`, driver `zText` and Luther versification remain unchanged.
- Preserve the exact BPC 2024 revision 2.0 original and approved cleaned OSIS, including all intentional omissions and existing documented reversible editorial overlays. No new editorial changes are included.
- The candidate changes only the configuration member of the native ZIP, verified against the independently downloaded immutable 0.1.1 asset.

## Evidence and acceptance

Original BPC OSIS SHA-256: `2204629e3efb3024dceb392780ef5e61f4296ea832c90e3dd2a5c3224179c1d3`.
Approved cleaned OSIS SHA-256: `35eb23c62eefdcda9a94d6a493df0bf32d5af1bc6ccc2132e495091d7771406d`.
Previous canonical archive SHA-256: `2b48c3c9a8897e58805a7cb3be731bb895363e51bc854df502ce7e7a45f0c2c4`.

The historical 0.1.1 source/native audits and bounded Xiphos/AndBible review remain applicable to the unchanged source and binary content, but are not new 0.1.2 visual or option-mode acceptance. See [the previous reader evidence](../evidence/darby-2024-0.1.1-final-reader-qa.md).

Release preparation includes exact archive and member hashes, renewed source-to-native index/structure/note audit, catalogue and release coverage, default and explicit cross-reference mode tests, and the owner's conditional publication authorization. Issue #549 remains open independently; do not claim that correcting the filter resolves optional-mode plain-text XML leakage.

The immutable 0.1.1 release remains available for rollback. No application repository change.

## Verified candidate result

- Canonical diagnostic ZIP SHA-256: `009af5d19795797337cfa25b68ce96d593fe60f93770d01c44942455d6827e5d` (1960800 bytes); the production builder independently matched it in CI.
- Candidate installed payload SHA-256: `37672ac52e881cf8343412eae65090c2eb745be7027896f10872140f248bb429`.
- Independently downloaded immutable 0.1.1 asset matched its pinned checksum. Only `mods.d/brjnd2024.conf` differed; all six compiled data files were identical.
- Complete native audit: 31,166 numbered verses, 6,340 note bodies/callers/types/anchors/target sequences, 1,257 titles (including two outside-book titles), 5,197 paragraphs, 3,895 poetry lines, 708 poetry groups; all 1,041 explicit target attributes addressable. No numbered reference or note discrepancy.
- Diatheke completed sampled option requests without literal OSIS tags; identical outputs did not independently establish option activation. The explicit native HTMLHREF audit below verifies the actual options.
- [Machine-readable evidence](../evidence/darby-2024-0.1.2-native-audit.json) from [CI](https://github.com/icfmp/Bible-Resources/actions/runs/45376786567). That run was superseded after emitting the Darby results; no overall green CI claim.

## Completed independent engine checks

- [Full-corpus actual SWORD HTMLHREF validation](https://github.com/icfmp/Bible-Resources/actions/runs/45379429851): the explicit standard markup manager was selected. All 31,166 numbered verses passed in four modes (notes/references Off/On combinations), with zero detected residual OSIS elements in plain or HTML output. Both prior and candidate packages returned identical text and HTML for every verse and mode. The previous unconfigured-manager diagnostic was not HTML output and remains tracked separately in #549.
- [Independent stable AndBible 5.1.1117 JSword replay](https://github.com/icfmp/Bible-Resources/actions/runs/45379658739/job/138395070138): five accepted historical integration tests replayed against this exact canonical archive; all passed, all 31,166 source keys addressable, no extra populated keys, representative repaired notes and intended absent verses preserved. This is Java engine evidence, not a new Android GUI test; the previous Android GUI review applies to the unchanged zText data.
- [Real Xiphos candidate and immutable prior reader replay](https://github.com/icfmp/Bible-Resources/actions/runs/45379658739/job/138395069652): seven source-attested reading-pane clipboard witnesses passed for both packages; all seven clipboard SHA-256 values matched between versions, with no detected literal OSIS markup. The automated Gen.2.4 note-preview witness was inconclusive in both versions; neither a new defect nor fresh popup acceptance is claimed. The prior bounded visual evidence and independent note integrity/JSword checks remain applicable.
