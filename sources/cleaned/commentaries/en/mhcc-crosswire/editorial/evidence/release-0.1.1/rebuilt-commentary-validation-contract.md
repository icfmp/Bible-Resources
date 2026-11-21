# Rebuilt SWORD commentary — accepted validation architecture

**Technical contract:** corrected compiled commentaries cannot use the proof route reserved for an **unchanged upstream stock SWORD** archive. Rebuilds and exact-stock redistribution have fundamentally different integrity assertions.

## Two distinct proof routes

- **Unchanged stock** (`stock_reader_keys`): independently pin the provider archive, compiled native member bytes and real reader/index inventory; any changed original payload makes this claim false.
- **Reviewed corrected rebuild** (`reviewed_compiled_commentary_rebuild`): pin original source identity, complete original→candidate full native body/identity comparison, exact reviewed prose/markup corrections, explicit alias mapping and the final compiled configuration/member SHA-256s. Use `scripts/reviewed_compiled_commentary_rebuild.py`; an input `validated=true` assertion is not itself proof.

## Required evidence for a corrected candidate

1. The exact original SWORD/OSIS edition, original archive SHA-256 and rights for a derivative.
2. A source-attested ledger of **every changed authorial word, reference target, note/section boundary and alias**. Unrelated prose and native linked identities must compare unchanged.
3. A full independent libSWORD K/I/TOP inventory and canonical ordered corpus comparison from original through candidate. Prove that no original entry was dropped, reinterpreted or newly invented.
4. Exact SHA-256 and member count for all driver-appropriate SWORD data files and the `mods.d` configuration. `zCom` chapter compression, `zCom4` and other drivers may differ: never hard-code an unrelated driver layout.
5. Deterministic package/installation tests and sampled independent reader tests with explicit unverified interaction/display behaviors.
6. Separate human review of actual edition rights, editorial choices and public release, followed by actual GitHub Release and public catalogue package verification.

## Historical MHCC 0.1.1 scope

MHCC's approved corrected rebuild has **24 original-section aliases, two exact source corrections, 28,742 numbered native K keys, 1,255 I and two TOP**. These counts are *case evidence*, not universal requirements. The accepted exact correction set and hashes belong to [MHCC rebuild manifest](../../../../../../../../config/commentary-rebuilds/mhcc-crosswire.json), [native audit](../../../../../../../../modules/mhcc-crosswire/SOURCE_AUDIT.json) and [0.1.1 release](../../releases/MHCC-0.1.1.md).

Do not reuse the historic private ZIP/test-date digests as a public release checksum. The actual [production contract](../../../../../../../../docs/PRODUCTION_PIPELINE.md) and [publication procedure](../../../../../../../../docs/workflows/PUBLISHING.md) remain authoritative.
