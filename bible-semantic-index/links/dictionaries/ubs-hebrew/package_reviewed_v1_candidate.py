#!/usr/bin/env python3
"""Build a reproducible, NONPUBLISHED UBS Hebrew BSI v1 release candidate.

Source-pin the entire index and package original identifier crosswalks only.
No source dictionary articles, Macula TSV/text or editorially inferred senses
are added. Explicit publication approval is a separate gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

NAME = "BSI-UBSHebrew-0.9.4-v1.0-rc2"
PREFIX = NAME + "/"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
CC_BY_SA = "https://creativecommons.org/licenses/by-sa/4.0/"
UBS_REV = "a15a96cfaa4ca18a6c0339016645ba1e534db3c8"
MACULA_REV = "47db250bd55d0d8577f2a94fba114ef16c35b23c"
MARKER = "editorially_reviewed_original_wlc_headword_only"

README = """# UBS Hebrew lexical crosswalk for Bible Semantic Index

Review candidate: v1.0-rc2. **Not published or approved as a release.**

Source-anchored, offline lexical headword lookup connecting original MACULA
Hebrew WLC word IDs to UBS Dictionary of Biblical Hebrew 0.9.4 (EN/FR).
Every original source word-ID and original Hebrew/Aramaic source spelling is
preserved. Source lookup must use the exact MACULA word ID, original lemma,
original SDBH, full Strong annotation, and H/A language. Wrong-source
lookups fail closed. Any remaining ambiguous/unsupported word is unlinked.

This package includes no original MACULA corpus TSV, biblical verses,
UBS dictionary prose or translations. The included index is an
entry/headword candidate crosswalk, not a Hebrew Bible or dictionary.

Data use: read index.json with the audited matching source editions and
use the word-aware lookup policy documented in the source repository.
A generic lookup based on Strong alone is less precise and cannot use
these independently reviewed word-ID-only candidate links.

* 248,680 selected original lexical WLC word occurrences (unchanged).
* 240,371 candidate occurrences with a UBS headword.
* 242,747 original UBS 0.9.4 indexed-headword-scope denominator.
* 99.022% coverage of that edition-specific scope, NOT semantic accuracy
  or full Hebrew vocabulary coverage.
* 275 independently reviewed WLC word-specific entry-only links (273 baseline
  + 2 independently substantiated exact-source lexical identities).
* 24 further individually audited original words retain explicit no-links.
* Zero editorially invented contextual UBS sense IDs.
* One ambiguous reviewed word deliberately not linked in 2 Sam. 21:22.
* All original editorial exclusions, source rights and homograph warnings
  must still be respected.

Do not publish this RC as v1.0 or integrate it into the Bible application
before separate editorial, legal/source-rights and consumer approval.

Source and reproducible verification:
https://github.com/icfmp/Bible-Resources/tree/main/entity-index/links/dictionaries/ubs-hebrew
"""

ATTRIBUTION = """# Attribution, upstream editions, license and changes

Derived index: Bible Semantic Index / Bible Resources, original word-level
lexical crosswalk. Data adaptation distributed upon approval under Creative
Commons Attribution-ShareAlike 4.0 International:
https://creativecommons.org/licenses/by-sa/4.0/

Original UBS Dictionary of Biblical Hebrew, edition 0.9.4 in English
and French, copyright United Bible Societies; published as open data:
https://github.com/ubsicap/ubs-open-license
Exact revision: a15a96cfaa4ca18a6c0339016645ba1e534db3c8
Source-documented license: CC BY-SA 4.0.
The original UBS lexical articles, translations and definitions are not
redistributed in this index. MainId and source sense-ID provenance retained.

Original MACULA Hebrew WLC linguistic word annotations:
https://github.com/Clear-Bible/macula-hebrew
Exact revision: 47db250bd55d0d8577f2a94fba114ef16c35b23c
Original dataset license: CC BY 4.0.
Exact source word identifiers, source lemma/Strong/SDBH and references
are used to build and independently verify the reviewed lexical links.
The complete WLC TSV, original biblical text and gloss sentences are not
redistributed in this package.

