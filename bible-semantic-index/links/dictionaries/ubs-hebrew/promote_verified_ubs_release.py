#!/usr/bin/env python3
"""Promote exact source-audited UBS v1.0-rc2 DATA to an authorized release ZIP.

The original technical RC2 and candidate index SHA-256 are frozen evidence.
Only public-distribution metadata is changed in the index. Source dictionaries,
Macula WLC, source-lexical links, Strong/SDBH, and lexical sense data are not
modified. The public ZIP is deterministic and has its OWN pinned SHA-256.

The script does not publish to GitHub; a protected-main workflow does so.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import zipfile
from pathlib import Path

TAG = "bsi-ubs-hebrew-v1.0.0"
FILE_NAME = "BSI-UBSHebrew-0.9.4-v1.0.0.zip"
PREFIX = "BSI-UBSHebrew-0.9.4-v1.0.0/"
RC_PREFIX = "BSI-UBSHebrew-0.9.4-v1.0-rc2/"
TIME = (1980, 1, 1, 0, 0, 0)
APPROVAL = "owner_authorized_for_stable_release_after_reviewed_ubs_v1_gates"
TECHNICAL_STATUS = "private_v1_candidate_not_published_or_approved"
PUBLISHED_STATUS = "released_source_audited_v1_0_0"
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
REVIEWED = "editorially_reviewed_original_wlc_headword_only"

README = """# Bible Semantic Index — UBS Hebrew lexical crosswalk v1.0.0

Published, independently source-attested offline Hebrew/Aramaic original
word-ID to UBS Hebrew Dictionary 0.9.4 lexical headword crosswalk.

**Separate from BSI v0.1.0 entity data and the Bible application.**
This is NOT a SWORD Bible/commentary, an original-language Bible text,
or a redistribution of original UBS dictionary articles and gloss prose.
A dictionary UI must obtain actual original source definitions from
their own duly licensed UBS edition. This package resolves lexical
HEADWORDS, not guaranteed contextual senses or historical identities.

The original MACULA WLC 475,911 word records were audited against the
exact original source edition. 248,680 words are in the selected lexical
source classes; of those, 240,373 source occurrences have a candidate UBS
headword, including 275 individually approved source-word-only links.
99.022% covers only the *242,747 WLC occurrences within this UBS 0.9.4
indexed-headword-inventory scope*. This does NOT claim 99.022% semantic
accuracy, all-language lexical completeness, or an inferred sense for
every linked word. The remaining 2,374 in-scope occurrences and 5,933
outside this edition's indexed-headword inventory are preserved as
explicitly unlinked source material, not guessed into matches.

Consumption: consult the index's source-edition metadata and pass the
exact original MACULA WLC word ID, original lemma, full Strong code,
original SDBH and H/A language into the source's word-aware lookup.
An ordinary Strong-only lookup cannot take advantage of the independently
reviewed word-ID-specific lexical distinctions.

This package has been independently source checked; it reuses a previously
verified technical candidate without changing any lexical links. For full
source review, limitations, source attestations and regeneration pipeline:
https://github.com/icfmp/Bible-Resources/tree/main/entity-index/links/dictionaries/ubs-hebrew

