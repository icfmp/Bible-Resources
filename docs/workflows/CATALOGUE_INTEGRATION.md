# Integrate Bible Resources into a SWORD-compatible application

Bible Resources publishes **curated, rights-reviewed resources** through an
ordinary, versioned **static HTTPS JSON catalogue** and a standard SWORD file
repository. It is not an API requiring authentication, and it is not a mirror
of every original CrossWire/eBible/AndBible module.

This is a **publisher-side data contract**. Applications are free to build
their own download UI, offline cache, install/update flow and reader interface.

## 1. Find the current catalogue

```http
GET https://icfmp.github.io/Bible-Resources/catalog/v1/catalog.json
```

- Response: UTF-8 JSON object, `schema_version: 1` and `modules: []`.
- No token, credentials, API key, query string or pagination is required.
- `modules` contains only **currently approved, redistributable** curated
  resources. A missing resource must not be inferred to be uninstalled.
- GitHub Pages serves the latest successful build of protected `main`. A CI
  success is **not** proof that every user can reach the public site.
- The address is a *current-version feed*, not an archive of historic versions
  or a request for automatically installing or updating anything.

Inspect it directly:

```sh
curl -fLsS https://icfmp.github.io/Bible-Resources/catalog/v1/catalog.json \
  | python3 -m json.tool
```

## 2. Read a module entry

The example below is intentionally abbreviated: the public catalogue also
includes full, potentially long Markdown descriptions and their provenance.

```json
{
  "schema_version": 1,
  "repository": "Bible Resources",
  "repository_url": "https://icfmp.github.io/Bible-Resources/",
  "modules": [
    {
      "id": "lsg-1910",
      "sword_id": "BRLSG1910",
      "canonical_edition_id": "louis-segond-1910-ebible",
      "title": {"fr": "Louis Segond 1910", "en": "Louis Segond 1910"},
      "category": "bible",
      "language": "fr",
      "version": "0.1.0",
      "versification": "Segond",
      "edition": "reader_optimized",
      "download": {
        "url": "https://icfmp.github.io/Bible-Resources/sword/packages/BRLSG1910.zip",
        "sha256": "f3f74a1016f708e10263b5628e606a73b727c0e80fbb7e131d195c4b11d86c51",
        "size_bytes": 4042088
      },
      "profiles": {
        "fr": {
          "revision": "2026-11-10.1",
          "approved_at": "2026-11-10",
          "format": "markdown",
          "short_markdown": "### Louis Segond 1910\n\n...",
          "long_markdown": "### Bible Louis Segond 1910\n\n...",
          "evidence_urls": {
            "curated_release": "https://github.com/icfmp/Bible-Resources/releases/tag/lsg-0.1.0"
          }
        }
      }
    }
  ]
}
```

The example represents the **currently published LSG 0.1.0**. Do not copy its
checksum or file size into application code: always obtain them from the
catalogue response at the moment of download.

| Field | How to use it |
| --- | --- |
| `schema_version` | Check support for `1` before interpreting module entries. Unknown incompatible schema versions must not be guessed. |
| `modules[].id` | Bible Resources' curated entry identifier. |
| `canonical_edition_id` | Identity of the reviewed underlying edition/lineage; not by itself a safe installed-module replacement key. |
| `sword_id` | Actual SWORD module identifier in the installed `.conf` and SWORD library. |
| `category`, `language`, `title` | Resource type, BCP-47-like source language tag and localized display names. A translation title is not necessarily available in every UI language. |
| `version` | Curated **module release version**; matches the embedded SWORD `.conf` `Version`. |
| `edition` | `faithful` or `reader_optimized`: provenance of the reviewed resource, not a quality rating. |
| `versification` | Declared SWORD versification; do not assume the same keys across different systems or translations. |
| `download.url` | HTTPS ZIP containing a normal SWORD module layout. |
| `download.sha256`, `size_bytes` | Exact expected ZIP bytes, **not** the source archive or a GitHub Release asset. |
| `profiles` (optional) | Locale-keyed, separately approved resource descriptions. Omitted for resources without an approved profile. |

Additional fields may be added compatibly under v1. Readers should ignore
unrecognized optional fields, but never bypass the required download checks.

## 3. Display approved descriptions

When `profiles` exists, select a locale (e.g., `fr`) and show
`short_markdown` in a library/list card; `long_markdown` can power a
dedicated details screen. Both are **Markdown**, not HTML or SWORD/OSIS
Scripture text. Use a safely configured Markdown renderer; do not execute
untrusted HTML/JavaScript embedded in Markdown or silently alter the Bible
module.

The same locale profile currently includes:

- `revision`, `approved_at`, `approved_by`, `approval_url`: separate
  editorial description history and review trail.
- `source_path`, `source_git_blob_sha1`: link to the exact source
  documentation revision (Git blob identity, **not** the SWORD archive hash).
