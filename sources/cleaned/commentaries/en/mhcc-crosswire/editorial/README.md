# Matthew Henry Concise Commentary — editorial decisions

**Release:** `MHCC` 0.1.2 (classic English), derived from CrossWire MHCC 2.0. Not the complete MHC commentary.

## Decisions worth preserving

- The maintained OSIS is a **native-attested reconstruction** of the approved 0.1.1 SWORD module, **not** the recovered original CrossWire authoring XML. Never cite it as the original author's unpublished XML.
- **24 reviewed native navigation aliases** make 17 existing commentary sections reachable. They do not create 24 new authorial comments.
- Two historical 0.1.1 source corrections: Ezekiel 3 malformed reference `3:12–2` → `3:12–21`; 1 Chronicles 7 `Zebulun or Dn` → `Zebulun or Dan`. 0.1.2 restores the attested Genesis 5:25–32 lacuna and normalizes redundant book milestones and two missing chapter end markers. No general authority to revise prose.
- Chapter-only commentary remains one authorial unit. A reader may expose it throughout the chapter without duplicating the source prose.
- SWORD ID `MHCC` collides with CrossWire's own module name; old `BRMHCC` installs require deliberate handling.

## Source of truth

| Need | Record |
| --- | --- |
| Reconstructed master, exact claims and SHA | [Cleaned source manifest](../CLEANUP_MANIFEST.json) |
| Approved corrections and alias list | [Rebuild manifest](../../../../../../config/commentary-rebuilds/mhcc-crosswire.json) |
| Release, rights and reader limitations | [0.1.2 release record](releases/MHCC-0.1.2.md) |
| Native-entry evidence | [Native source audit](../../../../../../modules/mhcc-crosswire/SOURCE_AUDIT.json) |
| Historical why/alternatives | [Editorial disposition](evidence/release-0.1.1/0.1.1-editorial-disposition.md), only when investigating a disputed decision |
| Earlier untouched stock edition | [0.1.0 release](releases/MHCC-0.1.0.md) |

For why a decision was made, consult the [evidence map](evidence/README.md). For the original-stock comparison, consult the [short historical evidence index](evidence/stock-research/README.md) before opening individual receipts. The optional ongoing [section/source research #274](https://github.com/icfmp/Bible-Resources/issues/274) does not retroactively revoke the separately approved 0.1.1 release. Do not reinterpret old `DRAFT` statuses as the present published edition state.
