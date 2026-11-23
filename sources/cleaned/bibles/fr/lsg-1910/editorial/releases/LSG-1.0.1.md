# Louis Segond 1910 — Bible Resources 1.0.1

## Cross-reference rendering hotfix

Restores the registered libSWORD configuration filter OSISScripref instead of the invalid OSISXRefs introduced in 1.0.0. The normal cross-references-disabled mode no longer leaks literal reference XML into plain Bible reading. The exact 1.0.0 Bible OSIS source, all six native zText binary members, all 31,170 source verse IDs, 31,169 native verse bodies and all 9,751 notes are unchanged.

**Known limitation:** when a reader explicitly turns ON the SWORD Cross-references global option, libSWORD stripText can still expose note-internal XML reference markup. The standard OFF/default mode is tested through every native verse; this patch does not claim full XML-free stripText under an explicit ON setting. The Bible application source code is not modified.

This release retains all 1.0.0 editorial improvements, 12 reviewed citation corrections, 3 introduction decisions, 9,440 linked reference notes, and the documented Marc 10.53 Segond native index limitation. No source-absent verse has been introduced. See the unchanged 1.0.0 release notes for original source/rights.

All previous public release assets and hashes remain immutable.
