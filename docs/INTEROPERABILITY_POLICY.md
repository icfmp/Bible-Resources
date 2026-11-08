# Stable SWORD interoperability: release requirement

Bible Resources publishes **standard SWORD modules**, not Xiphos-specific
packages or editions requiring an experimental SWORD build. Xiphos, Bible
(GTK/Python), JSword-based readers and others are consumers, not publication
formats. A module compiling with `osis2mod` is not automatically portable.

## Release contract

1. Work from independently identified, immutable, rights-cleared **authorial
   source archives**, and verify their exact edition and reference system.
2. Enumerate numeric verse capacities from the **actual released** CrossWire
   SWORD registry (not an invented or inferred edition-specific v11n).
3. Check each authored book/chapter/verse reference against the registry;
   unknown, out-of-range and duplicate keys block publication. Keep genuine
   source omissions as omissions; report empty registry positions, never
   fill them with invented Scripture.
4. Compile with a released, supported `osis2mod` and read the compiled
   module independently with the released SWORD engine. The *resolved* and
   *populated* verse key inventory must match the source references exactly.
   Do not reconstruct the reader-key inventory from the input or assume that
   a successful query proves a key is independently addressable.
5. Run separate, complete source-to-compiled **text, punctuation, notes,
   cross-references, Strong's, poetry, headings and chapter navigation**
   audits. Test representative real frontends, including a SWORD C++ client
   and JSword where applicable. Reader appearance is checked separately.
6. Attach `SWORD_COMPATIBILITY.json` to an approved Bible module. Generate
   its baseline with `scripts/stable_sword_refs.py` using independently
   produced text-free source-key and resolved-reader-key inventories, the
   real SWORD registry TSV and the exact module directory. The tool binds
   the report to a source OSIS SHA-256 and a deterministic hash of the entire
   compiled payload; it deliberately writes `reviewed_by=PENDING`. A human
   must review the evidence and record sign-off. `scripts/validate.py`
   fails closed on missing, stale, development-runtime or mismatched proofs.

The index report is **only one gate**. It never certifies text or markup
fidelity, editorial provenance or widespread compatibility on its own.
Snapshot evidence, CLI versions, raw input manifests and reproducible build
instructions must be retained privately and reviewed. Content is not
published merely because all keys were independently addressable.

### Usage

```sh
python scripts/stable_sword_refs.py \
  --source-keys /private/source.keys \
  --resolved-reader-keys /private/resolved-reader.keys \
  --registry-tsv /private/released-sword-v11n.tsv \
  --versification Segond \
  --reader-version 1.9.0 \
  --source-osis-sha256 <validated-osis-sha256> \
  --module-directory /private/approved-module \
  --report /private/SWORD_COMPATIBILITY.json
```

Each input key file contains one `Book.Chapter.Verse` per line, without
Scripture content. The TSV comes from a helper linked against the chosen
released `VersificationMgr` (as in the LSG pilot). The compiled reader
inventory must be obtained by traversing and actually resolving the
published binary, not by reusing the input list. Release builds must also
verify its provenance. The tool refuses a negative comparison and cannot
substitute for a whole-module readback.

## Segond 1910 pilot: edition evidence, not a silent correction

The original eBible `fraLSG` USFM/USFX source has **31,170** unique verse
keys. Against the 18 registered stable systems enumerated by the pilot,
none has an identical key grid. `Segond` has:

- `Mark.10.53` present in the authorial eBible source but outside
  installed Segond's maximum of 52. Stable `osis2mod` appends this verse
  body to `Mark.10.52`, making verse 53 independently unreachable.
- A registered `Job.34.37` entry that is absent from the eBible USFM/USFX
  source. Its text appears attached to verse 36 in eBible's own printable
  presentation, whereas a 1910 print transcription has a separate
  `Job.34.37` reference.

Evidence:
- Full installed-registry inventory:
  https://github.com/icfmp/Bible-Resources/blob/test/lsg-segond-rebuild-roundtrip/docs/evidence/normalizer-3/lsg-sword-v11n-full-coverage.md
- Publisher Mark 10 (verse 53): https://ebible.org/study/content/texts/fraLSG/MK10.html
- Published 1910 print transcription, Mark 10:
  https://fr.wikisource.org/wiki/Bible_Segond_1910/%C3%89vangile_selon_Marc
- Published 1910 print transcription, Job 34 (verse 37):
  https://fr.wikisource.org/wiki/Bible_Segond_1910/Job
- eBible print export, Job 34:
  https://ebible.org/pdf/fraLSG/fraLSG_JOB.pdf

The transcript and eBible exports are **independent review leads**;
they do not authorize an automated edit. Locate and inspect the original
1910 printed page image and publisher source history before deciding if
the eBible verse-36/37 split is an upstream digitization defect or a
documented edition variant. Other discrepancies could still exist.

Do not silently split `Job.34.36`, merge `Mark.10.53`, insert verses,
renumber this edition, or claim that another SWORD edition's license covers
our redistribution. Report a confirmed source defect upstream first and
keep both original files and all proposed corrections auditable.

A pinned development SWORD XML-v11n experiment can address both source
keys exactly; stock SWORD 1.9 cannot. **That experiment is R&D only, not
the stable distribution solution.** No Segond module is approved, published,
or downloadable from this repository until the exact released-runtime
reference and full editorial gates pass.

Official CrossWire documentation:
- https://wiki.crosswire.org/Alternate_Versification
- https://wiki.crosswire.org/Osis2mod
