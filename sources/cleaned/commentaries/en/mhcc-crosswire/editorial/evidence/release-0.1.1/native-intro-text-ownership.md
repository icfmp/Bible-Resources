# MHCC — introduction ownership and chapter-only commentary

**Purpose:** distinguish genuine native SWORD book/chapter introductions from independently authored numbered passage commentary. Original technical observations are recoverable from Git history and [source audit issue #274](https://github.com/icfmp/Bible-Resources/issues/274).

## Original CrossWire source facts

The archived stock native corpus contains **28,718 numbered K**, **1,255 introduction I** and **two TOP records**. Most I records carry no visible prose; **12** contain visible words: **five short book titles** and **seven chapter-level records**. Therefore, neither the presence nor absence of an I entry is sufficient to infer actual authored explanatory prose.

The native `I` versus `K` storage role must be verified for each section independently. Compiling a synthetic `osis2mod` sample proves only that standard OSIS can transport separate introductions, **not** that the original author wrote the reconstructed XML or that all original formatting is preserved.

## Two specifically verified chapter-only cases

| Chapter | Authorial source | Verse-level comment bodies | Safe derivative navigation |
| --- | --- | --- | --- |
| Leviticus 19 | One I-level full chapter exposition | None | Link its one body to 37 canonical verse addresses, if independently validated |
| Psalm 108 | One I-level full chapter exposition | None | Link its one body to 13 canonical verse addresses, if independently validated |

These are **explicit exceptions supported by their actual source**, not a general algorithm to fill every unannotated verse in partially commented chapters. In the Bible application, a chapter-level fallback may be more appropriate than native aliases for some source editions.

## Proof boundary

Preserve the exact original I/K/TOP counts and bodies, authenticated title/intro scope and independent adjacent verse entries. Do not infer source-text equivalence from matching word counts or one rendered passage. The [final cleaned source manifest](../../../CLEANUP_MANIFEST.json) documents the separately reconstructed MHCC 0.1.1 master and limitations; the original CrossWire authoring OSIS was **not** recovered.
