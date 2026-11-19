# MHC 2.2 — bounded reader acceptance for first private release candidate

**Technical decision:** accept the first private CrossWire-derived MHC SWORD candidate as **reader-tested with explicit limits**, not as a guarantee that every frontend implements all OSIS markup. This review does not publish or merge the module.

## Verified by independent real readers

- [Private Xiphos source/GUI run #44539128176](https://github.com/icfmp/Bible-Resources/actions/runs/44539128176): three independent substantial commentary text excerpts were read in GTK/Xiphos and compared to the original source/native SWORD, **3/3 passed**. No failed GUI navigation-command categories.
- The authentic preface of **2 Chronicles 1** appears as native chapter-introduction content. It was independently copied and verified **through Xiphos's chapter-heading/context menu**. Normal verse-pane clipboard text contains only the corresponding original exposition; those are separate source frames, not a lost or duplicated preface.
- Two source-authored rich-reference labels were real links in the GTK HTML clipboard, with **9/9** and **3/3** original Scripture target components encoded within the corresponding real GUI anchors. These checks do not prove exact URI equality or what a mouse click will select.
- [Native source/full structure run #44544830593](https://github.com/icfmp/Bible-Resources/actions/runs/44544830593): all **32,355** frames and 25 approved source-attested machine-target repairs retain source/markup/word fidelity. [Pinned AndBible JSword test #44528218903](https://github.com/icfmp/Bible-Resources/actions/runs/44528218903) independently checks index compatibility (not the Android app GUI).
- The final private `MHC` 0.1.0 ZIP was reinstalled and read by the real SWORD engine; its **six binary data members are byte-identical** to the verified preview and its full native raw corpus checksum matches. No content was exported.

## Not tested or not asserted

- A physical mouse click on every corrected reference, in particular the Psalm 60 superscription landing behavior; reader-specific click/preview semantics remain **unverified**.
- Detailed visual review of every original title, note, footnote popup, poetry or paragraph in Xiphos, AndBible or any other frontend.
- An interactive Android application GUI acceptance test.
- CrossWire OSIS source equivalence to every independent CCEL historical transcription or printed edition; only the exact CrossWire 2.2 source is the asserted target.

These are **documented limits**, not observed source defects. The project must not silently change authorial prose, insert duplicate chapter introductions, remove notes or add special-case UI workarounds to manufacture a frontend test success. A later reproducible failure must be investigated as either a source/address problem or a reader-specific rendering/navigation issue.

## Release gate interpretation

The above is **sufficient technical reader evidence for a first privately reviewed release candidate**, given the complete independent native/source integrity and preserved editorial structures. Additional manual clicked-link and visual checks are desirable QA follow-ups, not automatic evidence that the SWORD source is invalid or that a full reconstructed module must be withheld indefinitely. However an actual newly reproduced high-severity content-loss or wrong-verse problem discovered before publication would block publication and must be fixed.

The owner's official CrossWire MHC 2.2 Public Domain licensing decision is recorded separately. **Explicit owner release/merge authorization, latest-main integration and final reproducible package verification remain mandatory** before public release.
