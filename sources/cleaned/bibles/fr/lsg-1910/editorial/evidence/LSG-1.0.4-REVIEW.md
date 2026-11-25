# Louis Segond 1910 — proposed 1.0.4

**Technical candidate, awaiting owner approval. No public release or catalogue change.**

Restore source-attested paragraph breaks and indentation in Ezra, Job, Jeremiah, Luke, John, Romans and Revelation. Seventeen original numbered paragraph boundaries were restored and nine displaced boundaries removed (net eight). Restore the two original 1 Peter introduction tables, and remove three literal converter-control residues from Luke and 1 Peter table cells. All changes are byte-reversible; no numbered Scripture prose, punctuation, verse numbering, notes, reference target literals, or lexical associations were changed. Previous reviewed Mark 10:52–53 native slot merge and 12 printed-witness note corrections remain unchanged.

- Both immutable original archives agree on all 2,654 numbered paragraph starts and styles (run 45569597564).
- All 13 source tables and 329 cells match their original row boundaries, folded text, header roles and six inline style spans.
- Official pinned OSIS XSD passes; BRNP has the same 311 unresolved reference targets as the published version (intentionally unlinked).
- Native roundtrip: 31,169 numbered slots, 9,751 notes, 705,605 numbered/body Strong spans, 4,542 titles, 3,236 paragraphs, 23,991 poetry lines, 1,014 groups, 56,482 boundary events. No findings in supported scopes (run 45569845095).
- Actual Xiphos reading-pane prose witnesses 17/17. No pixel-level typography or actual Android GUI claim.
- Independent JSword exact ZIP install: 31,169/31,169 slots, no extra/missing keys, all raw nonspace signatures equal, 23/23 canonical prose samples (run 45572211747).
- Two isolated package builds yield SHA-256 `b5af554a731cbdc5d5c1e268025add4757a94dc4d8ee7af8fec643ad9d391a68`, 4268093 bytes. All seven member hashes are recorded.

## Promotion checklist (not performed)

After explicit owner approval, use the existing approved release staging path: replay the exact byte edits, rebuild the seven-member package, verify its exact SHA-256, stage cleaned source and payload with new version metadata, update source/normalization/native proofs and profile version, archive the 1.0.3 release plan, install a reviewed 1.0.4 plan and catalogue import manifest, rebuild the catalogue, run complete Validate/release preflight on the exact PR head. Only then merge the release PR and verify the live GitHub Release and Pages catalogue. Do not put the draft plan into the active config directory before approval. Existing 1.0.3 remains immutable.
