# Entity index v0.1 — bounded common-noun/topic pilot

Tracked by [#338](https://github.com/icfmp/Bible-Resources/issues/338). This document is **a reproducible first set of source-linked candidate lookups**, not a completed lexical dictionary, a semantic certification of every source category, or authorization to publish.

## Frozen source scope

- ACAI original source: `icfmp/ACAI@e80a874e8282f996199c595378a3b3b9a43aac22` (unchanged original records).
- Original word corpus: pinned Macula WLC and SBLGNT editions from [source.lock.json](../data/source.lock.json).
- Source JSON file inventory at this exact ACAI revision: **flora 104**, **fauna 97**, **realia 345**, **keyterms 868**. These are file counts, **not** counts of independently reviewed entries nor guaranteed current consumer coverage.
- All active original-word IDs in the derived index are independently verified source-present by the existing complete-corpus CI. The examples below are separately asserted in real **reader-facing** exact-word lookups.

## Sixteen representative explicit links

| Source entity candidate | Context | Exact original-word anchor | Observed source sense / limitation |
| --- | --- | --- | --- |
| `flora:Fig` | Isaiah 28:4 | `wlc:o230280040112` | first-ripe fig (fruit, not a tree occurrence) |
| `flora:OliveTree` | Genesis 8:11 | `wlc:o010080110081` | olive in the description of a leaf |
| `flora:Wheat` | Genesis 30:14 | `wlc:o010300140051` | wheat |
| `flora:Barley` | Exodus 9:31 | `wlc:o020090310023` | barley |
| `fauna:Dove` | Genesis 8:8 | `wlc:o010080080032` | dove |
| `fauna:Fish` | Genesis 1:26 | `wlc:o010010260082` | fish |
| `fauna:Lion` | Genesis 49:9 | `wlc:o010490090021` | lion, in poetic imagery |
| `fauna:Camel` | Genesis 12:16 | `wlc:o010120160122` | camels |
| `realia:ArkOfTheCovenant` | Exodus 25:10 | `wlc:o020250100021` | ark construction; named form is contextual |
| `realia:Altar` | Genesis 8:20 | `wlc:o010080200031` | altar |
| `realia:Arrow` | Deuteronomy 32:23 | `wlc:o050320230041` | arrows, figurative threat |
| `realia:Anchor` | Acts 27:29 | `sblgnt:n44027029012` | anchor |
| `keyterm:Faith` | Matthew 8:10 | `sblgnt:n40008010016` | faith |
| `keyterm:Mercy` | Matthew 9:13 | `sblgnt:n40009013006` | mercy |
| `keyterm:Love` | Genesis 22:2 | `wlc:o010220020091` | verb 'you love', not necessarily noun 'love' |
| `keyterm:Covenant` | Genesis 6:18 | `wlc:o010060180031` | covenant (first segment of source group) |

**What the verification proves:** each listed token exists in the pinned word corpus, its exact derived `by_word` direct association is present, and the v0.1 reader resolver exposes that source entity via `explicit_instances`. It does **not** prove that every historical label, article, broader category sense, metaphor or lexical translation in ACAI is correct. An indexed word can have additional independent candidates; the reader must keep ambiguity and `review_status`, rather than assuming one certain meaning.

**What is intentionally not inferred:** this index is not a general word dictionary; it does not provide a complete original-language lexical bridge, and a Strong number or lemma similarity does not establish an exact word-to-entity occurrence. Multiword expressions, suffixes and metaphorical uses must retain their original segmented wording and verse-specific scope.

## Outliers identified during sampling (not accepted as exact topic names)

- `flora:Vine` contains `wlc:o100060190162` at **2 Samuel 6:19**, where the pinned Hebrew labels the word **raisin cake**, not a vine plant. This broad source tag is *not* approved as a direct “vine” name.
- `fauna:Lamb` contains `wlc:o010150090092` at **Genesis 15:9**, where the pinned Hebrew actually reads **ram** (`אַיִל`); do not certify a narrower “lamb” sense from that token.
- `realia:Lampstand` contains `wlc:o020250310111` at **Exodus 25:31**, whose pinned source sense is **buds** (part of the lampstand), not the whole object named by that segment.
- `flora:Fig` at **Isaiah 28:4** is the *fruit*, and `flora:OliveTree` at **Genesis 8:11** refers to *olive* in an olive-leaf phrase; this is an entity/topic lookup, not proof that the clicked word names the whole tree.
- `keyterm:Love` at **Genesis 22:2** is a *verb* meaning “you love,” not a noun.

These are documented source-level semantic scope questions. No blind deletions, name-to-lemma substitutions or ACAI original edits. If these broader subject links are exposed, they must be labeled as **source topic candidates**, not as certified dictionary definitions.

## Reader-facing acceptance

Use `EntityResolver.resolve_for_reader` from [resolve.py](../scripts/resolve.py). Keep only explicit original-word candidates; preserve any direct ambiguity, original corpus/verse guards, and `review_status`. **Do not display participant lists for pronouns.** The full raw index remains available unchanged for future study, audits and deeper contextual enrichment.

Acceptance is limited to the sixteen source-backed examples, with no presumption of whole-corpus lexical accuracy. Full release and redistribution remain gated separately by [#339](https://github.com/icfmp/Bible-Resources/issues/339).
