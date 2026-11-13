# Matthew Henry's Concise Commentary — English resource profile

**DRAFT — NOT FOR PUBLICATION · 2026-11-13**

This is proposed reader-facing metadata for the **specific CrossWire MHCC 2.0 digital module**, **not** Matthew Henry's complete commentary (`MHC`), a new translation, or a claim to reproduce an identified historical print edition exactly. The project owner has not granted editorial, rights, profile, or release approval. Do not add this file to any public catalogue, create a profile approval receipt, or ship it in the application until the separate approvals are documented.

## Short description — library

### Matthew Henry's Concise Commentary

**Bible commentary · English · Whole Bible**

A shorter commentary on the books of the Bible, attributed to the English minister and author Matthew Henry. It offers historical Christian exposition alongside Scripture, intended as a companion to biblical reading rather than a replacement for the Bible text.

This research edition is based on **CrossWire's MHCC 2.0 SWORD module**. Its original compiled commentary text has been preserved byte for byte in a private test candidate.

**Source:** CrossWire MHCC 2.0 · **Availability in Bible Resources:** not yet released

## Full description — resource details

### About the work

*Matthew Henry's Concise Commentary on the Whole Bible* presents an abridged form of the exposition associated with Matthew Henry (1662–1714), an English Nonconformist minister and Bible commentator. It is an English-language commentary to consult beside the biblical text, not a biblical translation or a critical textual apparatus.

Readers should distinguish the concise commentary **MHCC** from the longer **MHC**. Neither its name nor its association with Henry establishes that every individual digital transcription, editorial heading or annotation is identical across publishers.

### About this exact digital source

The proposed resource retains the existing, compiled CrossWire module:

| Field | Source-backed value |
| --- | --- |
| Upstream provider | CrossWire |
| Original SWORD module ID | `MHCC` |
| Original module version | **2.0** (dated **2021-02-14**) |
| Language and category | English, commentary |
| Compiled SWORD driver / mapping | `zCom`, `KJV` versification |
| Original declared source | Moody Press, 28th printing, ISBN **0-8024-5190-X**; an earlier digital text with subsequent corrections is also reported |
| Distribution claim | Original CrossWire `.conf` says **Public Domain**; the official module page also says it may be copied freely |
| Bible Resources candidate | Private test-only ID `BRMHCCReview`; full original compressed SWORD payload unchanged, with only test identity/path metadata adapted |
| Public Bible Resources release | **None — approval pending** |

The earlier CCEL XML/ThML transcription is an **independent digital witness**. It is not established as byte-identical or textually identical to CrossWire's compiled MHCC. This project has not replaced CrossWire's actual text with CCEL readings or silently corrected any of its notes, headings, punctuation or references.

### Verified technical characteristics

- The exact upstream archive and module configuration are SHA-256 pinned, and all **29,975 occupied native SWORD commentary keys** (including introductions) were independently checked for original-to-private-candidate byte preservation.
- With the approved `BRLSG1910` Bible installed beside the commentary, **five** selected passages were actually displayed and their prose read back from the Xiphos commentary pane, matching the original stock SWORD text.
- **Two** original scripture-reference labels and their exact original `osisRef` link destinations were present in real Xiphos rich-text output. Actual mouse click navigation and the visual presentation/placement of all headings remain unverified.

These findings establish that the **private candidate** preserves the selected original digital module content and works in tested reader scenarios. They are not a full review of every rendered paragraph, heading or external link.

### Provenance and rights for review

**Author/work:** Matthew Henry's concise biblical exposition. **Compiled digital edition reviewed:** CrossWire MHCC 2.0. **Original package:** [CrossWire official module record](https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC) and [official SWORD ZIP](https://crosswire.org/ftpmirror/pub/sword/packages/rawzip/MHCC.zip). **Source and rights evidence:** [exact-edition dossier](../evidence/mhcc-177/crosswire-exact-stock-rights-review.md).

CrossWire's specific public-domain declaration is documented positive distribution evidence. Nevertheless, Bible Resources has **not independently approved the provenance or redistribution status of all potentially separate digital corrections and editorial additions**, nor issued the required owner legal/editorial sign-off. The independently retrieved CCEL transcription has its own rights and transcription concerns and is **not** being republished by this candidate.

**Version and release:** No public Bible Resources version, update policy or catalogue record has been approved. Any eventual resource ID, public version or editorial characterization must be reviewed separately.

### Review records

The technical evidence for the chosen exact-stock preservation track is in [MHCC import issue #177](https://github.com/icfmp/Bible-Resources/issues/177), especially [private Xiphos candidate verification #224](https://github.com/icfmp/Bible-Resources/pull/224). The independent CCEL-vs-CrossWire lexical comparisons and the five remaining properly comparable cases are documented in the [read-only editorial queue](../evidence/mhcc-177/source-book-identity-five-case-review-queue.md). Those differences **do not constitute proven errors in this exact upstream digital module**.

This draft is **descriptive material only**. It does not certify any issue as resolved, provide publication permission, change source/licence metadata or modify the SWORD module.
