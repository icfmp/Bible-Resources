# Verified cleaned/maintained sources

Here, and **only here**, maintain real **reproducible and independently
reviewed** OSIS/USFM masters with paths
`<category>/<language>/<resource-id>/`.

An existing published SWORD module does not prove the cleaned editorial source
has been preserved. Original publisher files belong under `../original/`;
copyright and source rights must permit any public derivatives.

Four **byte-identical recovered compiler inputs** plus one **new, whole-corpus
validated classic commentary source reconstruction** are now
committed under the required type/language/resource IDs:

- [Segond 1910, French Bible 0.1.0](bibles/fr/lsg-1910/lsg-1910.osis.xml)
- [Darby 2024, French Bible 0.1.1](bibles/fr/darby-jnd-2024/bible_jnd_2_0.osis.xml)
- [MHC Complete, English commentary 0.1.0](commentaries/en/mhc-crosswire/mhc.osis.xml)
- [MHCC classic, English commentary 0.1.1 — reconstructed OSIS](commentaries/en/mhcc-crosswire/mhcc.osis.xml)
- [HMCC Modern, English commentary 0.1.0](commentaries/en/hmcc-modern/hmcc-modern.osis.xml)

Every file includes an adjacent original/source-bound `CLEANUP_MANIFEST.json`
and its SHA matches its existing, previously authorized release/source proof.
The original unchanged witnesses are separate under `../original/`.
The historical MHC cleanup reports remain under
[`docs/evidence/mhc-285/source-cleanup/`](../../docs/evidence/mhc-285/source-cleanup/).

**Classic MHCC is now present** as a *newly reconstructed, semantically
round-trip verified OSIS* from the published and source-attested SWORD 0.1.1
module. Its new XML bytes do **not** claim to be the author's historic
CrossWire OSIS. The separately source-recovered originals above *do* match
their published source SHA-256 identities. LSG's full 29,686,495-byte final input was recovered to its
original release SHA, using the precise UTC build timestamp in the converter
metadata; this did not alter the Scripture. A
currently compiled SWORD is not a substitute.

For each real cleaned master, require a SHA-locked original, a reversible
delta manifest, full text/structure/Strong/notes/reference parity, and a
native SWORD readback and independent Xiphos acceptance receipt.

[Workspace layout](../../docs/WORKSPACE_LAYOUT.md).

## Edition-specific editorial decisions

Keep module-specific editorial decisions alongside the approved cleaned master, in `<type>/<language>/<resource-id>/editorial/README.md`. These records document approved changes, unresolved questions, source witnesses and exact evidence; they must never replace the original source, the immutable cleanup manifest or publication receipts. Universal rules stay in `docs/`, while historical research reports remain available until their inbound links and evidence are reviewed.

- [LSG 1910](bibles/fr/lsg-1910/editorial/README.md) · [Darby JND 2024](bibles/fr/darby-jnd-2024/editorial/README.md)
- [MHC](commentaries/en/mhc-crosswire/editorial/README.md) · [MHCC classic](commentaries/en/mhcc-crosswire/editorial/README.md) · [HMCC Modern](commentaries/en/hmcc-modern/editorial/README.md)
