#!/usr/bin/env python3
"""Offline regression and provenance tests for the nonpublished UBS v1 archive."""
from __future__ import annotations

import copy
import hashlib
import json
import runpy
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = runpy.run_path(str(HERE / "package_reviewed_v1_candidate.py"))
EID = "000001000000000"


def fixture():
    links = {
        f"o0100100{i:06d}": {
            "entry_id": EID,
            "match_type": "editorially_reviewed_original_wlc_headword_only",
            "lemma": "שָׁלוֹם", "strong": "7965", "lang": "H",
            "reference": "GEN 1:1!1", "original_sdbh": "000001001001000"
        } for i in range(275)
    }
    index = {
        "format": "bsi-ubs-hebrew-lexical-crosswalk",
        "schema_version": 1,
        "languages": ["en", "fr"],
        "license": "CC BY-SA 4.0",
        "dictionary": {"edition": "0.9.4", "revision": MOD["UBS_REV"]},
        "macula": {"revision": MOD["MACULA_REV"]},
        "by_entry_strong_family": {EID: ["H7965"]},
        "by_macula_word": links,
        "coverage_scope": {
            "original_lexical_source_occurrences": 248680,
            "linked_occurrences": 240373, "indexable_denominator": 242747,
            "indexable_unresolved": 2374, "coverage_pct": 99.022,
        },
        "coverage_with_word_ids": {
            "additional_entry_only_links": 275,
            "word_aware_entry_links": 268706,
            "sense_links": 30492,
        },
        "editorial_candidate": {
            "status": "private_v1_candidate_not_published_or_approved",
            "index_source_revisions": {
                "ubs_revision": MOD["UBS_REV"],
                "macula_revision": MOD["MACULA_REV"],
            },
            "original_index_sha256": "a" * 64,
            "original_index_left_unchanged": True,
            "source_corpus_left_unchanged": True,
            "new_headword_only_wlc_word_ids": 275,
            "additional_final_source_specific_approvals": 2,
            "remaining_source_specific_unlinked_words": 24,
            "inferred_contextual_sense_ids": 0,
        },
    }
    raw = MOD["canonical_json"](index)
    manifest = {
        "schema_version": 1,
        "status": "private_v1_candidate_not_published_or_approved",
        "release_approved": False,
        "source_editions": {
            "ubs_revision": MOD["UBS_REV"],
            "macula_revision": MOD["MACULA_REV"],
        },
        "candidate_index_sha256": MOD["sha256"](raw),
        "original_index_and_source_unchanged": True,
        "original_source_linked_lexical_occurrences": 240098,
        "new_entry_only_word_links": 275,
        "final_original_source_word_approvals": 2,
        "remaining_last_original_word_abstentions": 24,
        "previous_candidate_index_sha256": "7c2e386a07d0dede3bcb836f64db66a5779b7e4c9d8f6d20ec76e06d156c1b35",
        "original_source_words_left_unlinked_by_review": 1,
        "contextual_sense_ids_inferred": 0,
    }
    return index, raw, manifest


class ReleaseCandidateArchiveTests(unittest.TestCase):
    def test_pinned_source_candidate_and_reproducible_license_archive(self):
        index, raw, manifest = fixture()
        MOD["verify_candidate"](index, raw, manifest)
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "candidate-a.zip", Path(tmp) / "candidate-b.zip"
            files = MOD["payload"](raw, manifest)
            MOD["create_archive"](a, files)
            MOD["create_archive"](b, files)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with zipfile.ZipFile(a) as z:
                self.assertEqual(z.read(MOD["PREFIX"] + "index.json"), raw)
                self.assertIn(b"Attribution", z.read(MOD["PREFIX"] + "ATTRIBUTION.md"))
                self.assertIn(b"CC BY-SA", z.read(MOD["PREFIX"] + "LICENSE.txt"))
                self.assertFalse(json.loads(z.read(
                    MOD["PREFIX"] + "manifest.json"))["publication_authorized"])

    def test_refuse_unpinned_source_and_publication_flag(self):
        ix, raw, man = fixture()
        man["release_approved"] = True
        with self.assertRaisesRegex(ValueError, "not cleared"):
            MOD["verify_candidate"](ix, raw, man)
        ix, raw, man = fixture()
        ix["dictionary"]["revision"] = "changed"
        raw = MOD["canonical_json"](ix)
        man["candidate_index_sha256"] = MOD["sha256"](raw)
        with self.assertRaisesRegex(ValueError, "edition drift"):
            MOD["verify_candidate"](ix, raw, man)

    def test_refuse_unsafe_new_sense_and_missing_attribution_population(self):
        ix, _, man = fixture()
        first = next(iter(ix["by_macula_word"].values()))
        first["LEXID"] = "000001001001000"
        raw = MOD["canonical_json"](ix)
        man["candidate_index_sha256"] = MOD["sha256"](raw)
        with self.assertRaisesRegex(ValueError, "Unsafe source-reviewed"):
            MOD["verify_candidate"](ix, raw, man)
        ix, _, man = fixture()
        ix["by_macula_word"].pop(next(iter(ix["by_macula_word"])))
        raw = MOD["canonical_json"](ix)
        man["candidate_index_sha256"] = MOD["sha256"](raw)
        with self.assertRaisesRegex(ValueError, "Word link inventory"):
            MOD["verify_candidate"](ix, raw, man)

    def test_refuse_byte_mutation_even_when_json_decodes(self):
        ix, raw, man = fixture()
        tampered = raw.replace(b'"languages":["en","fr"]',
                               b'"languages": ["en", "fr"]')
        self.assertNotEqual(raw, tampered)
        with self.assertRaisesRegex(ValueError, "Noncanonical"):
            MOD["verify_candidate"](ix, tampered, man)
        with self.assertRaisesRegex(ValueError, "independently pinned hash"):
            MOD["verify_candidate"](ix, raw, {**man, "candidate_index_sha256": "0" * 64})


if __name__ == "__main__":
    unittest.main()