The source lexicon and WLC remain separately owned/licensed. Retain the
original publisher attribution and CC BY-SA 4.0 terms in this archive.
No original author or publisher has endorsed this adaptation.
"""

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encode(data) -> bytes:
    return (json.dumps(data, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def require_auth(approval, allow_missing_public_hash=False):
    if (approval.get("schema_version") != 1
            or approval.get("status") != APPROVAL
            or approval.get("release_tag") != TAG
            or approval.get("published") is not False
            or approval.get("requires_exact_verified_bytes") is not True
            or approval.get("exclude_original_ubs_dictionary_prose") is not True
            or approval.get("exclude_original_macula_biblical_text") is not True
            or approval.get("independent_bible_app_integration") is not True
            or not approval.get("owner_decision", "").strip()
            or not SHA256.fullmatch(approval.get("approved_private_index_sha256", ""))
            or not SHA256.fullmatch(approval.get("approved_technical_rc2_zip_sha256", ""))
            or approval.get("source_editions") != {
                "ubs_revision": "a15a96cfaa4ca18a6c0339016645ba1e534db3c8",
                "macula_revision": "47db250bd55d0d8577f2a94fba114ef16c35b23c",
            }
            or approval.get("original_lexical_source_occurrences") != 248680
            or approval.get("linked_source_occurrences") != 240373
            or approval.get("edition_indexed_headword_denominator") != 242747
            or approval.get("indexed_scope_coverage_pct") != 99.022
            or approval.get("original_word_specific_reviewed_links") != 275
            or approval.get("inferred_contextual_sense_ids") != 0):
        raise ValueError("Missing exact owner approval or source-pinned release scope")
    expected = approval.get("expected_public_release_zip_sha256")
    if expected is None and allow_missing_public_hash:
        return
    if not isinstance(expected, str) or not SHA256.fullmatch(expected):
        raise ValueError("Public release ZIP is not immutably SHA-256 authorized")


def verify_private_rc(raw: bytes, approval: dict):
    if digest(raw) != approval["approved_technical_rc2_zip_sha256"]:
        raise ValueError("Original independently audited technical RC2 ZIP changed")
    with zipfile.ZipFile(__import__("io").BytesIO(raw)) as archive:
        if archive.testzip() is not None:
            raise ValueError("Technical release ZIP has an invalid member CRC")
        required = {
            RC_PREFIX + name for name in
            ("index.json", "README.md", "ATTRIBUTION.md",
             "LICENSE.txt", "manifest.json")
        }
        if set(archive.namelist()) != required:
            raise ValueError("Original technical review ZIP members changed")
        files = {name: archive.read(RC_PREFIX + name)
                 for name in ("index.json", "README.md", "ATTRIBUTION.md",
                              "LICENSE.txt", "manifest.json")}
    technical = json.loads(files["manifest.json"])
    if (technical.get("version") != "1.0-rc2"
            or technical.get("release_status") !=
              "private_candidate_not_approved_or_published"
            or technical.get("publication_authorized") is not False
            or technical.get("source_editions") != approval["source_editions"]
            or technical.get("reviewed_word_specific_entry_only_links") != 275
            or technical.get("inferred_contextual_ubs_sense_ids") != 0
            or technical.get("candidate_index_sha256") !=
              approval["approved_private_index_sha256"]):
        raise ValueError("Original technical source candidate manifest changed")
    if any(
        technical["files"][name]["sha256"] != digest(data)
        or technical["files"][name]["bytes"] != len(data)
        for name, data in files.items() if name != "manifest.json"
    ):
        raise ValueError("Technical candidate member SHA-256 is invalid")
    original = json.loads(files["index.json"])
    if files["index.json"] != encode(original):
        raise ValueError("Uncanonical original review index")
    if (digest(files["index.json"]) != approval["approved_private_index_sha256"]
            or original["format"] != "bsi-ubs-hebrew-lexical-crosswalk"
            or original["schema_version"] != 1
            or original["dictionary"]["revision"] !=
                approval["source_editions"]["ubs_revision"]
            or original["macula"]["revision"] !=
                approval["source_editions"]["macula_revision"]
            or original["coverage_scope"]["linked_occurrences"] != 240373
            or original["coverage_scope"]["indexable_denominator"] != 242747
            or original["coverage_scope"]["indexable_unresolved"] != 2374
            or original["coverage_scope"]["coverage_pct"] != 99.022
            or original["coverage_with_word_ids"]["sense_links"] != 30492
            or original["editorial_candidate"]["status"] != TECHNICAL_STATUS
            or original["editorial_candidate"]["new_headword_only_wlc_word_ids"] != 275
            or original["editorial_candidate"]["inferred_contextual_sense_ids"] != 0):
        raise ValueError("Original indexed-source lexical evidence changed")
    if sum(x.get("match_type") == REVIEWED
           for x in original["by_macula_word"].values()) != 275:
        raise ValueError("Some approved original WLC links are missing")
    if b"CC BY-SA" not in files["LICENSE.txt"] or b"United Bible Societies" not in files["ATTRIBUTION.md"]:
        raise ValueError("Original data rights attribution missing")
    return original, files


def build_public_files(technical_rc: bytes, approval: dict):
    """Review and rewrap only source-provenanced lexical payload; no link edits."""
    original, files = verify_private_rc(technical_rc, approval)
    index = copy.deepcopy(original)
    index["editorial_candidate"] = {
        **original["editorial_candidate"],
        "status": PUBLISHED_STATUS,
        "previous_technical_candidate_status": TECHNICAL_STATUS,
        "private_candidate_index_sha256":
            approval["approved_private_index_sha256"],
    }
    index["publication"] = {
        "status": "published_source_edition_pinned_standalone_lexical_data",
        "version": "1.0.0",
        "release_tag": TAG,
        "license": "CC BY-SA 4.0",
        "authorization_status": APPROVAL,
        "reviewed_original_word_specific_headword_links": 275,
        "contextual_senses_inferred": 0,
        "source_technical_candidate_sha256":
            approval["approved_private_index_sha256"],
        "source_editions": approval["source_editions"],
    }
    # A published index differs ONLY in publication/provenance metadata.
    for key in original:
        if key != "editorial_candidate" and index[key] != original[key]:
            raise ValueError("Source crosswalk payload changed during promotion")
    if index["editorial_candidate"]["inferred_contextual_sense_ids"] != 0:
        raise ValueError("Contextual sense created while promoting lexical entries")
    content = {
        "index.json": encode(index),
        "README.md": README.encode("utf-8"),
        "ATTRIBUTION.md": files["ATTRIBUTION.md"],
        "LICENSE.txt": files["LICENSE.txt"],
    }
    manifest = {
        "schema_version": 1,
        "release_tag": TAG,
        "version": "1.0.0",
        "status": "owner_authorized_published_data_release",
        "license": "CC BY-SA 4.0",
        "publication_approved": True,
        "authorization_status": APPROVAL,
        "source_editions": approval["source_editions"],
        "original_wlc_lexical_occurrences": 248680,
        "linked_lexical_occurrences": 240373,
        "ubs_0_9_4_indexed_headword_scope": 242747,
        "edition_headword_coverage_pct": 99.022,
        "individual_source_word_headwords_approved": 275,
        "contextual_lexical_senses_inferred": 0,
        "private_reviewed_index_sha256":
            approval["approved_private_index_sha256"],
        "technical_rc2_zip_sha256":
            approval["approved_technical_rc2_zip_sha256"],
        "public_index_sha256": digest(content["index.json"]),
        "files": {
            name: {"sha256": digest(data), "bytes": len(data)}
            for name, data in sorted(content.items())
        },
    }
    content["manifest.json"] = encode(manifest)
    return content


def make_archive(files: dict) -> bytes:
    from io import BytesIO
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(PREFIX + name, TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o644 << 16
            archive.writestr(info, content,
                             compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)
    return buf.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--technical-rc", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview", action="store_true",
                        help="Only for CI PR: allow unpinned future public archive hash")
    parser.add_argument("--verify-only", action="store_true",
                        help="Check existing public archive byte for byte; do not write")
    args = parser.parse_args()
    approval = json.loads(args.approval.read_text(encoding="utf-8"))
    require_auth(approval, allow_missing_public_hash=args.preview)
    public = make_archive(build_public_files(args.technical_rc.read_bytes(), approval))
    actual = digest(public)
    expected = approval.get("expected_public_release_zip_sha256")
    if expected is not None and actual != expected:
        raise ValueError("Final public release bytes differ from owner authorized SHA-256")
    if args.verify_only:
        if not args.output.is_file() or args.output.read_bytes() != public:
            raise ValueError("Public archive has not been reverified byte for byte")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(public)
        args.output.with_suffix(args.output.suffix + ".sha256").write_text(
            actual + "  " + args.output.name + "\n", encoding="ascii"
        )
    with zipfile.ZipFile(__import__("io").BytesIO(public)) as package:
        if package.testzip() is not None:
            raise ValueError("Public release ZIP failed CRC")
        manifest = json.loads(package.read(PREFIX + "manifest.json"))
        for name, metadata in manifest["files"].items():
            if digest(package.read(PREFIX + name)) != metadata["sha256"]:
                raise ValueError("Public ZIP member checksum mismatch: " + name)
        if manifest["publication_approved"] is not True:
            raise ValueError("Public release package is not owner approved")
    print("UBS_HEBREW_V1_PUBLICATION_PAYLOAD_VERIFIED",
          json.dumps({"tag": TAG, "zip_sha256": actual,
                      "source_index_sha256":
                        approval["approved_private_index_sha256"],
                      "public_index_sha256": manifest["public_index_sha256"],
                      "pinned_public_zip_sha256": expected == actual},
                     sort_keys=True))


if __name__ == "__main__":
    main()

