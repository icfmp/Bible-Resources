# OSIS source → native SWORD index verification

The active authoring source is the **reviewed cleaned OSIS master**, not an
original-USFX stock-reuse experiment. Compare that exact source against a
separately built, isolated SWORD candidate before treating its key inventory
as evidence. See the [production pipeline](../PRODUCTION_PIPELINE.md).

## Required evidence

1. Pin the original and cleaned OSIS edition, approved transformation record,
   source SHA-256, canon, versification and rights. Do not treat a valid source
   file as proof of correct edition identity or legal redistribution.
2. Run `scripts/guard_osis.py` and `scripts/source_osis_inventory.py` against
   the actual authorial source to enumerate all populated keys and intentional
   verse omissions.
3. Independently compile and inspect the actual candidate with
   `scripts/sword_native_index.cpp` and
   `scripts/sword_native_inventory.py`, ensuring correct SWORD module,
   versification, intros, empty native slots and occupied entries.
4. Use `scripts/publisher_osis_sword_candidate.py` for the maintained private
   source-to-compiled candidate checks. Compare every authored address to its
   independently read native address. Do not infer text from an addressable
   but empty SWORD slot; never reconstruct a missing source verse.
5. Record exact key equality and each reviewed conversion/reindex exception
   separately. Native key equality cannot establish text, notes, reference
   destinations, chapter introductions, poetry or paragraph fidelity.

The report must retain exact input hashes and source versus native key counts,
including omitted, source-only, native-only, intro and TOP categories. Unresolved
differences are blocked rather than silently accepted.

## Publication boundary

The index is **one** production gate. Independently verify source-to-native
wording, punctuation, notes/callers, annotated references, full editorial
structure and actual reader rendering. An allowed nontrivial versification
mapping requires documented editorial evidence; do not hardcode an exception
simply to satisfy a test. Rights, editorial sign-off and publication approval
remain distinct decisions.

This procedure replaces the former stand-alone
`scripts/source_native_index_audit.py` experiment. Historical receipts and
the original implementation remain recoverable through Git history; the old
script is not a second active production entrypoint.
