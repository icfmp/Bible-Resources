"""Unit tests: source integrity, editorial review, ambiguity and reproducibility."""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("compile_index.py")
spec = importlib.util.spec_from_file_location("entity_index_builder", SCRIPT)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
CATS = builder.CATEGORIES


class EntityIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for category in CATS:
            (self.root / category / "json").mkdir(parents=True)
        self.lock = {
            "schema_version": 1, "source_repository": "https://example.invalid/ACAI",
            "source_commit": "test-sha", "source_license": "CC BY-SA 4.0",
            "source_credit": "ACAI source test", "reviewed_hebrew_source": "pinned-test",
            "reviewed_greek_source": "pinned-test", "source_records_expected": 0,
            "source_editions": {"wlc": {"edition": "pinned-test",
                                        "word_id_prefix": "o"}} ,
        }

    def write_record(self, category, name, **fields):
        entity_id = CATS[category] + ":" + name
        doc = {"id": entity_id, "primary_id": entity_id, "references": [],
               "key_references": [], "explicit_instances": {},
               "pronominal_referents": {}, "subject_referents": {},
               "localizations": {"eng": {
                   "preferred_label": "Never copy",
                   "descriptions": [{"description": "Invented biographical prose"}]}}}
        doc.update(fields)
        path = self.root / category / "json" / (name + ".json")
        path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        self.lock["source_records_expected"] += 1
        return path

    def build(self, decisions=(), source_absences=None):
        return builder.build(self.root, self.lock,
                             {"schema_version": 1, "decisions": list(decisions)},
                             source_absences)

    def test_actual_editorial_pilots_preserve_source_and_correct_classification(self):
        path = self.write_record("people", "Jashar",
                                 references=["06010013", "10001018"],
                                 explicit_instances={"wlc": [
                                     ["o060100130142"], ["o100010180102"]]})
        self.write_record("people", "Perez-uzzah",
                          primary_id="person:Uzzah", references=["10006008"],
                          explicit_instances={"wlc": [
                              ["o100060080121", "o100060080131"]]})
        self.write_record("people", "Uzzah",
                          references=["10006008", "13013011"],
                          explicit_instances={"wlc": [
                              ["o100060080082"],
                              ["o100060080121", "o100060080131"],
                              ["o130130110072"]]})
        self.write_record("people", "Hammelech",
                          references=["24036026"],
                          explicit_instances={"wlc": [["o240360260022"]]})

        self.write_record("people", "Philistine",
                          references=["01010014", "13001012"],
                          explicit_instances={"wlc": [
                              ["o010100140081"], ["o130010120081"]]})
        self.write_record("groups", "Philistine",
                          references=["07015003"],
                          explicit_instances={"wlc": [["o070150030062"]]})
        self.write_record("people", "Shiloh",
                          references=["01049010"],
                          explicit_instances={"wlc": [["o010490100121"]]})
        self.write_record("keyterms", "Universe",
                          primary_id="keyterm:Ability",
                          references=["40012032"],
                          explicit_instances={"SBLGNT": [["n40012032029"]]})
        self.write_record("keyterms", "World",
                          primary_id="keyterm:Ability",
                          references=["43003016"],
                          explicit_instances={"SBLGNT": [["n43003016007"]]})
        source_before = path.read_bytes()
        decisions = json.loads(
            Path(__file__).with_name("editorial-decisions.json").read_text()
        )["decisions"]
        report = self.build(decisions)
        self.assertEqual(report["statistics"]["source_records"], 9)
        self.assertEqual(report["statistics"]["index_entities"], 6)
        self.assertEqual(report["statistics"]["quarantined_records"], 3)
        self.assertEqual(report["statistics"]["reviewed_entries"], 6)
        by_id = {row["id"]: row for row in report["entities"]}
        self.assertIn("work:BookOfJashar", by_id)
        self.assertIn("place:PerezUzzah", by_id)
        self.assertIn("person:Uzzah", by_id)
        self.assertNotIn("person:Jashar", by_id)
        self.assertNotIn("person:Hammelech", by_id)
        self.assertNotIn("person:Philistine", by_id)
        self.assertNotIn("person:Shiloh", by_id)
        self.assertNotIn("wlc:o010490100121", report["by_word"])
        self.assertEqual(by_id["keyterm:Universe"]["canonical_id"],
                         "keyterm:Universe")
        self.assertEqual(by_id["keyterm:World"]["canonical_id"],
                         "keyterm:World")
        self.assertEqual(by_id["keyterm:Universe"]["source_primary_id"],
                         "keyterm:Ability")
        self.assertEqual(by_id["keyterm:World"]["occurrences"]
                         ["explicit_instances"]["SBLGNT"],
                         [["n43003016007"]])
        self.assertIn("group:Philistine", by_id)
        self.assertEqual(by_id["group:Philistine"]["references"],
                         ["07015003", "01010014", "13001012"])
        self.assertEqual(by_id["group:Philistine"]["occurrences"]
                         ["explicit_instances"]["wlc"][-2:],
                         [["o010100140081"], ["o130010120081"]])
        self.assertEqual(report["by_word"]["wlc:o010100140081"],
                         [{"entity_id": "group:Philistine",
                           "link_type": "explicit_instances"}])
        self.assertEqual(by_id["work:BookOfJashar"]["source_id"], "person:Jashar")
        self.assertEqual(by_id["place:PerezUzzah"]["canonical_id"],
                         "place:PerezUzzah")
        self.assertEqual(by_id["place:PerezUzzah"]["references"],
                         ["10006008", "13013011"])
        self.assertEqual(by_id["place:PerezUzzah"]["occurrences"]
                         ["explicit_instances"]["wlc"][-1],
                         ["o130130110111", "o130130110121"])
        self.assertEqual(by_id["person:Uzzah"]["occurrences"]
                         ["explicit_instances"]["wlc"],
                         [["o100060080082"], ["o130130110072"]])
        self.assertEqual(report["by_word"]["wlc:o100060080121"],
                         [{"entity_id": "place:PerezUzzah",
                           "link_type": "explicit_instances"}])
        self.assertEqual(report["by_word"]["wlc:o060100130142"],
                         [{"entity_id": "work:BookOfJashar",
                           "link_type": "explicit_instances"}])
        self.assertNotIn("wlc:o240360260022", report["by_word"])
        self.assertEqual(path.read_bytes(), source_before)
        self.assertNotIn("Invented biographical prose",
                         json.dumps(report, ensure_ascii=False))
        self.assertNotIn("Never copy", json.dumps(report, ensure_ascii=False))

    def test_pinned_absent_word_is_quarantined_from_lookup_not_source(self):
        path = self.write_record(
            "people", "GenericMale", references=["02002013"],
            subject_referents={"wlc": [["o020020130103"]]})
        before = path.read_bytes()
        audit = {
            "schema_version": 1, "corpus": "wlc",
            "source_edition": "pinned-test",
            "provenance": [{"source": "pinned-source-check", "finding": "absent"}],
            "word_ids": ["o020020130103"],
        }
        report = self.build(source_absences=audit)
        self.assertEqual(report["statistics"]["unattested_distinct_source_words"], 1)
        self.assertNotIn("wlc:o020020130103", report["by_word"])
        self.assertEqual(
            report["unattested_source_words"]["wlc:o020020130103"]
                  ["source_claims"],
            [{"entity_id": "person:GenericMale", "link_type": "subject_referents"}],
        )
        self.assertEqual(report["entities"][0]["occurrences"]["subject_referents"]
                         ["wlc"], [["o020020130103"]])
        self.assertEqual(path.read_bytes(), before)

        with self.assertRaisesRegex(ValueError, "not in source index"):
            self.build(source_absences=dict(audit, word_ids=["o020020130104"]))
        with self.assertRaisesRegex(ValueError, "Duplicate source-unattested"):
            self.build(source_absences=dict(audit, word_ids=[
                "o020020130103", "o020020130103"]))
        with self.assertRaisesRegex(ValueError, "not pinned"):
            self.build(source_absences=dict(audit, source_edition="wrong"))
        with self.assertRaisesRegex(ValueError, "source provenance"):
            self.build(source_absences=dict(audit, provenance=[]))
        self.write_record(
            "people", "Other", references=["02002013"],
            explicit_instances={"wlc": [["o020020130103"]]})
        with self.assertRaisesRegex(ValueError, "direct/pronominal"):
            self.build(source_absences=audit)

    def test_preserve_group_order_repetitions_and_ambiguity(self):
        self.write_record("people", "A", references=["01001001"],
                          explicit_instances={"wlc": [
                              ["o010010010011", "o010010010021"],
                              ["o010010010011", "o010010010021"]]},
                          subject_referents={"wlc": [["o010010010031"]]})
        self.write_record("places", "A", references=["01001001"],
                          explicit_instances={"wlc": [["o010010010011"]]})
        report = self.build()
        by_id = {entry["id"]: entry for entry in report["entities"]}
        self.assertEqual(by_id["person:A"]["occurrences"]
                         ["explicit_instances"]["wlc"],
                         [["o010010010011", "o010010010021"]] * 2)
        self.assertEqual([x["entity_id"] for x in
                          report["by_word"]["wlc:o010010010011"]],
                         ["person:A", "place:A"])
        self.assertEqual(report["by_word"]["wlc:o010010010031"],
                         [{"entity_id": "person:A",
                           "link_type": "subject_referents"}])
        self.assertEqual(report, self.build())
        self.assertEqual(report["statistics"]["reviewed_entries"], 0)

    def test_fails_closed_on_missing_group_or_unverified_record_count(self):
        self.write_record("people", "A",
                          explicit_instances={"wlc": [["o010010010011"]]})
        decision = {"source_id": "person:A", "action": "amend_occurrences",
                    "reason": "reviewed", "evidence": ["test evidence"],
                    "remove_explicit_instances": {"wlc": [["o010010010021"]]}}
        with self.assertRaisesRegex(ValueError, "absent group cannot be removed"):
            self.build([decision])
        self.lock["source_records_expected"] += 1
        with self.assertRaisesRegex(ValueError, "Incomplete source snapshot"):
            self.build()
        self.lock["source_records_expected"] -= 1
        with self.assertRaisesRegex(ValueError, "nonexistent records"):
            self.build([dict(decision, source_id="person:Absent")])

    def test_rejects_silent_id_collision_and_malformed_source(self):
        self.write_record("people", "A",
                          explicit_instances={"wlc": [["o010010010011"]]})
        self.write_record("places", "A")
        decisions = [
            {"source_id": source, "action": "replace_identity",
             "id": "concept:Duplicate", "kind": "concept",
             "reason": "reviewed", "evidence": ["test"]}
            for source in ("person:A", "place:A")
        ]
        with self.assertRaisesRegex(ValueError, "same output entity ID"):
            self.build(decisions)
        self.write_record("people", "Bad",
                          explicit_instances={"wlc": [["malformed"]]})
        with self.assertRaisesRegex(ValueError, "invalid original-word ID"):
            self.build()


if __name__ == "__main__":
    unittest.main()
