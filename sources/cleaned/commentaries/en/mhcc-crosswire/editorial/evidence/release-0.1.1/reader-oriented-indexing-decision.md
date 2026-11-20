# MHCC — passage indexing without duplicated commentary

**Decision:** make an existing commentary section discoverable from every verified covered verse **when SWORD supports this without altering its authored identity**. This was implemented for the reviewed 24 aliases in [MHCC 0.1.1](../../releases/MHCC-0.1.1.md). It is not a mandate to restructure other editions.

## Why

An authorial unit may cover one verse, a contiguous range, distinct disjoint ranges or an entire chapter. One native SWORD key does **not** by itself define the true section extent. Conversely, a citation inside the prose is **not** automatically a section boundary.

Do not create individual verse prose from a chapter-wide comment. Two independent sections with identical words remain distinct; raw-text equality is not evidence that they are the same comment.

## Required validation of each alias

1. Establish source-attested original section identity and exact contiguous/discontinuous scope, including adjacent independent comments.
2. Compare native key occupancy against the actual SWORD versification and reject any collision with a different authored entry.
3. Link verified addressable keys to the **same original section body**; do not duplicate its text.
4. Read back all native keys, individual chapter introductions and opaque records and compare exact source/compiled identities.
5. Test both a single selected verse and sequential chapter reading: a client should ideally display a linked section once, but **source preservation takes priority over client-specific repetition**.
6. Record approved mappings and rollback in the [source-bound manifest](../../../../../../../../config/commentary-rebuilds/mhcc-crosswire.json).

## Known independent client limitation

Nonadjacent linked identities and deduplication of a comment spanning disjoint ranges may need specific client support. [Bible issue #267](https://github.com/icfmp/Bible/issues/267) tracks that display behavior. **Do not rewrite SWORD prose to compensate for an unsupported reader deduplication feature.**

The original evidence and reviewed direction are traceable in [issue #274](https://github.com/icfmp/Bible-Resources/issues/274). This document records the substantive decision, not successive candidate tests or private package hashes.
