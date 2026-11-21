# Source and SWORD formats

A common [Bible Resources Normalization Profile (BRNP)](BRNP.md) is **proposed**, not yet enforced; implementation and conformance tests are deferred to [issue #451](https://github.com/icfmp/Bible-Resources/issues/451). The existing official format, source fidelity and native reader gates remain authoritative.

Use standard SWORD drivers (RawText/zText, RawCom/RawCom4/zCom, RawLD/zLD, RawGenBook). Prefer structured OSIS for scripture and commentary when source material supports it; TEI is appropriate for dictionaries. Preserve authorial structure instead of enforcing a single type on all content. Configuration uses UTF-8, an accurate language code, checked Versification and standard mods.d entries. Test actual retrieval in diatheke or another SWORD client before publishing.


## Source structure standard and fail-closed gate

Use **official OSIS 2.1.1** (validated against the reviewed CrossWire XSD) for marked-up Bibles and commentaries, and a separately validated official TEI format for dictionaries when implemented. Do not invent a Bible Resources XML dialect or pretend SWORD binary data is itself an OSIS XML document. Source format validation precedes any transformation or compilation. The currently approved importer gate is described in [NORMALIZATION_POLICY.md](../policies/NORMALIZATION_POLICY.md); unknown markup halts processing rather than silently being stripped or approximated. A source format can be independently inventoried and rights-reviewed **without converting it**; this does not automatically establish a supported conversion or permit release. Any proposed source-derived conversion needs a format-specific, independently tested adapter. An unchanged stock SWORD edition instead follows its **binary-preservation proof route**, not a fictional XML conversion.


## OSIS commentary semantics

CrossWire OSIS commentaries use `<div annotateType="commentary" annotateRef="...">` rather than the Bible text `<verse osisID="...">` as the authoritative key for the entry. A commentary's `annotateRef` can be a single reference, range, or discontinuous list. Such relationships must not be guessed or derived from visible body quotations. Validated source checks are separate from later SWORD driver compilation; see [COMMENTARY_POLICY.md](../policies/COMMENTARY_POLICY.md).
