# MHCC Modern English — complete private OSIS/SWORD technical reconstruction

**18 November 2026 — technical build validated; NOT a source-faithful editorial edition, NOT released.**

## What was actually built

The existing `scripts/commentary_modern_draft_osis_preview.py` now has a **complete-canon mode** reading the **1,189** source-pinned modern English manuscripts and the full, immutable authentic `MHCC 0.1.1` real-SWORD source receipt. The source reference is the published original SHA-256 `2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e`. This is a *derived* **unlinked** technical OSIS, not a change to the original.

The OSIS was generated **successfully** on the GitHub-hosted isolated build runner and then compiled with the real `osis2mod` into private, temporary **`MHCCFULLTMP`**. The exact build and validation completed on [source-native CI run #44287760714](https://github.com/icfmp/Bible-Resources/actions/runs/44287760714) (**SUCCESS**), together with [Validate #44287760672](https://github.com/icfmp/Bible-Resources/actions/runs/44287760672) (**SUCCESS**) and [tool registry consistency #44287760806](https://github.com/icfmp/Bible-Resources/actions/runs/44287760806) (**SUCCESS**).

### Verified structural output

| Check | Real result |
| --- | ---: |
| Canonical books | **66** |
| Canonical modern English chapter manuscripts | **1,189** |
| Original separate authored numbered-K bodies | **4,047** |
| Exceptional original chapter-I-only authored bodies | **2**, Leviticus 19 and Psalm 108 |
| Modern OSIS numbered commentary groups | **4,049** |
| Modern editorial exposition subsections | **4,052** |
| Native source occupied numbered-K addresses | **28,742** |
| Two approved-for-technical-transport I-only chapter verse aliases | **50** (37 + 13) |
| **Real compiled private SWORD native numbered K addresses** | **28,792 / 28,792**, exactly matched, **zero missing or extra** |
| Modern paragraph blocks in technical OSIS | **40,092** |
| Modern chapter-outline tables | **1,035** |
| OSIS table cells | **8,746** |
| Authentic original chapter-I introductory prose units included as unapproved candidates | **5** |
| Additional book-introduction candidates quarantined, not automatically inserted | **51** |
| Headings lacking machine-readable precise verse-scope labels | **626** (manual scope review still necessary) |

The generated *unlinked* OSIS XML has the reproducible SHA-256 `187e15ab6dab16c4c0ef1e7abe4829b16634807da2b143035dd08afcdb7aebc1`, calculated before `osis2mod` compilation. The private compiled `MHCCFULLTMP` differs from the published original by design; its native-corpus SHA cannot substitute for original/prose parity.

A separate real SWORD `diatheke` smoke readback returned nonempty modern commentary for **Genesis 1:1, Leviticus 19:37, Psalms 108:13, Matthew 13:31, Acts 2:14 and 2 John 1:13**. A full native raw-occupancy scan of the compiled derivative then independently verified **all 28,792 numbered key addresses** against the original K map plus the two explicit I-only exception groups; the report is `mhcc-modern-complete-private-native-key-audit.json` in the CI **metadata-only** artifact. This is substantially stronger than six successful sampled reads, but still a structural/transport check and **not a content/annotation comparison**.

### Reproducible technical-only generation

After the exact published MHCC 0.1.1 source has passed the authenticated real-SWORD receipt procedure in `.github/workflows/commentary-modern-source-receipt.yml`, run:

```bash
python scripts/commentary_modern_draft_osis_preview.py \
  --root work/mhcc-modern/production/accepted \
  --accepted-native-receipt "$RUNNER_TEMP/mhcc-modern-whole-canon-native-receipt.json" \
  --source-topology-manifest work/mhcc-modern/production/MODERN_OSIS_TOPOLOGY_EXCEPTIONS.json \
  --ionly-manifest work/mhcc-modern/production/IONLY_CHAPTER_LINK_PREVIEW.json \
  --book-intro-candidate-root work/mhcc-modern/production \
  --osis "$RUNNER_TEMP/mhcc-modern-complete-unlinked.osis.xml" \
  --report "$RUNNER_TEMP/mhcc-modern-complete-unlinked-osis-structure.json" \
  --temp-module-id MHCCFULLTMP
```

The source source group-to-modern section mapping is explicit for the five known original/editorial topology cases: **Deut.20, 1Sam.25, John.3, Ps.95, Zech.9**. The separate two chapter-I-only exposition cases have all their verse keys attached to *one* authored body per chapter. The modern `##`/nested `###` groupings, original-outline tables in the manuscripts, paragraph breaks and simple emphasis are represented as readable XML; these are **not asserted equivalent to source-native XML formatting**. No unapproved verse boundaries or authorial K groups were invented to make the file compile.

## What is NOT done — non-negotiable release blockers

1. **1,204 original source Bible reference elements** were authenticated in the source but **have NOT been added to this complete OSIS**. A separate ledger proposes **17** source link corrections, with one unresolved single-digit case; all normal links also need correct modern text placement, literal `osisRef` transfer/correction decisions and compiled native readback.
2. **51 unplaced modern book-introduction candidates** are quarantined because their original storage is not proven as a separate source I record; some content may be embedded in original K bodies. Do **not** automatically prepend them and duplicate the exposition. The five authenticated chapter-I prefaces are included as separately labelled **unapproved** modernizations.
3. **626 source-aligned modern subsection headings** lack automatically parsed exact verse scopes. They are not automatically erroneous but must be checked by original K ownership; the five explicit topology exceptions are already handled without broadening native original verse ranges.
4. Source original **paragraph/title/outline, cross-reference, annotation and note equivalence**, and **independent semantic review of all 1,189 chapters** remain unverified. A technical OSIS module which opens in `diatheke` is not a publishable modernized Henry commentary.
5. **Rights and editorial publication approval are still required**. Keep `MHCCFULLTMP` and complete OSIS private and disposable; do **not** upload the text or binary into public CI artifacts, a release, catalogue or approved consumer module before signoff. The source-original published `MHCC 0.1.1` archive and package are unchanged.

**Current decision:** technical **Markdown → complete OSIS → private SWORD** conversion and full indexed-address parity **pass**; human-verified modern **edition**, authorial link parity and release **do not pass**. PR #272 remains a draft, and issue #270 stays open.