- `format: "markdown"` and `evidence_urls`: display format and documented
  source references, including text-critical cautions where applicable.

A profile change may update `revision`, `short_markdown` or
`long_markdown` **without changing the SWORD `version` or ZIP bytes**.
Applications should refresh descriptive metadata independently of installed
resources. Do not treat a profile revision as a Bible text update. Other
resource locales and profiles may be absent; provide a normal title fallback
from `title`.

## 4. Download and verify a module

A client should perform these steps in order:

1. Fetch the catalogue over HTTPS, parse it, and choose the intended approved
   module. Do not equate matching titles with matching editions.
2. Fetch `download.url` over HTTPS into a temporary file, respecting
   reasonable size limits and network errors.
3. **Before installing**, compare the actual downloaded file's byte size
   with `download.size_bytes` and its SHA-256 digest with
   `download.sha256`. On mismatch, discard the file; do not silently
   install or retry using a stale, previously accepted digest.
4. Inspect the ZIP safely: reject absolute paths, `..` traversal,
   symlinks, duplicate member paths and unexpected layout; limit extraction
   sizes. Normal packages contain `mods.d/<module>.conf` and
   `modules/...`. Do not overwrite an unrelated installed module.
5. Verify the SWORD module ID, declared versification, language and
   `.conf` `Version` before completing a staged installation using
   standard SWORD mechanisms. Preserve user annotations and an existing
   version until the candidate has passed checks.
6. Handle unavailable/invalid catalogue responses as an **unknown network or
   feed state**, not as instructions to delete installed resources.

A minimal, **download-only** Python example (it does not extract or install
anything):

```python
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

CATALOGUE = "https://icfmp.github.io/Bible-Resources/catalog/v1/catalog.json"
with urlopen(CATALOGUE, timeout=30) as response:
    catalogue = json.load(response)
if catalogue.get("schema_version") != 1:
    raise ValueError("Unsupported catalogue schema")

module = next(m for m in catalogue["modules"] if m["sword_id"] == "BRLSG1910")
download = module["download"]
if urlsplit(download["url"]).scheme != "https":
    raise ValueError("HTTPS download required")

# Example only: consumers should stage downloads with bounded size and
# an atomic final rename; never use this as a complete ZIP installer.
destination = Path("BRLSG1910.zip")
size = 0
digest = hashlib.sha256()
with urlopen(download["url"], timeout=60) as response, destination.open("wb") as out:
    while block := response.read(64 * 1024):
        size += len(block)
        if size > download["size_bytes"]:
            raise ValueError("Download exceeds declared size")
        digest.update(block)
        out.write(block)

if size != download["size_bytes"] or digest.hexdigest() != download["sha256"]:
    destination.unlink(missing_ok=True)
    raise ValueError("Download failed integrity verification")
print("Verified download:", destination)
```

The snippet intentionally stops **before extraction or installation**.

## 5. Alternatively use the standard SWORD repository

Bible Resources also generates an ordinary SWORD repository from the same
approved source modules:

- `https://icfmp.github.io/Bible-Resources/sword/mods.d.tar.gz`
- `https://icfmp.github.io/Bible-Resources/sword/mods.d/`
- `https://icfmp.github.io/Bible-Resources/sword/modules/`
- `https://icfmp.github.io/Bible-Resources/sword/packages/`

An existing SWORD-compatible reader can use the standard module metadata and
files. The JSON feed adds a structured discovery/update contract, checksums,
canonical edition IDs and separately approved reader descriptions. It does
**not** replace SWORD or invent a new Scripture data format.

## 6. Updates, caching and compatibility

- `/catalog/v1/catalog.json` describes the **current approved** release
  for each curated module, not its full history.
- `/sword/packages/<SWORD_ID>.zip` is a mutable *latest approved* package
  address. Download bytes may change **when an approved new version is
  released**. Always validate against the currently fetched catalogue.
- A change of `download.sha256` **without a curated version increment** is
  anomalous drift, not a safe update.
- A changed versification, module ID, absent entry, unavailable provider,
  or lower version does not authorize deletion/replacement.
- HTTP caching is allowed, but refresh catalogue metadata before considering
  a new download and handle stale/failed requests explicitly.
- Different upstream provider versions (CrossWire/eBible) are **not**
  comparable with Bible Resources curated versions.
- Only the module's rights-reviewed published materials are mirrored; don't
  infer redistribution permission for an unrelated original SWORD module.

See [the full v1 update protocol](CATALOGUE_UPDATE_PROTOCOL.md),
[resource profile editorial policy](RESOURCE_PROFILES.md),
[architecture](ARCHITECTURE.md) and [publication procedure](PUBLISHING.md).
Report integration problems via [GitHub issues](https://github.com/icfmp/Bible-Resources/issues),
including the exact catalogue schema, module ID, reader version and response
error (not private user data).
