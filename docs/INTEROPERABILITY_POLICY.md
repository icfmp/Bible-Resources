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
   unknown, out-of-range and duplicate keys block publication **unless an
   exact adjacent end-of-chapter merge has specific source-bound project-owner
   approval**. Keep genuine source omissions as omissions; report empty
   registry positions, never fill them with invented Scripture.
4. Compile with a released, supported `osis2mod` and read the compiled
   module independently with the released SWORD engine. The *resolved* and
   *populated* verse key inventory must match the source references exactly,
   **except for a specifically reviewed and proven adjacent merge** with
   source bodies fully preserved in the correct order. Do not reconstruct
   the reader-key inventory from the input or assume that a successful query
   proves a key is independently addressable.
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


### Explicitly reviewed adjacent verse merges

When a released stock SWORD versification cannot index an original source's
last verse of a chapter, the project owner may authorize a **temporary,
reversible, edition- and source-revision-bound** compromise. It is not a
blanket permission to renumber Scriptures, insert an annotation into biblical
prose or silently change a source file. The source USFM/USFX and original
OSIS verse milestones remain immutable; the actual compiler and reader
behavior is independently inspected.

The module stages `SOURCE_REFERENCE_MERGES.json` (a reviewed source digest,
exact OSIS source→reader key pairs, rationale and approval). The publication
report must include that exact file's SHA-256, its original publisher
source digest, a complete source→compiled chapter-body comparison and a
cryptographic report digest. `stable_sword_refs.py` accepts the review
file using `--reviewed-merge-policy` and the independent original source
fingerprint using `--publisher-document-sha256`. It **never** marks the
body comparison or human sign-off as passed on its own; the release auditor
must verify those separately.

Even a validated index exception is not a release on its own. The compiled
notes, original Strong and other lemma values, headings, poetry, reference
targets, rights, formatting and application renderings require their own
independent review. OSIS `verse@n` supports editorial numbering metadata,
but normal `osis2mod` does not guarantee visible range numbers in every
frontend. A range label must never be inserted as an invented sentence in
the Bible text.

For the current Segond 1910 pilot, the owner explicitly authorized the
**Mark 10:52–53 merge on 2026-11-08**, preserving both verse bodies in a
single stock `Segond` entry. The decision is source-bound in
[config/lsg-reviewed-verse-merges.json](https://github.com/icfmp/Bible-Resources/blob/test/lsg-stable-segond-candidate/config/lsg-reviewed-verse-merges.json),
and the known original-software limitations are recorded in
[UPSTREAM_LIMITATIONS.md](https://github.com/icfmp/Bible-Resources/blob/test/lsg-stable-segond-candidate/docs/UPSTREAM_LIMITATIONS.md).
This is **not** contingent upon a CrossWire fix or an upstream request.

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

Do not silently split `Job.34.36`, insert verses, renumber this edition,
or claim that another SWORD edition's license covers our redistribution.
The **explicitly authorized** Mark 10:52–53 combined entry is a documented
exception to *individual verse indexing only*: both original texts are
retained, and no Scripture text is inserted or rewritten. Keep all original
files and proposed corrections auditable; a possible Job source issue
is logged internally without requiring upstream contact.

A pinned development SWORD XML-v11n experiment can address both source
keys exactly; stock SWORD 1.9 cannot. **That experiment is R&D only, not
the stable distribution solution.** The ordinary `Segond` importer plus
the approved, source-verified merged index is the temporary stable route.
No Segond module is approved, published, or downloadable from this
repository until the remaining compiled markup, rights, visual and
editorial gates pass.

Official CrossWire documentation:
- https://wiki.crosswire.org/Alternate_Versification
- https://wiki.crosswire.org/Osis2mod
