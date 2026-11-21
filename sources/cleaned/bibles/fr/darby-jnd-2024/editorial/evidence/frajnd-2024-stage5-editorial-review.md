# Darby 2024 — stage-5 editorial review: useful conclusions

**Archived review checkpoint; not a current release-status report.** The [approved 0.1.1 release](../releases/DARBY-JND-2024-0.1.1.md), [cleaned-source manifest](../../CLEANUP_MANIFEST.json) and [final reader checks](darby-2024-0.1.1-final-reader-qa.md) supersede this preparatory draft. The full initial per-pass work log is in Git history.

## Decisions to preserve

1. **Exact edition first:** BPC J. N. Darby 2024 revision 2.0, including the chosen SWORD versification and intentional omitted-verse apparatus. Never manufacture Bible verses absent from the source.
2. **Original notes and verse associations:** preserve all **31,166 original numbered entries** and **6,340 translator notes**, their callers, anchors and literal cross-reference targets; do not infer uncertain links from displayed text alone.
3. **Technical markup vs authored language:** separate source XML formatting whitespace from authorial spaces, section divisions, poetry and text-critical signs. The later approved 0.1.1 corrections handle **521 editorial star/division markers** and **4,690 formatting-indentation positions** while protecting the one genuine text-critical star.
4. **Test source and native separately:** validate the entire source-to-cleaned transformation and actual SWORD readback. A successful XML parse or built module does not establish paragraph, lexical and note presentation in readers.
5. **Do not fix client-only rendering in the source.** Xiphos/AndBible samples provide useful compatibility evidence, not authority to reformat the Bible text.

## Where to go

The [release record](../releases/DARBY-JND-2024-0.1.1.md) lists exact original/cleaned hashes, reader evidence and publication authorization; [`CLEANUP_MANIFEST.json`](../../CLEANUP_MANIFEST.json) is the reproducible transformation ledger. Original investigations are traceable via [import issue #62](https://github.com/icfmp/Bible-Resources/issues/62).

This file supplies **no separate source correction authority**. Any new edition or formatting rule needs its own source-attested review.
