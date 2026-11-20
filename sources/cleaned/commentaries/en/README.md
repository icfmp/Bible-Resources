# English commentary — cleaned source masters

These are **reviewed, edition-specific OSIS compiler inputs**, not disposable conversions or automatically interchangeable transcriptions. Source identity and structural fidelity differ by edition.

| Edition | Reviewed source | SHA-256 (cleaned OSIS) | Source identity |
| --- | --- | --- | --- |
| MHC Complete 0.1.0 | [`mhc.osis.xml`](mhc-crosswire/mhc.osis.xml) | `c64891f4fb2c3bd3a7e5e6cca992d80675849e7b3615f80ee95121461ef385f4` | CrossWire MHC 2.2 authoring OSIS, independently corrected and reviewed |
| MHCC classic 0.1.1 | [`mhcc.osis.xml`](mhcc-crosswire/mhcc.osis.xml) | `6aca55c36789f6f7d081b7cba2a167a8006cad9447ae8b50d619ad0de32dfb39` | **Reconstructed from attested published SWORD 0.1.1**; original authoring OSIS not recovered |
| HMCC Modern 0.1.0 | [`hmcc-modern.osis.xml`](hmcc-modern/hmcc-modern.osis.xml) | `23f0872a67086d9f659bd96936ab63db63c8c7b8c10eb92e59537c3e6cf16189` | Separately approved modern-English derivative, **not** unchanged Matthew Henry prose |

## Use the authoritative records

Each cleaned edition has an adjacent `CLEANUP_MANIFEST.json` with exact provenance, approved compiler-input identity, recorded transformations and verification limits. Its `editorial/README.md` explains only the **decisions worth knowing**:

- [MHC Complete](mhc-crosswire/editorial/README.md)
- [MHCC classic](mhcc-crosswire/editorial/README.md)
- [HMCC Modern](hmcc-modern/editorial/README.md)

Do not claim the reconstructed MHCC XML is CrossWire's lost original; byte-identical OSIS serialization is **not** the same as independently verified source/native semantics. Original MHC OSIS is retained separately under [immutable sources](../../../original/commentaries/en/mhc-crosswire/). Original MHCC/MHC and modern-English HMCC are **three different editions**.

A maintained OSIS file is not itself proof that its original authorial source, exact native SWORD output and reader display are equal. Changes require source-to-cleaned evidence, full native round-trip, appropriate reader tests and separate editorial/rights/release decisions. Start with the [canonical production process](../../../../docs/PRODUCTION_PIPELINE.md).
