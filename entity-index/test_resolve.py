"""Regression tests for offline exact-word contextual entity lookup."""
from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

path = Path(__file__).with_name("resolve.py")
spec = importlib.util.spec_from_file_location("entity_index_resolver", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    return {
        "format": "bible-entity-index",
        "schema_version": 1,
        "provenance": {"source_editions": {
            "wlc": {"edition": "Macula-WLC@frozen", "word_id_prefix": "o"},
            "sblgnt": {"edition": "Macula-SBLGNT@frozen", "word_id_prefix": "n"},
        }},
        "entities": [
            {"id": "person:Alpha", "canonical_id": "person:Alpha",
             "kind": "person", "review_status": "source_unreviewed",
             "source_id": "person:Alpha", "references": ["01001001"]},
            {"id": "place:Alpha", "canonical_id": "place:Alpha",
             "kind": "place", "review_status": "source_unreviewed",
             "source_id": "place:Alpha", "references": ["01001001"]},
            {"id": "person:Alias", "canonical_id": "person:Alpha",
             "kind": "person", "review_status": "editorially_reviewed",
             "source_id": "person:OldAlias", "references": [],
             "editorial_reason": "Documented spelling form, not a distinct person."},
        ],
        "unattested_source_verses": {
            "sblgnt:40001002": {
                "source_edition": "Macula-SBLGNT@frozen",
                "scope": "absent_from_pinned_original_word_inventory_only",
                "source_reference_claims": ["person:Alpha"],
                "evidence": [{"source": "source-verse-audit"}],
            },
        },
        "unattested_source_words": {
            "wlc:o010010010041": {
                "source_edition": "Macula-WLC@frozen",
                "evidence": [{"source": "pinned-audit"}],
                "source_claims": [{"entity_id": "person:Alpha",
                                   "link_type": "subject_referents"}],
            },
        },
        "by_word": {
            "wlc:o010010010011": [
                {"entity_id": "person:Alpha", "link_type": "explicit_instances"},
                {"entity_id": "place:Alpha", "link_type": "explicit_instances"},
            ],
            "wlc:o010010010021": [
                {"entity_id": "person:Alpha", "link_type": "explicit_instances"},
                {"entity_id": "person:Alias", "link_type": "subject_referents"},
            ],
            "sblgnt:n40001001001": [
                {"entity_id": "person:Alpha", "link_type": "explicit_instances"},
            ],
        },
    }


class ResolverTests(unittest.TestCase):
    def setUp(self):
        self.resolver = module.EntityResolver(fixture())

    def lookup(self, word_id="o010010010011", verse_id="01001001",
               edition="Macula-WLC@frozen", corpus="wlc"):
        return self.resolver.resolve(
            corpus=corpus, edition=edition,
            word_id=word_id, verse_id=verse_id)

    def test_preserves_distinct_identity_ambiguity(self):
        r = self.lookup()
        self.assertEqual(r["status"], "ambiguous_source_candidates")
        self.assertEqual(r["canonical_ids"], ["person:Alpha", "place:Alpha"])
        self.assertEqual(len(r["candidates"]), 2)
        self.assertTrue(all(
            x["review_status"] == "source_unreviewed" for x in r["candidates"]))
        self.assertTrue(all(
            x["reference_list_includes_verse"] for x in r["candidates"]))

    def test_aliases_same_canonical_identity_keep_two_link_evidence(self):
        r = self.lookup(word_id="o010010010021")
        self.assertEqual(r["status"], "source_candidate")
        self.assertEqual(r["canonical_ids"], ["person:Alpha"])
        self.assertEqual(len(r["candidates"]), 2)
        alias = next(x for x in r["candidates"] if x["id"] == "person:Alias")
        self.assertEqual(alias["link_type"], "subject_referents")
        self.assertFalse(alias["reference_list_includes_verse"])
        self.assertIn("spelling form", alias["editorial_scope_note"])

    def test_edition_verse_and_corpus_must_match_exactly(self):
        self.assertEqual(self.lookup(edition="Macula-WLC@other")["status"],
                         "incompatible_source_edition")
        self.assertEqual(self.lookup(verse_id="01001002")["status"],
                         "verse_context_mismatch")
        self.assertEqual(self.lookup(verse_id="bad")["status"], "invalid_verse_id")
        self.assertEqual(self.lookup(word_id="n010010010011")["status"],
                         "invalid_source_word_id")
        self.assertEqual(self.lookup(corpus="lxx")["status"], "unavailable_corpus")
        r = self.lookup(word_id="n40001001001", verse_id="40001001",
                        edition="Macula-SBLGNT@frozen", corpus="sblgnt")
        self.assertEqual(r["status"], "source_candidate")
        self.assertEqual(r["canonical_ids"], ["person:Alpha"])

    def test_unindexed_word_does_not_become_guessed_entity(self):
        r = self.lookup(word_id="o010010010032")
        self.assertEqual(r["status"], "no_indexed_entity")
        self.assertEqual(r["candidates"], [])
        self.assertEqual(r["canonical_ids"], [])

    def test_verse_absent_from_pinned_original_word_source_only(self):
        r = self.lookup(corpus="sblgnt",
                        edition="Macula-SBLGNT@frozen",
                        word_id="n40001002001", verse_id="40001002")
        self.assertEqual(r["status"],
                         "verse_not_in_pinned_original_word_inventory")
        self.assertEqual(r["canonical_ids"], [])
        self.assertEqual(r["source_absence"]["source_reference_claims"],
                         ["person:Alpha"])
        self.assertEqual(
            self.lookup(corpus="sblgnt", edition="Macula-SBLGNT@other",
                        word_id="n40001002001", verse_id="40001002")["status"],
            "incompatible_source_edition")
        self.assertEqual(
            self.lookup(corpus="sblgnt", edition="Macula-SBLGNT@frozen",
                        word_id="n40001001001", verse_id="40001002")["status"],
            "verse_context_mismatch")

    def test_source_unattested_word_never_becomes_entity_candidate(self):
        r = self.lookup(word_id="o010010010041")
        self.assertEqual(r["status"], "unattested_source_word_id")
        self.assertEqual(r["canonical_ids"], [])
        self.assertEqual(r["candidates"], [])
        self.assertEqual(r["source_absence"]["evidence"],
                         [{"source": "pinned-audit"}])
        self.assertEqual(
            self.lookup(word_id="o010010010041", edition="incorrect")["status"],
            "incompatible_source_edition")

    def test_rejects_corrupt_or_incompatible_index(self):
        data = fixture()
        data["schema_version"] = 2
        with self.assertRaisesRegex(ValueError, "Incompatible"):
            module.EntityResolver(data)
        data = fixture()
        data["by_word"]["wlc:o010010010011"].append(
            {"entity_id": "person:Missing", "link_type": "explicit_instances"})
        with self.assertRaisesRegex(ValueError, "unknown entity"):
            module.EntityResolver(data).resolve(
                corpus="wlc", edition="Macula-WLC@frozen",
                word_id="o010010010011", verse_id="01001001")
        data = fixture()
        data["by_word"]["wlc:o010010010041"] = [
            {"entity_id": "person:Alpha", "link_type": "subject_referents"}]
        with self.assertRaisesRegex(ValueError, "must not remain lookup-indexed"):
            module.EntityResolver(data)
        data = fixture()
        data["entities"].append(copy.deepcopy(data["entities"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate entity IDs"):
            module.EntityResolver(data)


if __name__ == "__main__":
    unittest.main()
