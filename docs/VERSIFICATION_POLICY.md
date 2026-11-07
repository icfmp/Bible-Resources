# Official SWORD versification and intentionally absent verses

## Rule: use existing SWORD versifications, never one made-up system per Bible

SWORD's VerseMgr already provides a registry of canonical book/chapter/verse
systems. The supported set includes KJV, KJVA, NRSV, LXX, Vulg, Catholic,
MT/Leningrad and French Calvin, Darby_fr and Segond, among others.
Use the official **installed SWORD engine's actual supported registry** as
the authority. Do not declare a new system simply because a different
translation exists. Record and preserve each module's actual
\`mods.d/*.conf\` \`Versification\` value; never infer it from its language,
title or publisher.

Official reference: https://wiki.crosswire.org/Alternate_Versification

SWORD's tools include \`osis2mod -v11n\` for explicitly choosing a known
versification and \`emptyvss\` for enumerating empty entries according to
the module's own versification.

**No silent reference remapping**: when a Bible and commentary use different
SWORD systems (e.g. the Segond and KJV systems), verify each mapping through
an established canonical source and the SWORD verse engine. Unknown,
ambiguous or unsupported reference correspondences remain **unmapped** and
are flagged for review, not paired by approximate numerical proximity.
Validate book count/order, chapter maxima, verse maxima, headers/superscriptions
and ranges. Never append unexpected content to a neighboring canonical verse
without explicit review: the standard importer can have that behavior for
out-of-range verses (see CrossWire's documentation).

## Three different reasons a verse may be absent

1. **Editorially intentional absence**: the actual translation/edition
   deliberately omits a verse or moves it to the apparatus because of a
   documented textual choice. Preserve the reference slot *if the module's
   selected SWORD v11n includes that verse*, preserve the absence of body
   text, and attach a **clearly attributed editorial note** explaining the
   edition's decision. A note must be based on verifiable edition/source
   evidence, not an invented explanation.
2. **Versification difference**: the passage is numbered or placed
   differently in another v11n. Record the mapping if verified, but **do not**
   create a bogus blank verse in the module or hide content to imitate a
   different edition. The selected v11n remains authoritative.
3. **Accidental omission or corrupted import**: a verse is missing despite
   appearing in the authoritative source. Stop, give provider/module/
   book/chapter/verse and original file + line if available, and repair
   deterministically with review. Never label corruption as a critical-text
   omission.

CrossWire documents that an actually empty first verse of a chapter may
make some SWORD frontends unable to select that chapter. It suggests a
minimal placeholder or an empty \`<seg/>\` as possible workarounds:
https://wiki.crosswire.org/OSIS_Bibles#Empty_verses

For Bible Resources, prefer a **semantic empty slot + separate editorial
note**, not invented Scripture. The precise standard OSIS encoding and
SWORD display behavior must be proven on an actual test module with
\`osis2mod\`, \`emptyvss\`, \`diatheke\`, and the Bible GTK reader (including
the first verse of a chapter), **before** registering a production
normalization rule. A visually empty verse may still have a deliberate
structural marker. If \`<seg/>\` or an inline note is discarded or displays
incorrectly, block that transformation until a compatible encoding is
verified. Do not ship a misleading literal ellipsis as Scripture.

## Diagnostics and release criteria

- Preserve the **actual** source reference, SWORD v11n, original text,
  translations, notes, Strong/morph and editor attributions.
- Treat any \`emptyvss\` report as an **audit candidate**, never definitive
  proof of a textual-critical decision.
- For every confirmed intentional omission, record source edition, verse
  reference, supporting evidence URL/page, exact editorial note text,
  reviewer and chosen OSIS encoding.
- Verify by compiled-module round trip that the verse slot survives, the
  nearby verses are unchanged and the note remains attached to the
  correct location.
- Check parallel display and commentary synchronization against verified
  reference mappings; missing mappings must not silently attach a
  commentary to the wrong verse.

This is an editorial and QA policy. **No automatic blank-verse insertion,
note creation or cross-versification mapping is implemented yet.** See the
Segond + MHC pilot in [PILOT_SEGOND_MHC.md](PILOT_SEGOND_MHC.md).
