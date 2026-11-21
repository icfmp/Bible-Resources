"""Regression tests for offline exact-word contextual entity lookup."""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

path = (Path(__file__).resolve().parents[1] / 'scripts' / 'resolve.py')
spec = importlib.util.spec_from_file_location("entity_index_resolver", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    return {
        "format": "bible-entity-index",
        "schema_version": 1,
        "provenance": {"source_editions": {
            "wlc": {"edition": "Macula-WLC@frozen",
                    "word_id_prefix": "o", "word_id_digits": 12},
            "sblgnt": {"edition": "Macula-SBLGNT@frozen",
                       "word_id_prefix": "n", "word_id_digits": 11},
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
                "source_context": {
                    "classification": "traditional_textual_variant_not_in_pinned_main_text",
                    "explanation": "Source-specific verse wording difference",
                    "evidence": ["Pinned Greek word scan", "Variant-source comparison"],
                },
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
        self.assertEqual(self.lookup(word_id="o010010010011suffix")["status"],
                         "invalid_source_word_id")
        self.assertEqual(self.lookup(word_id="o01001001001")["status"],
                         "invalid_source_word_id")
        self.assertEqual(self.lookup(word_id="o01001001001X")["status"],
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
        self.assertEqual(r["source_absence"]["source_context"]["classification"],
                         "traditional_textual_variant_not_in_pinned_main_text")
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


    def reader_lookup(self, word_id="o010010010011",
                      verse_id="01001001",
                      edition="Macula-WLC@frozen", corpus="wlc"):
        return self.resolver.resolve_for_reader(
            corpus=corpus, edition=edition,
            word_id=word_id, verse_id=verse_id)

    def test_reader_preserves_direct_ambiguity_and_source_qualifications(self):
        raw = self.lookup()
        reader = self.reader_lookup()
        self.assertEqual(reader["lookup_policy"], "explicit_only")
        self.assertEqual(reader["status"], "ambiguous_source_candidates")
        self.assertEqual(reader["canonical_ids"], ["person:Alpha", "place:Alpha"])
        self.assertEqual(reader["candidates"], raw["candidates"])
        self.assertTrue(all(row["review_status"] == "source_unreviewed"
                            for row in reader["candidates"]))

    def test_reader_ignores_indirect_actors_and_keeps_raw_data(self):
        data = fixture()
        data["entities"].append({
            "id": "person:Beta", "canonical_id": "person:Beta",
            "kind": "person", "review_status": "source_unreviewed",
            "source_id": "person:Beta", "references": ["01001001"],
        })
        data["by_word"]["wlc:o010010010021"].append({
            "entity_id": "person:Beta",
            "link_type": "pronominal_referents",
        })
        data["by_word"]["wlc:o010010010051"] = [
            {"entity_id": "person:Beta", "link_type": "pronominal_referents"},
            {"entity_id": "person:Alias", "link_type": "subject_referents"},
        ]
        original = copy.deepcopy(data)
        resolver = module.EntityResolver(data)
        lookup = {"corpus": "wlc", "edition": "Macula-WLC@frozen",
                  "verse_id": "01001001"}
        self.assertEqual(
            resolver.resolve(word_id="o010010010021", **lookup)["status"],
            "ambiguous_source_candidates")
        direct = resolver.resolve_for_reader(word_id="o010010010021", **lookup)
        self.assertEqual(direct["status"], "source_candidate")
        self.assertEqual(direct["canonical_ids"], ["person:Alpha"])
        self.assertEqual([x["id"] for x in direct["candidates"]], ["person:Alpha"])
        indirect = resolver.resolve_for_reader(
            word_id="o010010010051", **lookup)
        self.assertEqual(indirect["status"], "no_explicit_entity")
        self.assertEqual(indirect["candidates"], [])
        self.assertEqual(indirect["canonical_ids"], [])
        self.assertEqual(
            resolver.resolve(word_id="o010010010051", **lookup)["status"],
            "ambiguous_source_candidates")
        self.assertEqual(data, original)

    def test_reader_aliases_do_not_create_second_identity(self):
        data = fixture()
        data["by_word"]["wlc:o010010010021"][1]["link_type"] = (
            "explicit_instances")
        resolver = module.EntityResolver(data)
        result = resolver.resolve_for_reader(
            corpus="wlc", edition="Macula-WLC@frozen",
            word_id="o010010010021", verse_id="01001001")
        self.assertEqual(result["status"], "source_candidate")
        self.assertEqual(result["canonical_ids"], ["person:Alpha"])
        self.assertEqual({x["id"] for x in result["candidates"]},
                         {"person:Alpha", "person:Alias"})

    def test_reader_does_not_bypass_source_version_or_missing_guards(self):
        cases = [
            ("o010010010011", "01001001", "other", "wlc",
             "incompatible_source_edition"),
            ("o010010010011", "01001002", "Macula-WLC@frozen", "wlc",
             "verse_context_mismatch"),
            ("o010010010041", "01001001", "Macula-WLC@frozen", "wlc",
             "unattested_source_word_id"),
            ("o010010010032", "01001001", "Macula-WLC@frozen", "wlc",
             "no_indexed_entity"),
            ("n40001002001", "40001002", "Macula-SBLGNT@frozen", "sblgnt",
             "verse_not_in_pinned_original_word_inventory"),
        ]
        for word, verse, edition, corpus, status in cases:
            with self.subTest(word=word, status=status):
                result = self.reader_lookup(
                    word_id=word, verse_id=verse,
                    edition=edition, corpus=corpus)
                self.assertEqual(result["status"], status)
                self.assertEqual(result["lookup_policy"], "explicit_only")
                self.assertEqual(result["candidates"], [])

    def test_cli_reader_mode_is_opt_in_and_raw_mode_unchanged(self):
        data = fixture()
        data["by_word"]["wlc:o010010010051"] = [
            {"entity_id": "person:Alias", "link_type": "subject_referents"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            index = Path(directory) / "index.json"
            index.write_text(json.dumps(data), encoding="utf-8")
            args = [sys.executable, "-I", str(path), "--index", str(index),
                    "--corpus", "wlc", "--edition", "Macula-WLC@frozen",
                    "--word-id", "o010010010051", "--verse-id", "01001001"]
            raw = subprocess.run(args, check=True, text=True,
                                 capture_output=True)
            reader = subprocess.run(args + ["--reader-facing"], check=True,
                                    text=True, capture_output=True)
            self.assertEqual(json.loads(raw.stdout)["status"], "source_candidate")
            self.assertEqual(json.loads(reader.stdout)["status"],
                             "no_explicit_entity")
            self.assertEqual(json.loads(reader.stdout)["candidates"], [])

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
