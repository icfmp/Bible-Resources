# Complete MHC — corrected SWORD in an actual Xiphos reader (2026-11-18)

**Status:** three independently selected corrected-commentary passages
visibly matched a real Xiphos GTK GUI clipboard. This is **not yet a
hyperlink-click or complete edition-presentation signoff**.

## Exact reproducible evidence

- Working draft: [PR #286](https://github.com/icfmp/Bible-Resources/pull/286),
  implementation SHA `6a4f89e5f59dc131b46b6b61019494995c2572ad`.
- [Private real Xiphos run #44313437723](https://github.com/icfmp/Bible-Resources/actions/runs/44313437723):
  the complete build, native XML/source fidelity, actual GUI dependency
  installation, GUI experiment, and general validation all **PASSED**.
- The **25** separately SHA-, original-line-, book- and label-hash-anchored
  source corrections were found in the compiled private module (no source
  exposition or displayed citation labels changed). There were exactly
  **32,355** native occupied records: 31,098 numbered K, 1,255 I
  introductions, and 2 TOP. The native XML comparison detected **197** keys
  containing reviewed link-attribute changes; no unrelated text, note, element,
  or other attribute changed.
- The isolated GUI installed a genuine Xiphos GTK application with the
  existing five-file SHA-attested released BRLSG1910 Bible and the privately
  recompiled `MHCLinkPreview` SWORD module. The three source-line cases below
  were independently selected from actual compiled verse groups, not invented
  test fixture passages:
  - Source line **50772**: Proverbs 31, compound Proverbs references preserving
    the complete 25:8–10 range.
  - Source line **81529**: Matthew 28, Luke 24:7–44 range and Mark 16:7.
  - Source line **58059**: Isaiah 63, Psalm 60 **chapter root** plus 2 Samuel
    8:13–14; printed citation refers to the Psalm's *superscription*.
- The GUI returned `real_xiphos_window=true`,
  `accepted_passage_commands=true`,
  `independent_gui_excerpt_matches=3` / `sample_count=3`,
  and no failed GUI action categories. **Each of the three actual copied
  commentary excerpts matches a separate diatheke/native-SWORD witness**.
  Only bounded counts, booleans and source lines were emitted; no authorial
  prose, screenshot, original XML or compiled binary was uploaded.
- The earlier [run #44306657428](https://github.com/icfmp/Bible-Resources/actions/runs/44306657428)
  and [run #44305258183](https://github.com/icfmp/Bible-Resources/actions/runs/44305258183)
  were **not GUI successes**: both Xiphos installation attempts timed out.
  The corrected GUI test eventually passed after using the canonical Ubuntu
  archive instead of the very slow EC2 regional mirror. They must not be
  counted as rendering failures or as rendering successes.

## Still unproven

- **Actual hyperlink mouse click** from the visible Isaiah 63 citation to the
  Psalm 60 *superscription*. A valid `Ps.60` chapter-root target is not
  evidence that a particular reader highlights the title.
- Rich-HTML link-label/target correspondence within the actual GTK-rendered
  commentary for each of the three cases; the existing helper can inspect
  clipboard HTML independently, but the first successful run logged only
  plain-text source-excerpt matches.
- Whole-chapter deduplication and section ownership at **2 Chronicles 1:1**,
  overlapping verse boundaries, long-commentary headings/paragraphs, notes,
  introduction navigation, and actual Android **AndBible GUI** selection.
- Original historical-edition identity, Psalm 7 / Acts 17 source differences,
  the exact rights applicable to a publicly modified electronic derivative,
  and explicit editorial/release permission.

**No release or merge:** the complete original OSIS, private corrected
commentary OSIS and compiled SWORD stayed in runner temporary storage. This
reader exercise is additional technical evidence, not a license or publication.
