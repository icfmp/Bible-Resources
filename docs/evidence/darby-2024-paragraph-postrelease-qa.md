# Darby 2024 paragraph rendering — post-release technical QA

Date: 2026-11-14
Related defect: [#234](https://github.com/icfmp/Bible-Resources/issues/234)
Implementation: [PR #236](https://github.com/icfmp/Bible-Resources/pull/236)

## Scope and immutable provenance

The owner reported literal division asterisks and visibly excessive paragraph indentation in the published `BRJND2024` 0.1.0, notably Genesis 6:9, 6:13 and 7:17 in stable AndBible. The original official **BPC 2024 rev. 2.0 OSIS** is unchanged, SHA-256 `2204629e3efb3024dceb392780ef5e61f4296ea832c90e3dd2a5c3224179c1d3`. This is a private, reversible **technical** rendering overlay, not an edited publisher edition or a new public release.

## Original XML -> native SWORD

- 522 original verse-leading stars were distinguished as **521** editorial paragraph/stanza divisions (477 regular paragraph, 13 major paragraph, 31 poetry) and **one protected text-critical sign** which stays in printed text.
- All 521 editorial division host/type/level tuples survive intact as non-displayed OSIS metadata, with 0 visible `marker` attributes in the native SWORD audit. The source/compiled metadata comparison passed.
- Precise XML pretty-print indentation was removed only at **4,690** verified paragraph-openings (56,288 XML layout spaces); internal textual and poetic spacing was not globally stripped.
- Whole-corpus native gate passed for **31,166** authored verse references and **6,340** notes, including callers, note bodies, note anchors and reference targets. All original source verse keys and intended omissions stayed unchanged. Official OSIS schema and source/native paragraph, stanza and heading checks passed.
- Audited private corrected OSIS SHA-256: `35eb23c62eefdcda9a94d6a493df0bf32d5af1bc6ccc2132e495091d7771406d`. Private compiled module digest: `1d9eac592c6ef99a92493d73dd4718e3a353b1fb478f961c6c09605be6e2524c`. These are **not** public release hashes.
- Source/native proof: [GitHub Actions #43528256423](https://github.com/icfmp/Bible-Resources/actions/runs/43528256423). Independent JSword: [#43528256374](https://github.com/icfmp/Bible-Resources/actions/runs/43528256374). Repository Validate: [#43528256322](https://github.com/icfmp/Bible-Resources/actions/runs/43528256322).

**Residual technical detail:** Raw SWORD can contain a single compiler-inserted leading space at some paragraph openings, including Genesis 6:9, 6:13 and 7:17. No zero-whitespace-byte claim is made. The relevant acceptance criterion is clean **visible** paragraph alignment in multiple independent readers, not elimination of all compiler spacing.

## Independent reader visual review

Final stable AndBible Android 5.1.1117 emulator candidate: [run #43528256427](https://github.com/icfmp/Bible-Resources/actions/runs/43528256427), on the **same private compiled-module digest** above. Independent manual inspection of the captured middle reader pane:

| Screenshot | SHA-256 | Visual finding |
| --- | --- | --- |
| `18-repaired-paragraph-Gen-6-9.png` | `a052601d79c2db202c0a2158ed8c025a68215d2337e7af5850340043114bef27` | `*` no longer visible before Gen 6:9; clean text start |
| `19-repaired-paragraph-Gen-6-13.png` | `113aac4d1ef465ddce8afdfcbc56c7f42d2a31e96317c2cf2668c29481bff6cc` | Gen 6:13 prose start aligned, no extraneous leading token |
| `20-repaired-paragraph-Gen-7-17.png` | `7cf690181af14d2cc54c266c32093aa2ef84c739a0154bd996cde2bb0d4a0941` | Gen 7:17 prose start aligned |
| `21-repaired-paragraph-Ps-3-1.png` | `8abff31c8658d4c32d1be1f6e0472e06d922d271b448f79216fd39ea4b95ef63` | Editorial star not printed; original italic poetry heading preserved |
| `22-repaired-paragraph-Job-3-1.png` | `7f66c16bf0624a9113f9adb96e0ab474d4e052205c5c8bf5bf45d7a7980322fd` | Original triple-star section mark not printed; distinct inline dagger still displayed |

The **Xiphos** headless GUI images of Gen 6:9, 6:13, 7:17, Ps 3:1 and Job 3:1 also show clean section starts and retained line/poetry structure; evidence is the exact-candidate Xiphos screenshot artifact of [#43528256423](https://github.com/icfmp/Bible-Resources/actions/runs/43528256423). Reader styling differs between Xiphos and Android.

**Limits:** The AndBible scripted safe receipt deliberately records some GUI navigation/import flags as `false`, because the automation alone cannot establish successful app import or every deep-link result. Manual review supports **only the passages actually visible in the screenshots**, using the research module selected in the secondary pane; it is **not** evidence of exhaustive Android reader navigation, app restart persistence, or all possible module settings. GUI content read from screenshots must never override exact full-corpus native checks.

## Release boundary and follow-up

This QA justifies merging **processing code, tests and private workflows** from PR #236. It does **not** authorize overwriting the immutable 0.1.0 module, publishing a new ZIP, editing public catalog metadata or marking issue #234 closed. The next independently scoped task is a **versioned 0.1.1 correction release** built from the same SHA-pinned original and reviewed overlays, with freshly attested 0.1.1 package hashes, independently installed final `BRJND2024` binary, and explicit owner/editorial publication authorization.

There is no decision to silently change verse wording, punctuations, omission policy, note bodies, footnotes, note labels or theology.
