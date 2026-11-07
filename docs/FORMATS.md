# SWORD format policy

Use standard SWORD drivers (RawText/zText, RawCom/RawCom4/zCom, RawLD/zLD, RawGenBook). Prefer structured OSIS for scripture and commentary when source material supports it; TEI is appropriate for dictionaries. Preserve authorial structure instead of enforcing a single type on all content. Configuration uses UTF-8, an accurate language code, checked Versification and standard mods.d entries. Test actual retrieval in diatheke or another SWORD client before publishing.


## Source structure standard and fail-closed gate

Use **official OSIS 2.1.1** (validated against the reviewed CrossWire XSD) for marked-up Bibles and commentaries, and a separately validated official TEI format for dictionaries when implemented. Do not invent a Bible Resources XML dialect or pretend SWORD binary data is itself an OSIS XML document. Source format validation precedes any transformation or compilation. The currently approved importer gate is described in [NORMALIZATION_POLICY.md](NORMALIZATION_POLICY.md); unknown markup halts processing rather than silently being stripped or approximated. Other legacy input formats cannot be approved until their dedicated standards-based converters and tests exist.
