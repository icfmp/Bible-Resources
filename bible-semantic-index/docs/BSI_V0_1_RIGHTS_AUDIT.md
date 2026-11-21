# BSI v0.1.0 — redistribution scope and source rights review

Review date: 2026-11-18. This is a documented source-license and field-selection
review, not an assertion of exclusive copyright ownership or legal advice.

## Authority and frozen materials

- Original ACAI snapshot: `icfmp/ACAI@e80a874e8282f996199c595378a3b3b9a43aac22`.
- Source README: https://github.com/icfmp/ACAI/blob/e80a874e8282f996199c595378a3b3b9a43aac22/README.md
  (the **JSON and Markdown release is CC BY-SA 4.0**, copyright 2025
  Mission Mutual; its LICENSE.md credits BiblioNexus 2024).
- Source license: https://github.com/icfmp/ACAI/blob/e80a874e8282f996199c595378a3b3b9a43aac22/LICENSE.md
- MACULA Hebrew and Greek pinned editions are recorded in `../data/source.lock.json`;
  their dataset LICENSE files declare CC BY 4.0. BSI does **not** package
  their original biblical text, glosses or source TSV data; it retains
  edition-qualified original-word IDs verified against the pinned inventories.
- UBS open thematic/lexical materials are publicly available at
  https://github.com/ubsicap/ubs-open-license . BSI is **not** redistributing
  thematic dictionary articles or their descriptions. The ACAI release's
  licensed identity annotations, not an unseen copied lexicon, remain
  the primary source of BSI records.

## Explicitly excluded

| Source field/content | v0.1 distribution |
| --- | --- |
| **All** `keyterms` entities | Excluded, along with all their reverse lookup links, qualified/missing references and labels. Paratext UBS Key Term data are described by ACAI as **“used by permission”**. No permission inheritance assumed. |
| Multilingual `localizations` and descriptions | Excluded. A **separate**, source-SHA-verified *English preferred_label only* is distributed, marked source-unreviewed. |
| `speeches`, biographies, roles, genealogy, geography, coordinates, third-party article links, dictionary entries, Strong crosswalks | Not included by the compiler or public package. |
| MACULA Hebrew/Greek text or original linguistic TSV files | Not included. Only source-version-qualified word identifiers are linked. |

## Distributed fields

- Entity ID, canonical ID, classification, original-source references, exact
  WLC/SBLGNT word groups (explicit and source-claimed indirect), inverse
  lookup, human-reviewed corrections with evidence, source SHA-256 and
  versioned provenance.
- A second JSON file with English `preferred_label`, its source entity ID,
  language and `source_unreviewed_label` qualification.
- Source lock; reproducible metadata and checksums; attribution/change notice.

These fields remain **an adaptation of CC BY-SA 4.0 ACAI data**, not a
newly authored replacement of ACAI. BSI data are distributed under CC BY-SA
4.0, with the original authors, original release and exact source revision
identified in `ATTRIBUTION.md` in the archive. No endorsement is claimed.

## Limitations and future action

The source's general dataset license is direct affirmative evidence for
reuse of retained records; excluding explicitly permission-only Key Terms
removes the known specific exception from the distribution. This review has
not found a separately incorporated restricted dictionary article or
copyrighted Bible text among the retained BSI fields. It is not proof that
every historical upstream third-party provenance question has been
conclusively litigated. If a rights-holder identifies a further restriction,
withdraw the affected distribution version and issue a new, explicitly
scoped corrected version rather than silently changing published bytes.

No original source JSON is edited. No synthesized Hebrew/Greek IDs or
manuscript verses are introduced. The v0.1 package deliberately makes
**no claim of complete independent historical/semantic certification**.
