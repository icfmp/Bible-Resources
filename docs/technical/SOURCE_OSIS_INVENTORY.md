# OSIS authorial numbered-key inventory

**Purpose:** produce an independent text-free inventory of numbered verse identities from a separately validated OSIS Bible. Accepts single unambiguous `book.chapter.verse` identifiers, including container `verse` and paired `sID/eID` milestones.

## Run

First validate the exact OSIS file against the official, pinned schema and reviewed source policy:

```sh
mkdir -p /tmp/source-proof
python scripts/source_osis_inventory.py \
  --source-osis /private/validated-source.osis.xml \
  --keys-output /tmp/source-proof/source-keys.txt \
  --report /tmp/source-proof/source-keys-audit.json
```

Use new output paths. The receipt binds the complete ordered source keys and structural counts to that input OSIS SHA-256. If the publisher gave USFM/USFX, **its provenance and conversion to this OSIS must be audited separately**; simply having OSIS does not establish the original edition.

## Reject rather than repair

Invalid XML, DTDs, out-of-order/duplicate keys, unmatched milestones, ambiguous multi-verse identities, unexpected nested books/verses, symlinks/unsafe outputs, oversized data and unsupported book identifiers must block. A numeric gap **does not** authorize inserting Scripture. Preserve source-only books and verse-zero/introduction structures for subsequent comparison.

This output includes reference IDs and counts, not Scripture, notes, private source prose or native compiled data.

## Scope boundary

Pass the source keys unchanged to [stable reference comparison](STABLE_SWORD_REFERENCE_AUDIT.md) **only after** collecting the real installed SWORD native registry and occupied-key inventory using [native inventory](NATIVE_SWORD_INDEX_INVENTORY.md). This tool does not inspect native SWORD, verify source-to-compiled text or annotations, approve rights or release anything. Follow [production](../PRODUCTION_PIPELINE.md) and the cross-edition audit issue [#28](https://github.com/icfmp/Bible-Resources/issues/28).
