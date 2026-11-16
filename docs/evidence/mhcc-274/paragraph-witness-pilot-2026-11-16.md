# MHCC — independently pinned paragraph pilot, exact original native entries

Date: 2026-11-16. Investigation [#278](https://github.com/icfmp/Bible-Resources/issues/278), draft [PR #275](https://github.com/icfmp/Bible-Resources/pull/275).

## Objective and non-authority caveat

Determine whether a long SWORD commentary section lost **original internal paragraph breaks**, without treating supplier formatting as authoritative or inventing punctuation, section boundaries or text. Use the existing **SHA-pinned original CrossWire MHCC 2.0** and **separately SHA-pinned CCEL ThML** only as independent digital witnesses. The latter is not an authenticated copy of the precise historical Moody Press 28th printing claimed by CrossWire. Both original inputs stay immutable.

A reusable `scripts/commentary_paragraph_witness_probe.py` compares exact **native I/K keys** selected by an audit CLI argument, independently located ThML `scripCom` section-start markers, actual **`<p>` elements within that source section**, eight-word unique lexical start/end anchors and the **entire case-folded Unicode word-token stream**, in memory. The source witness's chapter-level `<p>` count must never be mistaken for the paragraph count of one numbered commentary *section*. It exports no original words, source XML or annotation targets. The probe never proposes modifications.

## Six representative original source observations

[Exact real corpus pilot #43808286629](https://github.com/icfmp/Bible-Resources/actions/runs/43808286629) **SUCCESS**, including all previous source/compiled I/K/TOP integrity and authentic Xiphos navigation regressions. Preliminary word-whole comparison strengthened in [later PR commits](https://github.com/icfmp/Bible-Resources/pull/275).

| Original native entry | Original SWORD word tokens | Independent CCEL `<p>` per same section | CCEL paragraph word tokens | Original native prefatory word tokens before unique paragraph match | All CCEL paragraph words in same exact order? |
| --- | ---: | ---: | ---: | ---: | --- |
| `K:John.3.1` | 1,569 | **1** | 1,544 | 25 | **Yes** |
| `K:Exod.12.1` | 969 | **1** | 907 | 62 | **No — interior cross-edition difference(s), despite both unique eight-word anchors** |
| `K:Matt.4.1` | 760 | **1** | 723 | 37 | **Yes** |
| `K:Gen.3.1` | 578 | **1** | 509 | 69 | **Yes** |
| `K:2John.1.1` | 220 | **1** | 182 | 38 | **Yes** |
| `I:Lev.19` | 698 | **No uniquely matching CCEL `scripCom` start marker** | Not established | Not established | **Unresolved by this locator** |

In each of the first **five** cases, both beginning and ending eight-word runs are uniquely located at the expected source-section position in the original native SWORD exposition. **Four** independently digitized CCEL paragraph word streams equal the entire contiguous original SWORD exposition word stream after its existing prefatory markup. Their word-order parity is a strong digital-witness concordance, **not** punctuation, XML, rights, historical print paragraphing or complete edition equivalence.

The `Exod.12.1` source paragraph has exactly the same **word-token length** as the remaining SWORD exposition, with unique first and last eight-token anchors, but its **interior** does not match exactly. The added generic difference counter must report the actual position/count and classify it as an **unreviewed cross-digital-edition variant**. Neither text is allowed to replace the other automatically.

The original `Lev.19` prose is present in native **I chapter-introduction** storage with no original K for the chapter, and the established separate source-chapter audit discusses its source location. Do **not** infer that missing a `scripCom` section-start marker means the prose is lost, or move its text to K addresses.

## Editorial implications

1. **Correct the earlier false-positive assumption:** absence of original SWORD `<p>` tags and 807 long unwrapped sections is not by itself proof of **lost internal paragraphs**. Five independent ThML section-start witnesses likewise represent each sampled source exposition as **one `<p>`**. Multiple paragraphs visible across the complete CCEL chapter are generally separate section/outline elements. A long one-paragraph exposition may be unattractive to read without being a source transmission defect.
2. **Do not rewrite the existing K/I/TOP text or insert hypothetical paragraph breaks in BRMHCC 0.1.1.** New internal paragraph splits without an independently identified print-edition source would be a separately labelled editorial presentation adaptation, *not* a verified restoration. Such a decision requires an explicit owner/editorial choice.
3. **Keep the distinct question of reader layout open:** actual Xiphos formatting, historical print evidence and differences between section-heading/outline markup remain to be sampled. Original authorial content/annotations must never be silently altered.
4. **Retain provenance separately:** CrossWire's [module metadata](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC) identifies “Moody Press, 28th printing, ISBN 0-8024-5190-X” as the digital input printing; CCEL's [work record](https://ccel.org/ccel/henry/mhcc/mhcc) identifies a separately prepared abridgement. The cited input provenance is an upstream claim, not independent authentication of the specified printing.

## Release boundary

BRMHCC 0.1.1's separately tested **17 index-section / 24-link** changes and **one strictly bounded Ezekiel 3 reference correction** remain private, reproducible and unchanged. All original K/I/TOP words outside the single authorized private test change remain preserved in the existing full corpus audit. Nothing in this paragraph pilot authorizes additional K aliases, CCEL word replacement, a public download, a catalogue release, merge, a modern-English translation restart or Codex invocation.

This research trail is auditable without publishing independent source text. Independent actual **text/punctuation** comparison, exact print-edition boundaries, final metadata and any editorial paragraphing decision remain separate acceptance gates.
