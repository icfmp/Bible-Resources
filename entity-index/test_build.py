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
            "source_editions": {
                "wlc": {"edition": "pinned-test", "word_id_prefix": "o",
                        "word_id_digits": 12},
                "sblgnt": {"edition": "pinned-test", "word_id_prefix": "n",
                           "word_id_digits": 11},
            },
            "source_corpora": {"wlc": "wlc", "SBLGNT": "sblgnt",
                               "sblgnt": "sblgnt"},
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

    def build(self, decisions=(), source_absences=None,
              source_verse_absences=None, reference_qualifications=None):
        return builder.build(self.root, self.lock,
                             {"schema_version": 1, "decisions": list(decisions)},
                             source_absences, source_verse_absences,
                             reference_qualifications)

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
        self.write_record("people", "Johanan",
                          primary_id="person:Jehoahaz.3",
                          references=["13003015"],
                          explicit_instances={"wlc": [["o130030150041"]]})
        self.write_record("people", "Jehoahaz.3",
                          references=["12023030", "13003015"],
                          explicit_instances={"wlc": [
                              ["o120230300131"], ["o130030150041"]]})
        self.write_record("places", "Gadara",
                          primary_id="place:Gerasa",
                          references=["40008028", "41005001"],
                          explicit_instances={"SBLGNT": [["n40008028011"]]})
        self.write_record("places", "Gerasa",
                          references=["40008028", "41005001"],
                          explicit_instances={"SBLGNT": [
                              ["n40008028011"], ["n41005001012"]]})
        self.write_record("places", "Gadara.2", references=[])
        self.write_record("people", "Shallum.5",
                          references=["13003015"],
                          explicit_instances={"wlc": [["o130030150101"]]})
        source_before = path.read_bytes()
        all_decisions = json.loads(
            Path(__file__).with_name("editorial-decisions.json").read_text()
        )["decisions"]
        # This existing historical pilot fixture covers only its own source
        # records. Other editorial decisions have independent regressions,
        # and must not force unrelated mock entities into this test.
        fixture_ids = {
            json.loads(path.read_text(encoding="utf-8"))["id"]
            for category in CATS
            for path in (self.root / category / "json").glob("*.json")
        }
        decisions = [d for d in all_decisions if d["source_id"] in fixture_ids]
        report = self.build(decisions)
        self.assertEqual(report["statistics"]["source_records"], 15)
        self.assertEqual(report["statistics"]["index_entities"], 12)
        self.assertEqual(report["statistics"]["quarantined_records"], 3)
        self.assertEqual(report["statistics"]["reviewed_entries"], 10)
        by_id = {row["id"]: row for row in report["entities"]}
        self.assertIn("work:BookOfJashar", by_id)
        self.assertIn("place:PerezUzzah", by_id)
        self.assertIn("person:Uzzah", by_id)
        self.assertNotIn("person:Jashar", by_id)
        self.assertNotIn("person:Hammelech", by_id)
        self.assertNotIn("person:Philistine", by_id)
        self.assertNotIn("person:Shiloh", by_id)
        self.assertEqual(by_id["place:Gadara"]["canonical_id"], "place:Gadara")
        self.assertEqual(by_id["place:Gadara"]["source_primary_id"],
                         "place:Gerasa")
        self.assertEqual(by_id["place:Gerasa"]["canonical_id"], "place:Gerasa")
        self.assertEqual(by_id["place:Gadara.2"]["canonical_id"], "place:Gadara.2")
        self.assertEqual(
            report["by_word"]["sblgnt:n40008028011"],
            [{"entity_id": "place:Gadara", "link_type": "explicit_instances"},
             {"entity_id": "place:Gerasa", "link_type": "explicit_instances"}])
        self.assertEqual(by_id["place:Gadara"]["occurrences"]
                         ["explicit_instances"]["SBLGNT"], [["n40008028011"]])
        self.assertEqual(by_id["person:Johanan"]["canonical_id"],
                         "person:Johanan")
        self.assertEqual(by_id["person:Shallum.5"]["canonical_id"],
                         "person:Jehoahaz.3")
        self.assertEqual(by_id["person:Shallum.5"]["source_primary_id"],
                         "person:Shallum.5")
        self.assertEqual(by_id["person:Shallum.5"]["occurrences"]
                         ["explicit_instances"]["wlc"], [["o130030150101"]])
        self.assertEqual(report["by_word"]["wlc:o130030150101"],
                         [{"entity_id": "person:Shallum.5",
                           "link_type": "explicit_instances"}])
        self.assertEqual(by_id["person:Johanan"]["source_primary_id"],
                         "person:Jehoahaz.3")
        self.assertEqual(by_id["person:Jehoahaz.3"]["occurrences"]
                         ["explicit_instances"]["wlc"], [["o120230300131"]])
        self.assertEqual(report["by_word"]["wlc:o130030150041"],
                         [{"entity_id": "person:Johanan",
                           "link_type": "explicit_instances"}])
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

    def test_hur_father_name_excludes_lexical_ben_but_son_keeps_compound(self):
        father = self.write_record(
            "people", "Hur", references=["11004008"],
            explicit_instances={"wlc":[["o110040080031","o110040080041"]]})
        son = self.write_record(
            "people", "Ben-hur", references=["11004008"],
            explicit_instances={"wlc":[["o110040080031","o110040080041"]]})
        original = (father.read_bytes(), son.read_bytes())
        review = next(row for row in json.loads(
            Path(__file__).with_name("editorial-decisions.json").read_text()
        )["decisions"] if row["source_id"]=="person:Hur")
        index = self.build(decisions=[review])
        by_id={entry["id"]:entry for entry in index["entities"]}
        self.assertEqual(by_id["person:Hur"]["occurrences"]
                         ["explicit_instances"]["wlc"],[["o110040080041"]])
        self.assertEqual(by_id["person:Ben-hur"]["occurrences"]
                         ["explicit_instances"]["wlc"],
                         [["o110040080031","o110040080041"]])
        self.assertEqual(index["by_word"]["wlc:o110040080031"],
                         [{"entity_id":"person:Ben-hur","link_type":"explicit_instances"}])
        self.assertEqual(index["by_word"]["wlc:o110040080041"],
                         [{"entity_id":"person:Ben-hur","link_type":"explicit_instances"},
                          {"entity_id":"person:Hur","link_type":"explicit_instances"}])
        self.assertEqual((father.read_bytes(),son.read_bytes()),original)
        with self.assertRaisesRegex(ValueError,"absent group cannot be removed"):
            self.build(decisions=[dict(review,remove_explicit_instances={
                "wlc":[["o110040080031"]]})])

    def test_bebai_family_ancestor_and_zechariah_father_are_distinct_word_mentions(self):
        ancestor = self.write_record(
            "people", "Bebai", references=["15002011", "15008011"],
            explicit_instances={"wlc":[
                ["o150020110021"],["o150080110021"],["o150080110051"]]})
        father = self.write_record(
            "people", "Bebai.2", references=["15008011"],
            explicit_instances={"wlc":[
                ["o150080110021"],["o150080110051"]]})
        source_before = (ancestor.read_bytes(), father.read_bytes())
        editorial = json.loads(
            Path(__file__).with_name("editorial-decisions.json").read_text()
        )["decisions"]
        decisions = [row for row in editorial
                     if row["source_id"] in ("person:Bebai", "person:Bebai.2")]
        self.assertEqual(len(decisions), 2)
        report = self.build(decisions=decisions)
        by_id = {entity["id"]:entity for entity in report["entities"]}
        self.assertEqual(
            by_id["person:Bebai"]["occurrences"]["explicit_instances"]["wlc"],
            [["o150020110021"],["o150080110021"]])
        self.assertEqual(
            by_id["person:Bebai.2"]["occurrences"]["explicit_instances"]["wlc"],
            [["o150080110051"]])
        self.assertEqual(report["by_word"]["wlc:o150080110021"],
                         [{"entity_id":"person:Bebai","link_type":"explicit_instances"}])
        self.assertEqual(report["by_word"]["wlc:o150080110051"],
                         [{"entity_id":"person:Bebai.2","link_type":"explicit_instances"}])
        self.assertEqual(by_id["person:Bebai"]["references"],
                         ["15002011","15008011"])
        self.assertEqual(by_id["person:Bebai.2"]["references"],["15008011"])
        self.assertEqual((ancestor.read_bytes(),father.read_bytes()),source_before)

    def test_distinct_dishon_people_keep_exact_sources_and_avoid_false_collisions(self):
        elder = self.write_record(
            "people", "Dishon",
            references=["13001038", "13001041", "01036026"],
            explicit_instances={"wlc": [
                ["o130010380072"], ["o130010410031"],
                ["o130010410051"], ["o010360260031"]]})
        younger = self.write_record(
            "people", "Dishon.2",
            references=["13001041"],
            explicit_instances={"wlc": [
                ["o130010410031"], ["o130010410051"]]})
        unchanged = (elder.read_bytes(), younger.read_bytes())
        decision = next(
            d for d in json.loads(
                Path(__file__).with_name("editorial-decisions.json").read_text()
            )["decisions"]
            if d["source_id"] == "person:Dishon"
        )
        report = self.build(decisions=[decision])
        by_id = {e["id"]: e for e in report["entities"]}
        self.assertEqual(by_id["person:Dishon"]["references"],
                         ["13001038", "01036026"])
        self.assertEqual(by_id["person:Dishon"]["occurrences"]
                         ["explicit_instances"]["wlc"],
                         [["o130010380072"], ["o010360260031"]])
        self.assertEqual(by_id["person:Dishon.2"]["references"], ["13001041"])
        self.assertEqual(report["by_word"]["wlc:o130010410031"],
                         [{"entity_id": "person:Dishon.2",
                           "link_type": "explicit_instances"}])
        self.assertEqual(report["by_word"]["wlc:o130010410051"],
                         [{"entity_id": "person:Dishon.2",
                           "link_type": "explicit_instances"}])
        self.assertIn("wlc:o010360260031", report["by_word"])
        self.assertEqual((elder.read_bytes(), younger.read_bytes()), unchanged)

        with self.assertRaisesRegex(ValueError, "cannot remove missing"):
            self.build(decisions=[
                dict(decision, remove_references=["13001042"])])
        with self.assertRaisesRegex(ValueError, "invalid removed verse"):
            self.build(decisions=[
                dict(decision, remove_references=["invalid"])])

    def test_real_acai_greek_field_name_is_indexed_under_canonical_corpus(self):
        original = self.write_record(
            "people", "Phoebe", references=["45016001"],
            explicit_instances={"SBLGNT": [["n45016001004"]]})
        before = original.read_bytes()
        report = self.build()
        self.assertEqual(report["entities"][0]["occurrences"]
                         ["explicit_instances"]["SBLGNT"], [["n45016001004"]])
        self.assertEqual(report["by_word"]["sblgnt:n45016001004"],
                         [{"entity_id": "person:Phoebe",
                           "link_type": "explicit_instances"}])
        self.assertNotIn("SBLGNT:n45016001004", report["by_word"])
        self.assertEqual(original.read_bytes(), before)
        self.lock["source_corpora"] = {"wlc": "wlc"}
        with self.assertRaisesRegex(ValueError, "Unrecognized original source corpus"):
            self.build()
        self.lock["source_corpora"] = {"wlc": "wlc", "SBLGNT": "wlc"}
        with self.assertRaisesRegex(ValueError, "word prefix incompatible"):
            self.build()
        self.lock["source_corpora"] = {"wlc": "wlc", "SBLGNT": "sblgnt"}
        original = self.root / "people" / "json" / "Phoebe.json"
        value = json.loads(original.read_text(encoding="utf-8"))
        value["explicit_instances"]["SBLGNT"] = [["n45016001004suffix"]]
        original.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "malformed original word ID"):
            self.build()

    def test_pinned_absent_word_is_quarantined_from_lookup_not_source(self):
        path = self.write_record(
            "people", "GenericMale", references=["02002013"],
            subject_referents={"wlc": [
                ["o020020130103"], ["o020020130103"]]})
        before = path.read_bytes()
        audit = {
            "schema_version": 1, "corpus": "wlc",
            "source_edition": "pinned-test",
            "provenance": [{"source": "pinned-source-check", "finding": "absent"}],
            "word_ids": ["o020020130103"],
        }
        report = self.build(source_absences=audit)
        self.assertEqual(report["statistics"]["unattested_distinct_source_words"], 1)
        self.assertEqual(report["statistics"]["unattested_raw_word_assignments"], 2)
        self.assertNotIn("wlc:o020020130103", report["by_word"])
        self.assertEqual(
            report["unattested_source_words"]["wlc:o020020130103"]
                  ["source_claims"],
            [{"entity_id": "person:GenericMale", "link_type": "subject_referents"}],
        )
        self.assertEqual(report["entities"][0]["occurrences"]["subject_referents"]
                         ["wlc"], [["o020020130103"], ["o020020130103"]])
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

    def test_source_reference_qualifications_preserve_variant_and_subscription(self):
        bethabara = self.write_record(
            "places", "Bethabara", references=["43001028"])
        phoebe = self.write_record(
            "people", "Phoebe", references=["45016001", "45016027"],
            explicit_instances={"SBLGNT": [["n45016001004"]]})
        before = (bethabara.read_bytes(), phoebe.read_bytes())
        claim_manifest = {
            "schema_version": 1, "corpus": "sblgnt",
            "source_edition": "pinned-test",
            "claims": [
                {"source_id": "place:Bethabara", "verse_id": "43001028",
                 "classification": "textual_variant_name_not_in_pinned_edition",
                 "evidence": ["Greek pinned source says Bethany"]},
                {"source_id": "person:Phoebe", "verse_id": "45016027",
                 "classification": "traditional_subscription_candidate",
                 "evidence": ["No Phoebe in canonical last verse"]},
            ],
        }
        result = self.build(reference_qualifications=claim_manifest)
        self.assertEqual(result["statistics"]["qualified_source_reference_claims"], 2)
        qualified = result["qualified_source_references"]
        self.assertEqual(qualified["sblgnt:43001028"][0]["entity_id"],
                         "place:Bethabara")
        self.assertEqual(qualified["sblgnt:45016027"][0]["classification"],
                         "traditional_subscription_candidate")
        self.assertEqual(result["entities"][0]["references"], ["45016001", "45016027"])
        self.assertEqual(result["by_word"]["sblgnt:n45016001004"][0]["entity_id"],
                         "person:Phoebe")
        self.assertEqual((bethabara.read_bytes(), phoebe.read_bytes()), before)
        with self.assertRaisesRegex(ValueError, "Duplicate reference qualification"):
            self.build(reference_qualifications=dict(
                claim_manifest, claims=claim_manifest["claims"] * 2))
        with self.assertRaisesRegex(ValueError, "not pinned"):
            self.build(reference_qualifications=dict(
                claim_manifest, source_edition="other"))
        with self.assertRaisesRegex(ValueError, "no source reference"):
            self.build(reference_qualifications=dict(
                claim_manifest, claims=[dict(
                    claim_manifest["claims"][1], verse_id="45016025")]))
        with self.assertRaisesRegex(ValueError, "absent index record"):
            self.build(reference_qualifications=dict(
                claim_manifest, claims=[dict(
                    claim_manifest["claims"][1], source_id="person:Unknown")]))
        changed = json.loads(phoebe.read_text(encoding="utf-8"))
        changed["explicit_instances"]["SBLGNT"].append(["n45016027001"])
        phoebe.write_text(json.dumps(changed), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "conflicts with exact original word anchor"):
            self.build(reference_qualifications=claim_manifest)

    def test_distinguish_edition_apparatus_from_alternate_verse_numbering(self):
        original=self.write_record(
            "people","A",references=["45016027","47013014"])
        unchanged=original.read_bytes()
        manifest={
            "schema_version":1,"corpus":"sblgnt","source_edition":"pinned-test",
            "verse_ids":["45016027","47013014"],
            "provenance":[{"source":"pinned edition inventory"}],
            "verse_qualifications":[
                {
                    "verse_id":"45016027",
                    "classification":"doxology_in_edition_apparatus_not_main_word_inventory",
                    "explanation":"A doxology in the alternate edition apparatus",
                    "evidence":["Pinned Greek source end","SBL main/apparatus comparison"],
                },
                {
                    "verse_id":"47013014",
                    "classification":"alternate_verse_number_for_final_benediction",
                    "explanation":"The final benediction bears another verse number",
                    "equivalent_benediction_source_verse":"47013013",
                    "evidence":["Pinned Greek end","Alternative numbered edition"],
                },
            ],
        }
        result=self.build(source_verse_absences=manifest)
        self.assertEqual(result["statistics"]["qualified_source_verse_contexts"],2)
        self.assertEqual(
            result["unattested_source_verses"]["sblgnt:47013014"]["source_context"]
            ["equivalent_benediction_source_verse"],"47013013")
        self.assertEqual(
            result["unattested_source_verses"]["sblgnt:45016027"]["source_context"]
            ["classification"],
            "doxology_in_edition_apparatus_not_main_word_inventory")
        self.assertEqual(result["entities"][0]["references"],
                         ["45016027","47013014"])
        self.assertEqual(original.read_bytes(),unchanged)
        with self.assertRaisesRegex(ValueError,"Unqualified pinned source verses"):
            self.build(source_verse_absences=dict(
                manifest,verse_qualifications=manifest["verse_qualifications"][:1]))
        with self.assertRaisesRegex(ValueError,"Duplicate source verse qualification"):
            self.build(source_verse_absences=dict(
                manifest,verse_qualifications=manifest["verse_qualifications"]*2))
        with self.assertRaisesRegex(ValueError,"Invalid verse-number comparison"):
            self.build(source_verse_absences=dict(
                manifest,verse_qualifications=[
                    manifest["verse_qualifications"][0],
                    dict(manifest["verse_qualifications"][1],
                         equivalent_benediction_source_verse="45016027"),
                ]))
        with self.assertRaisesRegex(ValueError,"Invalid source verse-qualification evidence"):
            self.build(source_verse_absences=dict(
                manifest,verse_qualifications=[
                    dict(manifest["verse_qualifications"][0],evidence=[]),
                    manifest["verse_qualifications"][1],
                ]))
        with self.assertRaisesRegex(ValueError,"Invalid source verse-qualification evidence"):
            self.build(source_verse_absences=dict(
                manifest,verse_qualifications=[
                    dict(manifest["verse_qualifications"][0],
                         classification="all_verses_spurious"),
                    manifest["verse_qualifications"][1],
                ]))

    def test_source_verse_absence_only_qualifies_raw_references(self):
        original = self.write_record(
            "people", "A", references=["47013014", "45016027", "43001001"])
        self.write_record("places", "B", references=["47013014"])
        before = original.read_bytes()
        audit = {
            "schema_version": 1, "corpus": "sblgnt",
            "source_edition": "pinned-test",
            "verse_ids": ["47013014", "45016027"],
            "provenance": [{"source": "pinned Greek source verse scan"}],
        }
        report = self.build(source_verse_absences=audit)
        self.assertEqual(report["statistics"]["unattested_source_verses"], 2)
        self.assertEqual(
            report["statistics"]["unattested_source_verse_reference_claims"], 3)
        claims = report["unattested_source_verses"]["sblgnt:47013014"]
        self.assertEqual(claims["source_reference_claims"],
                         ["person:A", "place:B"])
        self.assertEqual(claims["scope"],
                         "absent_from_pinned_original_word_inventory_only")
        self.assertEqual(report["entities"][0]["references"],
                         ["47013014", "45016027", "43001001"])
        self.assertEqual(original.read_bytes(), before)

        with self.assertRaisesRegex(ValueError, "not pinned"):
            self.build(source_verse_absences=dict(audit, source_edition="other"))
        with self.assertRaisesRegex(ValueError, "Duplicate source-absent verse"):
            self.build(source_verse_absences=dict(
                audit, verse_ids=["47013014", "47013014"]))
        with self.assertRaisesRegex(ValueError, "not referenced"):
            self.build(source_verse_absences=dict(audit, verse_ids=["47013013"]))
        with self.assertRaisesRegex(ValueError, "source audit provenance"):
            self.build(source_verse_absences=dict(audit, provenance=[]))

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

    def test_exact_snapshot_hash_catches_unchanged_count_with_modified_data(self):
        path = self.write_record(
            "people", "A",
            references=["01001001"],
            explicit_instances={"wlc": [["o010010010011"]]})
        original_bytes = path.read_bytes()
        baseline = self.build()
        digest = baseline["provenance"]["source_snapshot_sha256"]
        self.assertEqual(len(digest), 64)
        self.assertEqual(digest, self.build()["provenance"]["source_snapshot_sha256"])
        # The real source lock pins this expected fingerprint. A synthetic
        # fixture can pin its own fingerprint to test fail-closed behavior.
        self.lock["source_snapshot_sha256"] = digest
        self.assertEqual(self.build()["provenance"]["source_snapshot_sha256"], digest)
        tampered = json.loads(path.read_text(encoding="utf-8"))
        tampered["references"].append("01001002")
        path.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "source snapshot digest mismatch"):
            self.build()
        path.write_bytes(original_bytes)
        self.assertEqual(self.build()["provenance"]["source_snapshot_sha256"], digest)
        with self.assertRaisesRegex(ValueError, "Invalid pinned original JSON"):
            self.lock["source_snapshot_sha256"] = "broken"
            self.build()

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
