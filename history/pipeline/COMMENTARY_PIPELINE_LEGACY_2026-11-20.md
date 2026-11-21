# Commentary pipeline — decisions from early implementation

**Archived design notes, not an alternative source-to-release workflow.** The active [commentary seven-stage checklist](../../docs/workflows/COMMENTARY_7_STAGE_WORKFLOW.md) and [canonical production contract](../../docs/PRODUCTION_PIPELINE.md) supersede this document. Original metadata-only experiments and their command histories are recoverable in Git history at commit `d17d41088eea269e879cbfe46f37a17779ea0ef9`.

## Decisions worth retaining

1. **One source-pinned edition per import.** Treat official CrossWire, CCEL and other witnesses as distinct digital editions until their identity and rights are independently established. Never conflate authorial text with a compiled SWORD entry.
2. **Different driver, different proof.** `zCom`, `zCom4`, `RawCom` and other module types require actual native key/I/TOP inventory, readback, links and versioned configuration. A successful MHCC test cannot serve as a MHC or Wesley attestation.
3. **No invented commentary coverage.** An authored section may comment on one verse, a range or chapter. Preserve chapter introductions, disjoint scopes and independent sections; do not duplicate prose to satisfy navigation.
4. **Keep exact stock reuse and corrected rebuild separate.** Source-bound corrected releases cannot inherit the upstream binary identity claim. A corrected master requires source/cleaned/native comparison, a change ledger and independently accepted rights.
5. **Translation is a distinct derivative workflow.** When modernizing or translating a commentary, use the [accepted-clean-source translation procedure](../../docs/workflows/COMMENTARY_TRANSLATION_FROM_CLEAN_SOURCE.md), preserving argument, scope, authorial notes and quotations with separate semantic review.
6. **Machine observations are bounded.** Commands reporting source SHA, native keys and metadata never authorize license, edits or publication; record `DONE`, `PARTIAL`, `BLOCKED` and `INCONCLUSIVE` precisely.

The original read-only test cases considered a second commentary/driver, but **no future edition's rights or completeness can be inferred** from those pilot results. Use the [tool registry](../../reports/tooling/TOOL_REGISTRY.md) for actual maintained script paths and [publishing guide](../../docs/workflows/PUBLISHING.md) for release procedure.
