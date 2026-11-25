# Louis Segond 1910 — proposed 1.0.4

**Technical candidate, awaiting owner approval. No public release or catalogue change.**

Restore source-attested paragraph breaks and indentation in Ezra, Job, Jeremiah, Luke, John, Romans and Revelation. Seventeen original numbered paragraph boundaries were restored and nine displaced boundaries removed (net eight). Restore the two original 1 Peter introduction tables, and remove three literal converter-control residues from Luke and 1 Peter table cells. All changes are byte-reversible; no numbered Scripture prose, punctuation, verse numbering, notes, reference target literals, or lexical associations were changed. Previous reviewed Mark 10:52–53 native slot merge and 12 printed-witness note corrections remain unchanged.

- Both immutable original archives agree on all 2,654 numbered paragraph starts and styles (run 45569597564).
- All 13 source tables and 329 cells match their original row boundaries, folded text, header roles and six inline style spans.
- Official pinned OSIS XSD passes; BRNP has the same 311 unresolved reference targets as the published version (intentionally unlinked).
- Native roundtrip: 31,169 numbered slots, 9,751 notes, 705,605 numbered/body Strong spans, 4,542 titles, 3,236 paragraphs, 23,991 poetry lines, 1,014 groups, 56,482 boundary events. No findings in supported scopes (run 45569845095).
- Actual Xiphos reading-pane prose witnesses 17/17. No pixel-level typography or actual Android GUI claim.
- Independent JSword exact ZIP install: 31,169/31,169 slots, no extra/missing keys, all raw nonspace signatures equal, 23/23 canonical prose samples (run 45575067478, exact final ZIP).
- Two initial builds matched; the final About field was then corrected. The exact final ZIP is SHA-256 `643b33b6f8130c46ec381394169c4ff3b60575b8e7d999ba550fbaeb36f65d05`, 4,268,152 bytes. All seven member hashes are recorded; all six native members equal the previously audited builds.

## Promotion checklist (not performed)

After explicit owner approval, use the existing approved release staging path: replay the exact byte edits, rebuild the seven-member package, verify its exact SHA-256, stage cleaned source and payload with new version metadata, update source/normalization/native proofs and profile version, archive the 1.0.3 release plan, install a reviewed 1.0.4 plan and catalogue import manifest, rebuild the catalogue, run complete Validate/release preflight on the exact PR head. Only then merge the release PR and verify the live GitHub Release and Pages catalogue. Do not put the draft plan into the active config directory before approval. Existing 1.0.3 remains immutable.

## Final metadata and private promotion dry-run

The initial versioned package inherited a stale 1.0.3 About string. The candidate source and six compressed native members remain unchanged; the exact final package must include the corrected About string. The private production catalogue dry-run and owner-authorization rejection are implemented in [the immutable replay workflow](https://github.com/icfmp/Bible-Resources/blob/5208c58aa36250ee1901698533729c85b20b686f/.github/workflows/lsg-layout-package-replay.yml) (run 45575067478). No active release plan is introduced by this PR. The final package receipt and independent reinstall evidence now refer to the corrected package. Standard repository Validate and two standard catalogue builds in the disposable worktree passed; all five other catalogue entries remained identical. The production release verifier rejected the pending owner authorization, as required. Final activation and publication are not authorized by this evidence.
