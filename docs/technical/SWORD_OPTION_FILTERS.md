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
  fixed in 1.0.1; Darby 0.1.2 repairs the invalid setting in the prior
  immutable 0.1.1 configuration. See [#553](https://github.com/icfmp/Bible-Resources/issues/553).
- **Reader rendering:** with Cross-references explicitly On, the
  `SWModule::stripText()` path with an unconfigured markup manager may expose
  nested literal OSIS reference tags even with `OSISScripref` configured correctly. This
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

The presence of an invalid option in any already approved module is a blocking defect, not an exception to this rule. A repair must be staged with a new version before the check can be merged to the publication branch.

The gate rejects an invalid filter before publication; a successful metadata test alone is not release authorization.

### Actual rendering versus internal markup

The shared `sword_native_render.cpp` probe explicitly constructs a standard
`MarkupFilterMgr(FMT_HTMLHREF)` before calling `renderText()`. A bare `SWMgr`
can return internal OSIS and must not be described as HTML output. The audit
checks every populated numbered verse in four separately verified option
combinations, distinguishes literal OSIS elements from valid HTML attributes,
and can compare the prior immutable package under the same render settings.
The Darby 0.1.2 and LSG 1.0.2 audits had zero residual OSIS marker detections
under HTMLHREF. Earlier unconfigured-manager limitations remain tracked in
#549; engine output is not proof of every graphical client's behavior.
