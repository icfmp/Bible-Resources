# Verified cleaned/maintained sources

Here, and **only here**, maintain real **reproducible and independently
reviewed** OSIS/USFM masters with paths
`<category>/<language>/<resource-id>/`.

An existing published SWORD module does not prove the cleaned editorial source
has been preserved. Original publisher files belong under `../original/`;
copyright and source rights must permit any public derivatives.

Four **actual, SHA-matching, recovered approved OSIS masters** are now
committed under the required type/language/resource IDs:

- [Segond 1910, French Bible 0.1.0](bibles/fr/lsg-1910/lsg-1910.osis.xml)
- [Darby 2024, French Bible 0.1.1](bibles/fr/darby-jnd-2024/bible_jnd_2_0.osis.xml)
- [MHC Complete, English commentary 0.1.0](commentaries/en/mhc-crosswire/mhc.osis.xml)
- [HMCC Modern, English commentary 0.1.0](commentaries/en/hmcc-modern/hmcc-modern.osis.xml)

Every file includes an adjacent original/source-bound `CLEANUP_MANIFEST.json`
and its SHA matches its existing, previously authorized release/source proof.
The original unchanged witnesses are separate under `../original/`.
The historical MHC cleanup reports remain under
[`docs/evidence/mhc-285/source-cleanup/`](../../docs/evidence/mhc-285/source-cleanup/).

**Original MHCC** remains unfilled because an independently source-attested
OSIS authoring master has not been recovered from its original compiled
SWORD pipeline. LSG's full 29,686,495-byte final input was recovered to its
original release SHA, using the precise UTC build timestamp in the converter
metadata; this did not alter the Scripture. A
currently compiled SWORD is not a substitute.

For each real cleaned master, require a SHA-locked original, a reversible
delta manifest, full text/structure/Strong/notes/reference parity, and a
native SWORD readback and independent Xiphos acceptance receipt.

[Workspace layout](../../docs/WORKSPACE_LAYOUT.md).