Changes relative to original datasets: verified original word-ID keyed,
headword-only crosswalk; conservative original Strong-family checks;
quarantined misleading matching SDBH IDs from unrelated editions; 275
independently documented original source-word UBS headword decisions;
source-attested exclusions retained; no inferred contextual UBS senses.

Additional reviewed original WLC word-specific headword links: Joshua 19:13
Rimmon/Rimmono and 1 Samuel 17:39 יאל/H2974; no other homonym or
source text, Strong code or UBS lexical sense is changed.

No original publishers, authors or organizations endorse this adaptation.
Retain this attribution and the ShareAlike license when redistributing.
"""

LICENSE = """Bible Semantic Index (BSI) UBS Hebrew 0.9.4 lexical crosswalk.

Data adaptation: CC BY-SA 4.0 International.
License URI: https://creativecommons.org/licenses/by-sa/4.0/

Original UBS Dictionary of Biblical Hebrew 0.9.4: CC BY-SA 4.0;
original MACULA Hebrew WLC dataset: CC BY 4.0. This derivative license
does not claim ownership of either original dataset, their text, or
separately copyrighted underlying Bible translations.
See ATTRIBUTION.md for exact source editions, rights and changes.
"""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_json(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def verify_candidate(index: dict, raw: bytes, manifest: dict) -> None:
    editorial = index.get("editorial_candidate") or {}
    scope = index.get("coverage_scope") or {}
    if (index.get("format") != "bsi-ubs-hebrew-lexical-crosswalk"
            or index.get("schema_version") != 1
            or index.get("languages") != ["en", "fr"]
            or index.get("license") != "CC BY-SA 4.0"):
        raise ValueError("Unsupported original indexed dictionary profile")
    if (manifest.get("schema_version") != 1
            or manifest.get("status") != "private_v1_candidate_not_published_or_approved"
            or manifest.get("release_approved") is not False
            or editorial.get("status") != manifest["status"]):
        raise ValueError("This candidate is not cleared for public release")
    if raw != canonical_json(index):
        raise ValueError("Noncanonical candidate serialization")
    if sha256(raw) != manifest["candidate_index_sha256"]:
        raise ValueError("Candidate bytes do not match independently pinned hash")
    if (index["dictionary"]["revision"] != UBS_REV
            or index["dictionary"]["edition"] != "0.9.4"
            or index["macula"]["revision"] != MACULA_REV
            or manifest["source_editions"] != {
                "ubs_revision": UBS_REV, "macula_revision": MACULA_REV
            } or editorial.get("index_source_revisions") !=
                manifest["source_editions"]):
        raise ValueError("Source or dictionary edition drift")
    if (scope.get("original_lexical_source_occurrences") != 248680
            or scope.get("linked_occurrences") != 240373
            or scope.get("indexable_denominator") != 242747
            or scope.get("indexable_unresolved") != 2374
            or scope.get("coverage_pct") != 99.022
            or manifest.get("original_source_linked_lexical_occurrences") != 240098
            or manifest.get("new_entry_only_word_links") != 275
            or manifest.get("original_source_words_left_unlinked_by_review") != 1
            or manifest.get("final_original_source_word_approvals") != 2
            or manifest.get("remaining_last_original_word_abstentions") != 24
            or manifest.get("previous_candidate_index_sha256") !=
               "7c2e386a07d0dede3bcb836f64db66a5779b7e4c9d8f6d20ec76e06d156c1b35"):
        raise ValueError("Candidate source population/coverage changed")
    if (editorial.get("original_index_left_unchanged") is not True
            or editorial.get("source_corpus_left_unchanged") is not True
            or editorial.get("new_headword_only_wlc_word_ids") != 275
            or editorial.get("additional_final_source_specific_approvals") != 2
            or editorial.get("remaining_source_specific_unlinked_words") != 24
            or editorial.get("inferred_contextual_sense_ids") != 0
            or manifest.get("contextual_sense_ids_inferred") != 0):
        raise ValueError("Unreviewed source word or contextual sense leaked into candidate")
    word_links = index.get("by_macula_word") or {}
    reviewed = {wid: entry for wid, entry in word_links.items()
                if entry.get("match_type") == MARKER}
    if (len(reviewed) != 275
            or index["coverage_with_word_ids"].get("additional_entry_only_links") != len(word_links)):
        raise ValueError("Word link inventory mismatches reviewed source ledger")
    for wid, record in reviewed.items():
        if (not wid.startswith("o") or not record.get("entry_id")
                or record["entry_id"] not in index["by_entry_strong_family"]
                or record.get("lang") not in ("H", "A")
                or not record.get("lemma") or not record.get("strong")
                or not record.get("reference")
                or "sense_id" in record or "LEXID" in record):
            raise ValueError("Unsafe source-reviewed headword record " + wid)
    if (index["coverage_with_word_ids"].get("word_aware_entry_links") != 268431 + 275
            or index["coverage_with_word_ids"].get("sense_links") != 30492):
        raise ValueError("Original indexed UBS word or sense link count changed")
    if (manifest.get("original_index_and_source_unchanged") is not True
            or not isinstance(editorial.get("original_index_sha256"), str)
            or len(editorial["original_index_sha256"]) != 64
            or any(ch not in "0123456789abcdef" for ch in editorial["original_index_sha256"])):
        raise ValueError("Original source index provenance missing")


def payload(index_raw: bytes, manifest: dict) -> dict[str, bytes]:
    provenance = {
        "schema_version": 1,
        "type": "bsi_ubs_hebrew_lexical_headword_crosswalk",
        "version": "1.0-rc2",
        "release_status": "private_candidate_not_approved_or_published",
        "edition": "UBS Hebrew 0.9.4",
        "source_editions": manifest["source_editions"],
        "license": "CC BY-SA 4.0",
        "source_original_lexical_occurrences": 248680,
        "linked_original_occurrences": 240373,
        "indexed_headword_scope_denominator": 242747,
        "indexed_headword_scope_coverage_pct": 99.022,
        "reviewed_word_specific_entry_only_links": 275,
        "last_word_specific_additional_approvals": 2,
        "retained_unlinked_original_final_word_reviews": 24,
        "inferred_contextual_ubs_sense_ids": 0,
        "original_index_sha256": json.loads(index_raw)["editorial_candidate"]["original_index_sha256"],
        "candidate_index_sha256": sha256(index_raw),
        "publication_authorized": False,
    }
    contents = {
        "index.json": index_raw,
        "README.md": README.encode("utf-8"),
        "ATTRIBUTION.md": ATTRIBUTION.encode("utf-8"),
        "LICENSE.txt": LICENSE.encode("utf-8"),
    }
    provenance["files"] = {
        key: {"sha256": sha256(data), "bytes": len(data)}
        for key, data in sorted(contents.items())
    }
    contents["manifest.json"] = canonical_json(provenance)
    return contents


def create_archive(destination: Path, files: dict[str, bytes]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w",
                         compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zip:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(PREFIX + name, FIXED_TIME)
            info.create_system = 3
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zip.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED,
                         compresslevel=9)
    with zipfile.ZipFile(destination) as zip:
        names = zip.namelist()
        if names != [PREFIX + name for name in sorted(files)]:
            raise ValueError("Nondeterministic archive entry ordering")
        for name, raw in files.items():
            if zip.read(PREFIX + name) != raw:
                raise ValueError("Archive source bytes changed during packing")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("index", "release_manifest", "output"):
        p.add_argument("--" + name, required=True, type=Path)
    args = p.parse_args()
    index_raw = args.index.read_bytes()
    index = json.loads(index_raw)
    manifest = json.loads(args.release_manifest.read_text(encoding="utf-8"))
    verify_candidate(index, index_raw, manifest)
    create_archive(args.output, payload(index_raw, manifest))
    digest = sha256(args.output.read_bytes())
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(
        digest + "  " + args.output.name + "\n", encoding="ascii"
    )
    print("UBS_V1_NONPUBLISHED_RELEASE_CANDIDATE", json.dumps({
        "artifact": args.output.name, "sha256": digest,
        "candidate_index_sha256": manifest["candidate_index_sha256"],
        "release_approved": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()

