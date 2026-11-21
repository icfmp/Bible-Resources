# Source-editorial disposition: 47 unmatched original Greek word IDs

**Status: PRIVATE SOURCE AUDIT — NOT APPROVED FOR LEXICAL RELEASE.**

Pinned sources: original MACULA SBLGNT revision `8423afe47b9e8f24b7772e808af45c7159a6fe7e`; original UBS Greek NT Dictionary v1.0 EN/FR revision `a15a96cfaa4ca18a6c0339016645ba1e534db3c8`. Every original word ID is in the privately generated [source evidence audit](audit_last_47_lexical_forms.py). No Greek spelling, Strong, morphology, source LN or historical index may be silently modified.

An explicit second audit of the original lexicon's `Lemma`, bilingual `AlternateLemmas` (which resolved 409 previous word IDs) and `BaseForms.Inflections` leaves **47 source word IDs, across 26 Greek source families**, without a source-approved UBS lexical headword. No family contained a matching exact original Greek inflection metadata string in the tested fields. Sharing a Louw–Nida semantic domain or looking similar to a different lexical lemma is **insufficient** to assert the same lexeme.

## Source inventory

| Original MACULA lemma | Original word IDs | Original Strong | MACULA original class counts | Original LN counts |
| --- | ---: | --- | --- | --- |
| Ναζαρέθ | 6 | `3478` | noun:6 | 93.536:6 |
| Ναζαρέτ | 4 | `3478` | noun:4 | 93.536:4 |
| τάχιον | 4 | `5032` | adj:4 | 67.110:4 |
| ἀκριβέστερον | 4 | `197` | adj:3, adv:1 | 72.19:4 |
| Πρίσκιλλα | 3 | `4252` | noun:3 | 93.302:3 |
| μέλαν | 3 | `3188` | noun:3 | 6.57:3 |
| μόνον | 2 | `3440` | adv:2 | — |
| ἄγε | 2 | `33` | verb:2 | 91.13:2 |
| ἥδιστα | 2 | `2236` | adj:2 | 25.129:2 |
| μέγιστος | 1 | `3176` | adj:1 | 65.53:1 |
| μήτιγε | 1 | `3386` | adv:1 | — |
| μείζων | 1 | `3187` | adj:1 | 87.22:1 |
| μειζότερος | 1 | `3186` | adj:1 | 78.2:1 |
| νουμηνία | 1 | `3561` | noun:1 | 51.5:1 |
| περισσότερον | 1 | `4054` | adv:1 | 78.31:1 |
| πραϋπάθια | 1 | `4236` | noun:1 | 88.59:1 |
| τοὔνομα | 1 | `5122` | noun:1 | 33.126:1, 92.24:1 |
| φαρμακός | 1 | `5332` | noun:1 | 53.101:1 |
| χρύσεος | 1 | `5552` | adj:1 | 2.50:1 |
| ἅλα | 1 | `251` | noun:1 | 5.25:1 |
| ἐγγύτερον | 1 | `1452` | adv:1 | 67.61:1 |
| ἐνέος | 1 | `1769` | adj:1 | 33.108:1 |
| ἔσθω | 1 | `2068` | verb:1 | 23.1:1 |
| Ἰωβήλ | 1 | `5601` | noun:1 | 93.192:1 |
| ὁμοιάζω | 1 | `3662` | verb:1 | 64.4:1 |
| ῥυπαρεύω | 1 | `4510` | verb:1 | 88.258:1 |

## Editorial next steps

- Keep the **10 Nazareth occurrences** (`Ναζαρέθ` 6 and `Ναζαρέτ` 4) unlinked pending verification of the original UBS name and any authentic alternate name spelling. Do **not** conflate different named places merely because their Louw–Nida person/place code coincides.
- Investigate original comparative/superlative inflections (`τάχιον`, `ἀκριβέστερον`, `μέγιστος`, `μείζων`, `μειζότερος`, `περισσότερον`) against named, independent Greek morphological lexicons and the exact original UBS entries. No generic comparative-to-positive alias is permitted.
- Inspect the three accent-only diagnostic comparisons (`πραϋπάθια`, `φαρμακός`, `ἐνέος`) with independent grammatical references. Accent stripping is **not** an approved lexical identity; one Greek accent may distinguish genuinely different lexical entries.
- The original `μόνον` (two word IDs) and `μήτιγε` (one) lack source LN evidence. Do not manufacture an LN code, or assign contextual meaning from another token.
- If a missing authentic UBS lemma or alternate spelling is demonstrated, propose a documented correction to the original UBS lexicon maintainers when appropriate. Until an original source or independent editorial evidence confirms the identity, leave the word unmatched.

## Coverage and release boundary

The reviewed **9,604** distinct original word-ID lexical headwords and the historical unchanged **128,090** Strong-derived candidate word IDs total **137,694 / 137,741 (99.966%)** original SBLGNT Greek word IDs with a source-attested lexical entry candidate. **47 remain without a source-approved lexeme.** Historical 224 multiply headed Strong candidates remain intact, of which 220 have separately source-reviewed word-ID headword identities; four are still unresolved.

These statistics concern lexical *entry/headword identity*, **not contextual UBS `LEXID` sense accuracy**. The original source corpora, lexical dictionary metadata, `index.json`, Strong/LN/morphology/verse annotations and publication status remain unchanged. CI review artifacts are **private and expire after 14 days**. No SWORD resource or Bible application module is published by this audit.
