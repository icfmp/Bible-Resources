"""Regression tests for non-destructive person-identity overlap audit."""
from __future__ import annotations

import importlib.util
import unittest
import tempfile
from pathlib import Path

script = (Path(__file__).resolve().parents[1] / 'scripts' / 'audit_person_overlaps.py')
spec = importlib.util.spec_from_file_location("identity_overlap_audit", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sample():
    def hit(entity, field):
        return {"entity_id": entity, "link_type": field}
    return {
        "format": "bible-entity-index",
        "schema_version": 1,
        "provenance": {
            "source_commit": "test-frozen-revision",
            "source_editions": {"wlc": {"edition": "test-edition"}},
        },
        "entities": [
            {"id": "person:Adam", "kind": "person", "canonical_id": "person:Adam"},
            {"id": "person:AdamAlias", "kind": "person",
             "canonical_id": "person:Adam"},
            {"id": "person:Abel", "kind": "person", "canonical_id": "person:Abel"},
            {"id": "place:City", "kind": "place", "canonical_id": "place:City"},
        ],
        "by_word": {
            "wlc:o010010010011": [
                hit("person:Adam", "explicit_instances"),
                hit("person:AdamAlias", "explicit_instances"),
                hit("place:City", "explicit_instances"),
            ],
            "wlc:o010010010021": [
                hit("person:Adam", "explicit_instances"),
                hit("person:Abel", "explicit_instances"),
            ],
            "wlc:o010010010031": [
                hit("person:Adam", "explicit_instances"),
                hit("person:Abel", "subject_referents"),
            ],
            "wlc:o010010010041": [
                hit("person:Adam", "subject_referents"),
                hit("person:Abel", "pronominal_referents"),
            ],
        },
    }


class PersonOverlapTests(unittest.TestCase):
    def test_aliases_and_different_kinds_do_not_create_person_collisions(self):
        report = module.audit(sample())
        stats = report["statistics"]
        self.assertEqual(stats["distinct_person_original_word_overlap_candidates"], 3)
        self.assertEqual(stats["multiple_explicit_names"], 1)
        self.assertEqual(stats["mixed_name_and_indirect"], 1)
        self.assertEqual(stats["indirect_only"], 1)
        self.assertEqual([e["word_id"] for e in report["findings"]],
                         ["o010010010021", "o010010010031", "o010010010041"])
        self.assertEqual(report, module.audit(sample()))
        self.assertNotIn("o010010010011", [
            e["word_id"] for e in report["findings"]])
        self.assertIn("candidate ambiguities", report["warning"])

    def test_contextual_overlap_reviews_require_exact_ids_people_and_editions(self):
        report=module.audit(sample())
        entry={
            "corpus":"wlc", "word_id":"o010010010021",
            "canonical_people":["person:Abel","person:Adam"],
            "classification":"shared_genealogical_name_component",
            "reason":"A source-cited compound in a synthetic fixture",
            "evidence":["Pinned source word claim","Contextual source role"],
        }
        manifest={
            "schema_version":1,
            "kind":"exact_word_distinct_person_review",
            "source_editions":{"wlc":"test-edition"},
            "cases":[entry],
        }
        verified=module.verify_explicit_name_reviews(report,manifest)
        self.assertEqual(verified["statistics"]["reviewed_explicit_name_word_overlaps"],1)
        self.assertEqual(verified["statistics"]["shared_genealogical_name_component"],1)
        self.assertEqual(verified["cases"][0]["canonical_people"],
                         ["person:Abel","person:Adam"])
        with self.assertRaisesRegex(ValueError,"Wrong original-language review edition"):
            module.verify_explicit_name_reviews(report,dict(
                manifest,source_editions={"wlc":"wrong-edition"}))
        with self.assertRaisesRegex(ValueError,"Unreviewed exact-person"):
            module.verify_explicit_name_reviews(report,dict(manifest,cases=[]))
        with self.assertRaisesRegex(ValueError,"Stale or incorrect"):
            module.verify_explicit_name_reviews(report,dict(
                manifest,cases=[dict(entry,canonical_people=["person:Adam"])]))
        with self.assertRaisesRegex(ValueError,"Duplicate exact-word"):
            module.verify_explicit_name_reviews(report,dict(
                manifest,cases=[entry,entry]))
        with self.assertRaisesRegex(ValueError,"Source evidence required"):
            module.verify_explicit_name_reviews(report,dict(
                manifest,cases=[dict(entry,evidence=[])]))
        with self.assertRaisesRegex(ValueError,"Invalid exact-word"):
            module.verify_explicit_name_reviews(report,dict(
                manifest,cases=[dict(entry,classification="all_resolved")]))

    def test_indirect_source_form_triage_is_complete_and_non_editorial(self):
        report = module.audit(sample())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "macula.tsv"
            header = "xml:id\tref\tnumber\tmorph\ttext\n"
            word = "o010010010041"
            path.write_text(header + word + "\tGEN 1:1!4\tplural\tSp3mp\tthey\n",
                            encoding="utf-8")
            reviewed = module.audit_indirect_source_forms(report, {"wlc": path})
            self.assertEqual(reviewed["statistics"]["indirect_only_source_words"], 1)
            self.assertEqual(reviewed["statistics"]["by_corpus"], {"wlc": 1})
            self.assertEqual(reviewed["statistics"]["source_word_number_buckets"],
                             {"source_word_plural": 1})
            self.assertEqual(reviewed["statistics"]["different_canonical_people_per_word"],
                             {"2": 1})
            self.assertEqual(reviewed["cases"][0]["source_word"]["morph"], "Sp3mp")
            self.assertEqual(reviewed["cases"][0]["canonical_people"],
                             report["findings"][-1]["canonical_people"])
            self.assertIn("NOT proof", reviewed["warning"])
            # A singular source word is only a review signal, never
            # an automatic identity correction or candidate deletion.
            path.write_text(header + word + "\tGEN 1:1!4\tsingular\tSp3ms\the\n",
                            encoding="utf-8")
            singular = module.audit_indirect_source_forms(report, {"wlc": path})
            self.assertEqual(singular["statistics"]["source_word_number_buckets"],
                             {"source_word_singular": 1})
            self.assertEqual(singular["cases"][0]["canonical_people"],
                             reviewed["cases"][0]["canonical_people"])
            # Missing/duplicated ID and wrong TSV schema fail closed.
            path.write_text(header + "o010010010099\tGEN 1:1\tplural\tPp\tthey\n",
                            encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "absent from pinned"):
                module.audit_indirect_source_forms(report, {"wlc": path})
            path.write_text(header + (word + "\tGEN 1:1\tplural\tPp\tthey\n") * 2,
                            encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicated pinned"):
                module.audit_indirect_source_forms(report, {"wlc": path})
            path.write_text("xml:id\tword\n" + word + "\tthey\n",
                            encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "TSV schema"):
                module.audit_indirect_source_forms(report, {"wlc": path})
            with self.assertRaisesRegex(ValueError, "Incomplete pinned source"):
                module.audit_indirect_source_forms(report, {})

    def test_fail_closed_for_broken_index(self):
        data = sample()
        data["schema_version"] = 2
        with self.assertRaisesRegex(ValueError, "Incompatible"):
            module.audit(data)
        data = sample()
        data["by_word"]["wlc:o010010010021"].append(
            {"entity_id": "person:Unknown", "link_type": "explicit_instances"})
        with self.assertRaisesRegex(ValueError, "unknown derived record"):
            module.audit(data)


if __name__ == "__main__":
    unittest.main()
