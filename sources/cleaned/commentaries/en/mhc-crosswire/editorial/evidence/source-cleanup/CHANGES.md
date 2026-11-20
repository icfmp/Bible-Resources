# MHC — reviewed source change ledger

The original CrossWire authoring OSIS is preserved unchanged. This summary identifies **actual approved structural corrections**; exact source and intermediate SHA-256 hashes are authoritative in [`CLEANUP_MANIFEST.json`](../../../CLEANUP_MANIFEST.json). Reproduce a new release from its reviewed plans, not this prose summary.

| Change | Why / safeguard |
| --- | --- |
| **11 empty inert `hi type="super"` leaves** | Remove unsupported empty formatting markup only; nonempty emphasis and authorial prose unchanged |
| **3 invalid range endpoints** | Verified correction for Proverbs 31, Isaiah 7, Acts 26 against source and native bounds |
| **25 machine-readable `osisRef` destinations** | Correct source-attested targets without altering displayed citation wording |
| **6 overlap/navigation groups** | Restore independently authored scope; preserve every original section |
| **2 Chronicles 1 preface classification** | Put original chapter-preface content in native introduction, keep verse-one exposition distinct |

## First proven lossless cleanup checkpoint

Original XML SHA-256: `3cf367f00c498a3124b339c00896aaef4ef1196a2d5c310ecb20ea42abd130f6`.

After removing the 11 empty formatting leaves: `ded53fe37e83609790433a01b2dabf0ea3a13e929bd3bded39262ce4a5b24016`.

The reviewed empty tags were on original XML lines **6451, 6850, 7895, 12595, 15355, 15363, 15397, 15415, 15519, 111795, 113304**. Original full visible Unicode character SHA-256 was unchanged: `defe78fc9c56be07e0eeb577c73c52ac0c21a443342a5a10bd1c28d12e8029ff`. [Native control run](https://github.com/icfmp/Bible-Resources/actions/runs/44270721733).

The final cleaned source includes additional reviewed transformations recorded by the full manifest; **do not treat the initial empty-tag SHA as the final release master**.

No source quotation, title, note, paragraph or commentary entry may be silently rewritten or replaced by different-edition CCEL wording. For the current release see [MHC 0.1.0](../../releases/MHC-0.1.0.md).
