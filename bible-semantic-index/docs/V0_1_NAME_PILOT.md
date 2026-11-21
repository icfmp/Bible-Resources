# Entity index v0.1 — bounded named-entity review (24 cases)

Tracked by [#337](https://github.com/icfmp/Bible-Resources/issues/337). This is **a finite acceptance sample** built from independently checked and merged source-pinned editorial evidence, **not** a certification that all ACAI word-to-entity claims are correct.

Frozen evidence:
- Original ACAI source: `icfmp/ACAI@e80a874e8282f996199c595378a3b3b9a43aac22`.
- Hebrew original-word witness: `Clear-Bible/macula-hebrew@47db250bd55d0d8577f2a94fba114ef16c35b23c`.
- Greek original-word witness: `Clear-Bible/macula-greek@8423afe47b9e8f24b7772e808af45c7159a6fe7e`.
- Editorial fixes: reviewed PRs [#296](https://github.com/icfmp/Bible-Resources/pull/296), [#298](https://github.com/icfmp/Bible-Resources/pull/298), [#302](https://github.com/icfmp/Bible-Resources/pull/302), [#305](https://github.com/icfmp/Bible-Resources/pull/305), [#306](https://github.com/icfmp/Bible-Resources/pull/306), [#308](https://github.com/icfmp/Bible-Resources/pull/308), [#310](https://github.com/icfmp/Bible-Resources/pull/310), [#314](https://github.com/icfmp/Bible-Resources/pull/314), [#320](https://github.com/icfmp/Bible-Resources/pull/320), [#322](https://github.com/icfmp/Bible-Resources/pull/322), [#323](https://github.com/icfmp/Bible-Resources/pull/323), [#325](https://github.com/icfmp/Bible-Resources/pull/325), [#328](https://github.com/icfmp/Bible-Resources/pull/328), [#334](https://github.com/icfmp/Bible-Resources/pull/334), [#335](https://github.com/icfmp/Bible-Resources/pull/335).

## Reviewed finite sample

| Group | Case | Source verse | Original-word evidence | v0.1 disposition | Evidence / qualification |
| --- | --- | --- | --- | --- | --- |
| People vs ancestors | Israel / people | 2 Chronicles 1:2 | wlc:o140010020041 | group:Israel, not person:Israel | Corrected in #334; current living people |
| People vs ancestors | Judah / kingdom | 2 Chronicles 11:1 | wlc:o140110010071 | group:Judah, not person:Judah.4 | Corrected in #334; Rehoboam's subjects |
| People vs ancestors | Levi / Levites | 2 Chronicles 5:4 | wlc:o140050040062 | group:Levi, not person:Levi.3 | Corrected in #334; source plural gentilic |
| People vs ancestors | Ephraim / tribe | 2 Chronicles 28:7 | wlc:o140280070041 | group:Ephraim, not person:Ephraim | Corrected in #334; tribal affiliation |
| People vs ancestors | Israel / elders | Exodus 3:18 | wlc:o020030180061 | group:Israel, not person:Israel | Corrected in #322; community, not Jacob |
| People vs ancestors | Judah / population | 1 Kings 5:5 (WLC) | wlc:o110050050021 | group:Judah, not person:Judah.4 | Corrected in #328; living people in Solomon's reign |
| Homonyms and aliases | Dishon (son of Anah) | 1 Chronicles 1:41 | wlc:o130010410031 | person:Dishon.2, not person:Dishon | Corrected in #310; distinct genealogical individuals |
| Homonyms and aliases | Bebai clan reference | Ezra 8:11 | wlc:o150080110021 | person:Bebai, not person:Bebai.2 | Corrected in #314; family/ancestor expression |
| Homonyms and aliases | Bebai, Zechariah's father | Ezra 8:11 | wlc:o150080110051 | person:Bebai.2, not person:Bebai | Corrected in #314; immediate father in source model |
| Homonyms and aliases | Johanan | 1 Chronicles 3:15 | wlc:o130030150041 | person:Johanan, not person:Jehoahaz.3 | Corrected in #302; separate brother/name token |
| Homonyms and aliases | Shallum / Jehoahaz | 1 Chronicles 3:15 | wlc:o130030150101 | person:Shallum.5 canonical person:Jehoahaz.3 | Reviewed identity in #308; historic royal name form |
| Homonyms and aliases | Two Joash/Jehoash kings | 2 Kings 14:13 | wlc:o120140130061 and wlc:o120140130101 | distinct Judah/Israel king candidates in original order | Corrected in #325; do not collapse same-name kings |
| Places and groups | Perez-Uzzah | 2 Samuel 6:8 | wlc:o100060080121 | place:PerezUzzah; not person:Uzzah | Corrected in #296; compound place name |
| Places and groups | Philistines | Genesis 10:14 | wlc:o010100140081 | group:Philistine; not person:Philistine | Corrected in #298; plural ethnic group |
| Places and groups | Gadara/Gerasa | Matthew 8:28 | sblgnt:n40008028011 | two separate city candidates; unresolved regional expression | #306 preserves ambiguity, not a fabricated geographic certainty |
| Places and groups | Judah / nation | Isaiah 22:8 | wlc:o230220080041 | group:Judah; not person:Judah.4 | Corrected in #322; nation's defenses |
| Places and groups | Ephraim / people | Hosea 13:1 | wlc:o280130010021 | group:Ephraim; not person:Ephraim | Corrected in #322; collective usage |
| Places and groups | Israel / people | 1 Kings 5:5 (WLC) | wlc:o110050050032 | group:Israel; not person:Israel | Corrected in #328; Solomon's contemporary people |
| Mixed / text traditions | Bethabara | John 1:28 | No matching Bethabara original word in pinned SBLGNT | qualified source variant; not an indexed Bethabara token | Source-variant claim in #305; main text has Bethany |
| Mixed / text traditions | Trogyllium | Acts 20:15 | No matching Trogyllium original word in pinned SBLGNT | qualified source variant, not a direct word hit | Source-variant claim in #305; keep Samos/Miletus main-text words |
| Mixed / text traditions | Traditional Matthew 23:14 | Matthew 23:14 | No original-word verse ID in pinned SBLGNT | verse_not_in_pinned_original_word_inventory | Qualified in #320; no invented text |
| Mixed / text traditions | Traditional Acts 8:37 | Acts 8:37 | No original-word verse ID in pinned SBLGNT | verse_not_in_pinned_original_word_inventory | Qualified in #320; no invented confession |
| Mixed / text traditions | 2 Corinthians final benediction | 2 Corinthians 13:14 | No original-word verse ID in pinned SBLGNT | verse mapping to pinned 13:13, not invented names | Qualified in #320; edition numbering difference |
| Mixed / text traditions | Two women in Solomon's judgment | 1 Kings 3:22 | wlc:o110030220022 | explicit candidate vs indirect candidate; historic identity unresolved | #323: do not infer true mother from source role label |

## Final three word-overlap dispositions for v0.1 (reviewed 18 November 2026)

The final three previously unresolved **direct-person name collisions** were checked against the original pinned word and competing external textual explanations. This completes their **bounded review**, not an assertion that the two historical identity puzzles have a demonstrable single answer.

| Original word | Observed original form | Disposition |
| --- | --- | --- |
| `sblgnt:n40016017010` (Matthew 16:17) | Single Greek vocative `Βαριωνᾶ`, *Bar-Jonah*, immediately after `Σίμων` | **Legitimate shared patronymic component:** Simon Peter is addressed by a patronymic containing his father's name. Father/son remain distinct; debate over father **John/Jonah** does not make this an erroneous shared-word assignment. |
| `wlc:o150030090081` (Ezra 3:9) | `יְהוּדָה` (*Judah*) within `sons of Judah` | **Editorially reviewed, historically unresolved:** family name may reflect Hodaviah from Ezra 2:40 / Nehemiah 7:43, but commentators debate alternate name vs scribal transmission. No proof of identity between original records `Hodaviah.4` and `Hodiah.2`. Keep both qualified claims; do not substitute a hypothesized Hebrew word. |
| `wlc:o160120080061` (Nehemiah 12:8) | `יְהוּדָה` (*Judah*) among listed Levites | **Editorially reviewed, historically unresolved:** connecting this Judah with the Hodiah named in Nehemiah 10 is a disputed historical/name-form hypothesis, potentially conflating generations. Retain the distinct `Judah.7` and `Hodiah.2` source claims without asserting equivalence. |

Source discussion: [NET Ezra 3:9](https://classic.net.bible.org/verse.php?book=Ezr&chapter=3&verse=9), [Cambridge Ezra 3](https://biblehub.com/commentaries/cambridge/ezra/3.htm), [Cambridge Nehemiah 12](https://biblehub.com/commentaries/nehemiah/12-8.htm), [Lange Nehemiah 12](https://mail.biblehub.com/commentaries/lange/nehemiah/12.htm), [Keil–Delitzsch Nehemiah 12](https://www.bible.armeniancathedral.org/comments/kad/Neh_12.htm), and the [John 1:42 name-form note](https://www.biblegateway.com/passage/?search=John.1.42&version=NABRE). Exact case-level technical evidence and original-word IDs are retained in [reviewed-person-word-overlaps.json](../data/reviewed-person-word-overlaps.json).

**v0.1 reader contract:** the Bar-Jonah overlap is not an *either/or* choice of which person the Greek word denotes; it is a compound name containing a paternal reference. The two Hebrew cases remain genuinely uncertain and therefore must never be presented as historically established aliases or auto-merged identities. Keep source candidate ambiguity and label the uncertainty in any later UI that presents those cases; the raw source words and every frozen ACAI JSON record remain unchanged.

**Final reviewed-person overlap statistics: 8 direct word collisions = 6 legitimate shared genealogical/patronymic name components + 2 historically unresolved source identity/name variants.** Zero unreviewed direct-person collisions in **this pinned audit**, but this does not establish that all proper names throughout the entire corpus are correct. The 2,332 indirect-only person collisions remain outside v0.1 reader-facing coverage.

## Acceptance boundary

The six source-word absence/variant entries do **not** all have a direct source word: `No matching word` means **no original-word identifier exists for the named claim in the pinned edition**, never a permission to invent one. Other original words may exist in the verse, and textual traditions/versification differ.

The 24 entries are intentionally balanced across (a) historical people-vs-ancestor names, (b) homonyms and aliases, (c) place/group name collisions and (d) explicit/indirect or textual-tradition ambiguities. Already reviewed corrections are **reused, not re-applied**. The unresolved Gadara/Gerasa regional reading, direct patronymic and Solomon judgment cases remain ambiguous: the v0.1 reader must never claim editorial certainty where it is not proven.

The reader API [resolve.py](../scripts/resolve.py) returns only source `explicit_instances` candidates and labels unreviewed entries as `source_unreviewed`. The raw index continues preserving all original `pronominal_referents` and `subject_referents` for later enrichment. No new ad-hoc hardcoded code, no original JSON rewrite, no Strong/lemma guessed word IDs, no requirement to resolve 2,332 indirect overlaps before the first candidate.

**This 24-case sample is a checkable minimum, not evidence of a whole-corpus accuracy rate.** A published resource requires the separate rights/integration checks in [#339](https://github.com/icfmp/Bible-Resources/issues/339).
