# MHC — maintained OSIS source

**Status: source workspace reserved; no cleaned text committed or editorial
validation claimed.** This is Matthew Henry's *Complete Commentary*, **not**
the shorter MHCC edition.

## Original supplier

- Provider: CrossWire (original OSIS authoring repository)
- Original repository: https://gitlab.com/crosswire-bible-society/mhc
- Source file: `mhc.osis.xml`
- Original source Git commit: `537591a94c991941877b47a06666b6a7812e05d8`
- Original OSIS SHA-256:
  `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`
- Original OSIS size: 48,020,985 bytes
- Identity, collection and rights: `config/commentary-intake/mhc-crosswire.json`
- Existing tracking: https://github.com/icfmp/Bible-Resources/issues/285
- Working PR: https://github.com/icfmp/Bible-Resources/pull/286

**The original source is pinned but not mirrored here.** Its exact
digital-edition redistribution and modification rights still need
affirmative review. Neither the Public Domain claim attached to the compiled
module nor the historical author's status grants automatic permission to
mirror this particular digital transcription in a public Git repository.

## Planned deliverables

1. `mhc.osis.xml` — our maintained source, added only after public source
   redistribution rights are established; independent hashes and a reversible
   correction record required
2. `CHANGES.md` — each actual cleanup rule and textual correction, its
   justification, affected original scope and before/after checksums
3. Standard rebuilt SWORD module — **generated**, never stored here as the
   editable source; publication is a separate review decision

Technical cleanup and editorial collation are distinct passes. Unnecessary
printer/editor markers, spurious spacing and redundant markup can be removed
where the content is not changed. Asterisks or other marks that may be note
callouts, theological emphasis or meaningful punctuation are **not**
automatically discarded. The original OSIS hash always identifies the
rollback reference.

## Verified technical experiment

A disposable SWORD `zCom4` module was successfully compiled from the pinned
original OSIS on 2026-11-18 with 31,098 numbered native keys, 1,255
introduction keys and 2 TOP keys. The workflow also performed a complete
native key readback and a command-line reader smoke test:
https://github.com/icfmp/Bible-Resources/actions/runs/44258061922

This is **not** a successful full content-parity comparison, editorial
correction, GUI acceptance, or public release.
