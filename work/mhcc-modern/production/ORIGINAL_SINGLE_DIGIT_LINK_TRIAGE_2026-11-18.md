# MHCC 0.1.1 original-native single-digit linked-label triage

**2026-11-18 — read-only candidate inventory, not a batch of automatically corrected references.**

The real libSWORD whole-canon reference fingerprint receipt [#44276719759](https://github.com/icfmp/Bible-Resources/actions/runs/44276719759) contains 1,204 original hyperlink occurrences. A bounded local **hash-only lookup** of the original displayed-label SHA-256 values against the exact UTF-8 single characters `0` through `9` found **30 original `<reference>` elements in 27 distinct original source K bodies** with *single-digit link display text*. The target below was recovered only when its SHA-256 matched a real canonical one-verse OSIS target spelling in the already authenticated full-canon K verse registry; all 30 here matched. This is an index to *source literal original hyperlink identities*, not copied original prose.

**Do not assume one-digit links are wrong.** A genuine shorthand reference such as `1Co 5:7, 8` can legitimately display a single `8`, while an ordinary numbered list item can be accidentally hyperlinked by digit-based reference conversion. The distinction requires **actual context and independently readable original witness evidence**, not a regex-only rewrite.

| Original native first K key | 1-based link ordinal | Original displayed single digit | Original compiled target | Editorial finding |
| --- | ---: | --- | --- | --- |
| `1John.2.24` | 2 | `4` | `John.15.4` | **Confirmed correct shorthand John.15.4** |
| `1Sam.6.19` | 4 | `7` | `Mic.6.7` | **Confirmed correct shorthand Mic.6.7** |
| `2Kgs.20.12` | 2 | `8` | `John.16.8` | **Confirmed correct shorthand John.16.8** |
| `2Sam.10.1` | 2 | `7` | `Ps.37.7` | **Confirmed correct shorthand Ps.37.7** |
| `2Sam.19.9` | 2 | `3` | `Ps.110.3` | **Confirmed correct shorthand Ps.110.3** |
| `Deut.11.18` | 2 | `3` | `Ps.119.3` | **Confirmed spurious third enumerator; propose omit** |
| `Deut.4.24` | 2 | `3` | `Ps.19.3` | **Confirmed correct shorthand Ps.19.3** |
| `Exod.12.1` | 6 | `3` | `Rom.8.3` | **Source-witness confirmed spurious list number** |
| `Exod.12.1` | 11 | `4` | `Heb.13.4` | **Source-witness confirmed spurious list number** |
| `Exod.12.1` | 13 | `8` | `1Cor.5.8` | **Source-witness confirmed legitimate abbreviated verse** |
| `Exod.14.21` | 6 | `2` | `2Cor.10.2` | **Confirmed wrong-book link → 1Cor.10.2** |
| `Exod.16.13` | 2 | `3` | `Jas.5.3` | **Confirmed correct abbreviated Jas.5.3** |
| `Exod.28.15` | 2 | `2` | `2Cor.1.2` | **Confirmed wrong-book link → Heb.1.2** |
| `Exod.29.1` | 4 | `6` | `1Cor.1.6` | **Confirmed wrong-book link → Rev.1.6** |
| `Gen.2.8` | 4 | `2` | `2Cor.6.2` | **Source-witness confirmed spurious list number** |
| `Gen.21.1` | 4 | `2` | `2Cor.11.2` | **Confirmed wrong-book link → Hos.11.2** |
| `Gen.3.14` | 3 | `2` | `2Cor.2.2` | **Source-witness confirmed spurious list number** |
| `Gen.3.6` | 2 | `2` | `2Cor.5.2` | **Source-witness confirmed spurious list number** |
| `Gen.3.6` | 4 | `3` | `Matt.4.3` | **Source-witness confirmed spurious list number** |
| `Gen.32.24` | 2 | `5` | `Hos.12.5` | **Confirmed correct abbreviated Hos.12.5** |
| `Judg.7.16` | 2 | `7` | `2Cor.4.7` | **Confirmed correct shorthand 2Cor.4.7** |
| `Lev.14.54` | 2 | `5` | `2Cor.2.5` | **Confirmed wrong-book continuation → Eph.2.5** |
| `Lev.16.1` | 2 | `3` | `Heb.10.3` | **Confirmed correct shorthand Heb.10.3** |
| `Lev.8.1` | 2 | `6` | `1Cor.1.6` | **Confirmed wrong-book continuation → Rev.1.6** |
| `Neh.13.23` | 2 | `3` | `Deut.25.3` | **Confirmed correct shorthand Deut.25.3** |
| `Num.18.20` | 2 | `2` | `2Cor.3.2` | **Confirmed spurious second enumerator; propose omit** |
| `Num.5.11` | 2 | `2` | `2Cor.2.2` | **Confirmed spurious second enumerator; propose omit** |
| `Ps.89.38` | 2 | `4` | `2Pet.3.4` | **Confirmed correct shorthand 2Pet.3.4** |
| `Rom.13.1` | 2 | `2` | `2Cor.2.2` | **Confirmed wrong-book continuation → 1Tim.2.2** |
| `Song.1.1` | 2 | `6` | `Isa.54.6` | **QUARANTINED — source witness does not independently establish Isa.54.6 destination** |

**Disposition status (30 occurrences):** **9** source-witness-confirmed spurious prose-enumerator hyperlinks; **7** genuine abbreviated one-digit references with the **wrong biblical book** in original compiled SWORD; **13** legitimate, correctly linked shorthand references that **must be retained**; **1 unresolved and quarantined** (`Song.1.1` original `Isa.54.6`, label `6`) pending stronger text/source evidence. The **16** proposed single-digit corrections are SHA- and ordinal-attested in the [correction disposition report](GENESIS_EXODUS_NATIVE_REFERENCE_DISPOSITIONS_2026-11-18.md) and [machine-checkable manifest](GENESIS_EXODUS_REFERENCE_DISPOSITIONS.json). A **seventeenth erroneous source link with the two-digit label `14`**, `Gen.3.14` originally targeting `2Cor.2.14` instead of authored `Heb.2.14`, is separately documented there. The 13 confirmed legitimate abbreviated links are deliberately **not modified or suppressed**. These are narrowly reviewed source-link findings, **not derivative SWORD corrections already implemented**.

**No change** to any of the original 1,204 reference elements or to the original compiled `MHCC 0.1.1` module. No derivative link corrections, full SWORD roundtrip, independent semantic signoff or publication approved. Next independently resolve the **one quarantined Song.1.1 candidate**, then examine non-single-digit wrong-link and missing-link cases by authenticated source-group scope. Never auto-correct from label length or regex patterns. Do not conflate original-source link identity proof with correct derived hyperlink destination.
