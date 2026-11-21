#!/usr/bin/env python3
"""Regression tests: BSI UBS public promotion changes metadata, not lexical links."""
from __future__ import annotations

import copy
import io
import json
import runpy
import unittest
import zipfile
from pathlib import Path

MOD = runpy.run_path(str(Path(__file__).with_name(
    "promote_verified_ubs_release.py")))
MID = "000001000000000"


def fixture():
    words = {
        f"o0100100{i:06d}": {
            "entry_id": MID,
            "match_type": MOD["REVIEWED"],
            "lemma": "שָׁלוֹם",
            "strong": "7965",
            "lang": "H",
            "original_sdbh": "000001001001000",
            "reference": "GEN 1:1!1",
        } for i in range(275)
    }
    ix = {
        "format": "bsi-ubs-hebrew-lexical-crosswalk",
        "schema_version": 1,
        "license": "CC BY-SA 4.0",
        "dictionary": {"revision": "a15a96cfaa4ca18a6c0339016645ba1e534db3c8"},
        "macula": {"revision": "47db250bd55d0d8577f2a94fba114ef16c35b23c"},
        "by_macula_word": words,
        "by_sdbh": {"000001001001000": [MID]},
        "by_strong": {"H7965": [MID]},
        "coverage_with_word_ids": {"sense_links": 30492},
        "coverage_scope": {
            "linked_occurrences": 240373,
            "indexable_denominator": 242747,
            "indexable_unresolved": 2374,
            "coverage_pct": 99.022,
        },
        "editorial_candidate": {
            "status": MOD["TECHNICAL_STATUS"],
            "new_headword_only_wlc_word_ids": 275,
            "inferred_contextual_sense_ids": 0,
        },
    }
    raw = MOD["encode"](ix)
    approval = {
        "schema_version": 1,
        "status": MOD["APPROVAL"],
        "release_tag": MOD["TAG"],
        "published": False,
        "requires_exact_verified_bytes": True,
        "exclude_original_ubs_dictionary_prose": True,
        "exclude_original_macula_biblical_text": True,
        "independent_bible_app_integration": True,
        "owner_decision": "Project owner explicitly requested publication",
        "source_editions": {
            "ubs_revision": ix["dictionary"]["revision"],
            "macula_revision": ix["macula"]["revision"],
        },
        "original_lexical_source_occurrences": 248680,
        "linked_source_occurrences": 240373,
        "edition_indexed_headword_denominator": 242747,
        "indexed_scope_coverage_pct": 99.022,
        "original_word_specific_reviewed_links": 275,
        "inferred_contextual_sense_ids": 0,
        "approved_private_index_sha256": MOD["digest"](raw),
        "approved_technical_rc2_zip_sha256": None,
        "expected_public_release_zip_sha256": None,
    }
    contents = {
        "index.json": raw,
        "README.md": b"Internal source candidate; not a release",
        "ATTRIBUTION.md": b"United Bible Societies, CC BY-SA 4.0",
        "LICENSE.txt": b"CC BY-SA 4.0",
    }
    man = {
        "version": "1.0-rc2",
        "release_status": "private_candidate_not_approved_or_published",
        "publication_authorized": False,
        "source_editions": approval["source_editions"],
        "reviewed_word_specific_entry_only_links": 275,
        "inferred_contextual_ubs_sense_ids": 0,
        "candidate_index_sha256": approval["approved_private_index_sha256"],
        "files": {
            name: {"sha256": MOD["digest"](data), "bytes": len(data)}
            for name, data in contents.items()
        },
    }
    contents["manifest.json"] = MOD["encode"](man)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in contents.items():
            archive.writestr(MOD["RC_PREFIX"] + name, value)
    zip_bytes = output.getvalue()
    approval["approved_technical_rc2_zip_sha256"] = MOD["digest"](zip_bytes)
    return ix, zip_bytes, approval


class VerifiedUBSPublicReleaseTests(unittest.TestCase):
    def test_exact_source_preserving_promotion_deterministic_and_self_contained(self):
        original, private_zip, authorization = fixture()
        MOD["require_auth"](authorization, allow_missing_public_hash=True)
        contents = MOD["build_public_files"](private_zip, authorization)
        public = MOD["make_archive"](contents)
        self.assertEqual(public, MOD["make_archive"](contents))
        with zipfile.ZipFile(io.BytesIO(public)) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(
                set(archive.namelist()),
                {MOD["PREFIX"] + name for name in
                 ("index.json", "README.md", "ATTRIBUTION.md",
                  "LICENSE.txt", "manifest.json")}
            )
            index = json.loads(archive.read(MOD["PREFIX"] + "index.json"))
            man = json.loads(archive.read(MOD["PREFIX"] + "manifest.json"))
            for field in original:
                if field != "editorial_candidate":
                    self.assertEqual(index[field], original[field], field)
            self.assertEqual(index["editorial_candidate"]["status"],
                             MOD["PUBLISHED_STATUS"])
            self.assertTrue(man["publication_approved"])
            self.assertEqual(man["private_reviewed_index_sha256"],
                             authorization["approved_private_index_sha256"])
            self.assertEqual(man["individual_source_word_headwords_approved"], 275)
            self.assertIn(b"United Bible Societies", archive.read(
                MOD["PREFIX"] + "ATTRIBUTION.md"))

    def test_fail_closed_on_modified_private_artifact(self):
        _, original, auth = fixture()
        broken = bytearray(original)
        broken[55] ^= 1
        broken = bytes(broken)
        self.assertNotEqual(original, broken)
        with self.assertRaisesRegex(ValueError, "technical RC2 ZIP changed"):
            MOD["build_public_files"](broken, auth)

    def test_fail_closed_on_authorization_drift(self):
        _, source, auth = fixture()
        auth["status"] = "not_authorized"
        with self.assertRaisesRegex(ValueError, "Missing exact owner approval"):
            MOD["require_auth"](auth, allow_missing_public_hash=True)
        _, source, auth = fixture()
        auth["expected_public_release_zip_sha256"] = "0"*64
        contents = MOD["build_public_files"](source, auth)
        actual = MOD["digest"](MOD["make_archive"](contents))
        self.assertNotEqual(actual, auth["expected_public_release_zip_sha256"])
        _, _, auth = fixture()
        with self.assertRaisesRegex(ValueError, "not immutably SHA"):
            MOD["require_auth"](auth, allow_missing_public_hash=False)

    def test_fail_closed_on_source_sense_and_lexical_drift(self):
        original, _, auth = fixture()
        original["coverage_with_word_ids"]["sense_links"] += 1
        raw = MOD["encode"](original)
        auth["approved_private_index_sha256"] = MOD["digest"](raw)
        with self.assertRaisesRegex(ValueError, "Original technical source candidate manifest changed"):
            _, source, _ = fixture()
            MOD["build_public_files"](source, auth)


if __name__ == "__main__":
    unittest.main()

