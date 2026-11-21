# MHCC — source-to-standard-OSIS reconstruction proof boundary

**Historical technical proof.** An OSIS reconstruction was needed because the exact upstream CrossWire authoring OSIS was unavailable. The [reviewed cleaned-source manifest](../../../CLEANUP_MANIFEST.json) explicitly says the final OSIS is a *native-attested reconstruction*, **not** a byte-exact recovery of the CrossWire original.

## What the original native readback established

Original CrossWire MHCC 2.0: **29,975 occupied records**, comprising **28,718 K**, **1,255 I** and **two opaque TOP** entries. There were **5,302 distinct, nonopaque native raw bodies**, many reused through standard SWORD links.

A source-to-standard-`osis2mod` trial confirmed that native bodies can be represented using standard OSIS commentary sections, with their visible wording and internal tag/attribute relationships preserved under controlled comparisons. It did **not** establish identical serialized XML bytes or independent historical print-edition identity.

The standard compiler may add `div` wrappers, restructure milestones and change raw XML while retaining meaning; therefore **raw fragment SHA equality is not the only acceptance criterion**. Exact text, punctuation, notes, literal targets, original section coverage, introduction ownership and linked native identity require distinct checks.

## What was accepted later

The [MHCC 0.1.1 source manifest](../../../CLEANUP_MANIFEST.json), [approved correction plan](../../../../../../../../config/commentary-rebuilds/mhcc-crosswire.json), [native source audit](../../../../../../../../modules/mhcc-crosswire/SOURCE_AUDIT.json) and [release receipt](../../releases/MHCC-0.1.1.md) supersede these pre-release trials. The final output includes **24 reviewed aliases and two attested corrections**; neither may be used to reinterpret the original source as byte-identical.

Original pilot runs and exact intermediate SHA values remain in this document's Git history and [issue #274](https://github.com/icfmp/Bible-Resources/issues/274). A future reconstruction must run its own full-corpus checks rather than inherit an old green pilot.
