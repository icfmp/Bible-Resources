# First Bible onboarding — lessons from LSG 1910

**Historical retrospective, not a second production workflow.** The first resource's issue, trial receipts and editorial acceptance are preserved in [LSG 0.1.0](../../sources/cleaned/bibles/fr/lsg-1910/editorial/releases/LSG-0.1.0.md), [research PR #24](https://github.com/icfmp/Bible-Resources/pull/24) and [generalization backlog #28](https://github.com/icfmp/Bible-Resources/issues/28). Detailed old stage tables, commands and tentative capability statuses remain recoverable from the file's Git history at `d17d41088eea269e879cbfe46f37a17779ea0ef9`.

## Lessons still useful to a future maintainer

1. Pin the exact source edition and supplier rights, not merely its familiar translation name. Preserve immutable original sources and signed publisher metadata.
2. Compare **whole source versus whole compiled module**, including every verse, intentional omission, unusual versification, note caller, lexical attribution, paragraph/poetry boundary and original introduction.
3. Distinguish a canonical verse index problem from textual loss. **Segond-versification and Mark 10:52–53** required particular source-bound handling; they are not universal patches for other Bibles.
4. Keep editorial notes and section titles semantically distinct from main Scripture. A targetless title or absent-verse citation does not justify adding a navigable target or Scripture.
5. Use official OSIS/USFM validation and real native SWORD readback; independent GUI readers still need source-aware testing, especially across mixed versifications.
6. Correct only proved errors through a reversible ledger; never silently normalize typography or assume a separate electronic witness is equivalent.
7. Distinguish an experiment, a passing CI job, editorial rights approval, published GitHub release and independently verified public catalogue. Record each as a **separate checkpoint**.

Use the [current production contract](../../docs/PRODUCTION_PIPELINE.md) and the [seven-stage Bible workflow](../../docs/workflows/BIBLE_7_STAGE_WORKFLOW.md). This history should no longer be read as a current checklist.
