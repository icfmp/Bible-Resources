# SWORD OSIS option filters: prepublication guard

The `GlobalOptionFilter` setting is a repeated key in SWORD `.conf` files.
The ordinary metadata parser retains only its first value, so a broken
second (or later) option could previously pass unnoticed.

The generic `scripts/sword_option_filters.py` guard reads every declaration
and compares its name and source-markup family against the registered
[CrossWire SWMgr option filters](https://www.crosswire.org/sword/apiref/swmgr_8cpp_source.html).
An unregistered or duplicated option stops validation and therefore
publishing. Update the review list against the exact stable SWORD version
when adding a newly supported filter; do not add translation-specific bypasses.

### Two distinct reference issues

- **Configuration:** `OSISXRefs` is not registered by stable libSWORD;
  `OSISScripref` is the valid filter for OSIS cross-references. LSG was
  fixed in 1.0.1, but the currently published Darby 0.1.1 still has the
  invalid setting. See [#553](https://github.com/icfmp/Bible-Resources/issues/553).
- **Reader rendering:** with Cross-references explicitly On, the
  `SWModule::stripText()` path may still expose nested literal OSIS
  reference tags even with `OSISScripref` configured correctly. This
  is a separate unresolved [#549](https://github.com/icfmp/Bible-Resources/issues/549).
  Do not flatten original cross-reference notes or delete their machine
  destinations to make a plain-text reader look cleaner.

### Distinct preservation checks

Config validation is necessary but does **not** prove that all source
`osisRef` targets remain addressable in the compiled SWORD module or
that each reader renders them correctly. The full source-to-native
reference inventory and an actual-reader Off/On matrix remain separate
work items under [#28](https://github.com/icfmp/Bible-Resources/issues/28)
and [#553](https://github.com/icfmp/Bible-Resources/issues/553).

Never change historical published module tags or original Bible text
when repairing a rendering filter. A corrected Darby binary distribution
requires an independently verified new version and publication approval.
