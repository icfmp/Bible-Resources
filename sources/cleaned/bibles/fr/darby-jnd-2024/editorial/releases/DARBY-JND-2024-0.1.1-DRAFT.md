# J. N. Darby Bible (BPC 2024 rev. 2.0) — Bible Resources 0.1.1

> **DRAFT — NOT YET APPROVED OR PUBLISHED.** This document is a proposed release note, not evidence that a new version is available for download.

## What this maintenance release fixes

- Removes visible raw historic `*`, `**`, `***` editorial subject-section/stanza symbols from the first words of paragraphs in SWORD readers, including Genesis 6:9 and Job 3:1. The original editorial division level and its exact Bible reference remain reproducibly preserved as **non-displayable OSIS metadata**, not discarded or transformed into biblical prose.
- Removes XML source-formatting indentation at **4,690** exact paragraph-leading start positions. This does not normalize authorial spaces inside a verse, poetry layout or note prose.
- Keeps the previous eight reviewed machine-only note destination fixes, three intentionally missing-verse non-link labels and two inline measurement tag repairs from 0.1.0. No absent verse is introduced or restored.

## Fidelity and compatibility evidence

The source remains the exact official BPC JND 2024 revision 2.0 OSIS (SHA-256 `2204629e3efb3024dceb392780ef5e61f4296ea832c90e3dd2a5c3224179c1d3`). Original publisher files are immutable. The private corrected OSIS candidate SHA-256 is `35eb23c62eefdcda9a94d6a493df0bf32d5af1bc6ccc2132e495091d7771406d`.

The research candidate passed independently inspected CrossWire native source-to-SWORD checks for **31,166 source-populated numbered verses**, **6,340 source notes**, and **521 authorial division markers**, including exact original paragraph/poetry markers and host verse IDs. The one original text-critical leading sign was intentionally retained as text. Real independent Xiphos and stable AndBible 5.1.1117 Android reader screenshots confirm clean presentation of Genesis 6:9, 6:13, 7:17, Psalm 3:1 and Job 3:1. See [post-release QA evidence](../evidence/darby-2024-paragraph-postrelease-qa.md), [issue #234](https://github.com/icfmp/Bible-Resources/issues/234) and [release preparation #241](https://github.com/icfmp/Bible-Resources/issues/241).

### Release identity (pending final verification)

- Module: `BRJND2024` (`zText`, `Luther` versification).
- Proposed version: `0.1.1` (prior public version: `0.1.0`).
- Proposed new immutable tag: `darby-jnd-2024-0.1.1`.
- Proposed package: `BRJND2024-0.1.1.zip`.
- **Final release ZIP hash and catalogue URL:** PENDING exact approved final binary build and independent delivery verification.
- **Publication authorization:** PENDING. Do not mark this version published or replace the public 0.1.0 catalogue entry until explicitly approved.

## Updating and rollback

Because the module identifier is unchanged, a SWORD reader may recognize 0.1.1 as an update to 0.1.0, depending on its module-installation and update behavior. For a manual installation, use the final checksum-attested SWORD ZIP once it is published, following the reader's normal installation/update procedure; verify that `Version=0.1.1` is visible after import. Avoid asserting that automatic in-app module updates are supported without a separate real test.

The immutable [0.1.0 release](https://github.com/icfmp/Bible-Resources/releases/tag/darby-jnd-2024-0.1.0) will remain independently retrievable for rollback. Never silently overwrite the old release asset, source original, or source hash.

## Rights and scope

This is an independently curated technical SWORD distribution of the **public-domain BPC 2024 J. N. Darby edition**, not the separately copyrighted Darby revision and not an official BPC software release. It does not claim print-facsimile typography or exhaustive GUI inspection of every verse/note. Original textual-critical choices, notes, and references must remain faithfully documented.
