"""Offline proof that USFX reference normalization is source-bound and byte-safe."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from normalize_bible_references import ReviewError, run, _intro_target, _complete_printed_destinations  # noqa: E402

NS = "http://www.bibletechnologies.net/2003/OSIS/namespace"


def example(clean_origin="1.1", original_origin="1.1",
            clean_dest="Ps 2:1; 3:1.", original_dest="Ps 2:1; 3:1.",
            intro="1:1–2:1", note_ref='', include_last=True):
    verses = ('<chapter osisID="Gen.1"><verse osisID="Gen.1.1">One</verse>'
              '<verse osisID="Gen.1.2">Two</verse></chapter>'
              '<chapter osisID="Gen.2"><verse osisID="Gen.2.1">Three</verse></chapter>'
              if include_last else
              '<chapter osisID="Gen.1"><verse osisID="Gen.1.1">One</verse>'
              '<verse osisID="Gen.1.2">Two</verse></chapter>')
    osis = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<osis xmlns="{NS}"><osisText osisIDWork="Demo" osisRefWork="Bible">'
        '<header/><div type="book" osisID="Gen">'
        + verses +
        '<p><note type="crossReference" n="a">'
        '<reference type="annotateRef" subType="x-origin"' + note_ref + '>'
        + clean_origin + ' </reference>'
        '<reference>' + clean_dest + '</reference></note></p>'
        '<div type="introduction"><list><item><reference subType="x-introduction">'
        + intro + '</reference></item></list></div></div>'
        '</osisText></osis>'
    )
    usfx = (
        '<usfx><book id="GEN"><p><x caller="a"><xo>'
        + original_origin + '</xo><xt>' + original_dest +
        '</xt></x></p><p><ior>' + intro + '</ior></p></book></usfx>'
    )
    return osis.encode(), usfx.encode()


class NormalizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cleaned = self.root / "master.xml"
        self.original = self.root / "original.zip"
        self.manifest = self.root / "manifest.json"
        self.crosswalk = self.root / "book-map.json"
        self.crosswalk.write_text(json.dumps(
            {"books": [{"usfm": "GEN", "osis": "Gen"}]}), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, **kw):
        source, usfx = example(**kw)
        self.cleaned.write_bytes(source)
        with ZipFile(self.original, "w") as archive:
            archive.writestr("demo_usfx.xml", usfx)
        self.manifest.write_text(json.dumps({
            "cleaned_osis_sha256": sha256(source).hexdigest(),
            "original_usfx_sha256": sha256(self.original.read_bytes()).hexdigest(),
        }))
        return source

    def aliases(self):
        path = self.root / "printed-aliases.json"
        path.write_text(json.dumps({
            "schema_version": 1,
            "crosswalk": "config/standard_usfm_osis_66.json",
            "printed_sources": ["https://example.org/printed-page"],
            "aliases": {"Ge": "Gen"},
        }))
        return path

    def apply(self, output=None, aliases=None, complete_lists=False):
        return run(cleaned_path=self.cleaned, usfx_zip=self.original,
                   manifest_path=self.manifest, crosswalk_path=self.crosswalk,
                   destination_aliases_path=aliases,
                   complete_citation_lists=complete_lists,
                   output_path=output)

    def test_preserves_every_original_byte_except_verified_additions(self):
        source = self.fixture()
        candidate, report = self.apply(output=self.root / "candidate.xml")
        self.assertEqual(self.cleaned.read_bytes(), source)
        self.assertEqual((self.root / "candidate.xml").read_bytes(), candidate)
        self.assertIn(b'osisRef="Gen.1.1"', candidate)
        self.assertIn(b'osisRef="Gen.1.1-Gen.2.1"', candidate)
        self.assertEqual(report["candidate_additions"], 2)
        self.assertEqual(report["original_cross_reference_notes"], 1)
        self.assertEqual(report["original_introduction_spans"], 1)
        self.assertEqual(report["unlinked_original_destination_labels_preserved"], 1)
        self.assertIn(b'<reference>Ps 2:1; 3:1.</reference>', candidate)
        self.assertEqual(
            "".join(etree.fromstring(source).itertext()),
            "".join(etree.fromstring(candidate).itertext()),
        )

    def test_idempotent_after_updating_exact_candidate_manifest_hash(self):
        self.fixture()
        candidate, _ = self.apply()
        self.cleaned.write_bytes(candidate)
        manifest = json.loads(self.manifest.read_text())
        manifest["cleaned_osis_sha256"] = sha256(candidate).hexdigest()
        self.manifest.write_text(json.dumps(manifest))
        twice, report = self.apply()
        self.assertEqual(twice, candidate)
        self.assertEqual(report["candidate_additions"], 0)

    def test_attested_em_dash_and_dot_endpoints_are_resolved(self):
        target = _intro_target("1:57—2.40", "Luke", {
            "Luke.1.57", "Luke.2.40",
        })
        self.assertEqual(target, "Luke.1.57-Luke.2.40")

    def test_single_chapter_verse_ranges_do_not_imply_other_books(self):
        self.assertEqual(_intro_target("1-3", "Phlm", {
            "Phlm.1.1", "Phlm.1.3",
        }), "Phlm.1.1-Phlm.1.3")
        with self.assertRaises(ReviewError):
            _intro_target("1-3", "Gen", {
                "Gen.1.1", "Gen.1.3", "Gen.2.1",
            })

    def test_chapter_only_section_pointer_is_supported(self):
        self.assertEqual(_intro_target("5", "John", {
            "John.4.1", "John.5.1",
        }), "John.5")

    def test_mixed_narrative_introduction_label_is_not_invented(self):
        source = self.fixture(intro="1:1–2:1 (voir un autre passage)")
        candidate, report = self.apply()
        self.assertEqual(report["unlinked_introduction_spans_preserved"], 1)
        self.assertEqual(report["resolved_introduction_spans"], 0)
        self.assertEqual(report["candidate_additions"], 1)
        self.assertIn(b' subType="x-introduction">', candidate)
        self.assertIn("1:1–2:1 (voir un autre passage)".encode(), candidate)
        self.assertEqual(source.count(b' osisRef="'), 0)

    def test_exact_printed_single_destination_is_source_verified(self):
        self.fixture(clean_dest="Ge 1:2.", original_dest="Ge 1:2.")
        candidate, report = self.apply(aliases=self.aliases())
        self.assertIn(b'<reference osisRef="Gen.1.2">Ge 1:2.</reference>', candidate)
        self.assertEqual(report["resolved_original_destination_labels"], 1)
        self.assertEqual(report["resolved_destination_target_tokens"], 1)
        self.assertEqual(report["multi_target_reference_labels"], 0)
        self.assertEqual(report["unlinked_original_destination_labels_preserved"], 0)
        self.assertEqual(report["candidate_additions"], 3)

    def test_printed_single_destination_idempotence(self):
        self.fixture(clean_dest="Ge 1:2.", original_dest="Ge 1:2.")
        aliases = self.aliases()
        candidate, report = self.apply(aliases=aliases)
        self.cleaned.write_bytes(candidate)
        manifest = json.loads(self.manifest.read_text())
        manifest["cleaned_osis_sha256"] = sha256(candidate).hexdigest()
        self.manifest.write_text(json.dumps(manifest))
        twice, report = self.apply(aliases=aliases)
        self.assertEqual(candidate, twice)
        self.assertEqual(report["candidate_additions"], 0)

    def test_explicit_printed_range_requires_both_real_verses(self):
        self.fixture(clean_dest="Ge 1:1-2.", original_dest="Ge 1:1-2.")
        candidate, report = self.apply(aliases=self.aliases())
        self.assertIn(b'osisRef="Gen.1.1-Gen.1.2">Ge 1:1-2.', candidate)
        self.assertEqual(report["resolved_original_destination_labels"], 1)

    def test_printed_compound_label_never_receives_partial_link(self):
        self.fixture(clean_dest="Ge 1:2. Ps 3:1.",
                     original_dest="Ge 1:2. Ps 3:1.")
        candidate, report = self.apply(aliases=self.aliases())
        self.assertIn(b'<reference>Ge 1:2. Ps 3:1.</reference>', candidate)
        self.assertEqual(report["resolved_original_destination_labels"], 0)
        self.assertEqual(report["unlinked_original_destination_labels_preserved"], 1)
        self.assertEqual(report["candidate_additions"], 2)

    def test_unknown_abbreviation_or_missing_verse_is_not_guessed(self):
        for printed in ("Gé 1:2.", "Ge 1:99.", "Ge 1:2-99.",
                        "Ge 1:2; 2.", "v. 2."):
            with self.subTest(printed=printed):
                self.fixture(clean_dest=printed, original_dest=printed)
                candidate, report = self.apply(aliases=self.aliases())
                self.assertEqual(report["resolved_original_destination_labels"], 0)
                self.assertEqual(report["candidate_additions"], 2)
                self.assertIn(("<reference>"+printed+"</reference>").encode(),
                              candidate)

    def test_printed_crosswalk_must_cover_exact_approved_books(self):
        self.fixture(clean_dest="Ge 1:2.", original_dest="Ge 1:2.")
        alias_path = self.aliases()
        doc = json.loads(alias_path.read_text())
        doc["aliases"] = {"Ge": "Exod"}
        alias_path.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ReviewError, "one-to-one"):
            self.apply(aliases=alias_path)

    def test_existing_conflicting_destination_is_blocked(self):
        self.fixture(clean_dest="Ge 1:2.", original_dest="Ge 1:2.")
        clean = self.cleaned.read_bytes().replace(
            b"<reference>Ge 1:2.</reference>",
            b'<reference osisRef="Gen.1.1">Ge 1:2.</reference>')
        self.cleaned.write_bytes(clean)
        manifest = json.loads(self.manifest.read_text())
        manifest["cleaned_osis_sha256"] = sha256(clean).hexdigest()
        self.manifest.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ReviewError, "conflicts"):
            self.apply(aliases=self.aliases())

    def test_full_compound_book_list_maps_every_explicit_printed_part(self):
        targets = {"Gen.1.1", "Exod.2.1"}
        linked, reason, context = _complete_printed_destinations(
            "Ge 1:1. Ex 2:1.", {"Ge":"Gen", "Ex":"Exod"}, targets)
        self.assertEqual(linked, "Gen.1.1 Exod.2.1")
        self.assertEqual(reason, "complete_printed_list")
        self.assertEqual(context, 0)

    def test_full_semicolon_context_and_comma_repetition(self):
        targets={"Gen.1.1", "Gen.1.2", "Gen.2.1"}
        linked, reason, context = _complete_printed_destinations(
            "Ge 1:1, 2; 2:1.", {"Ge":"Gen"}, targets)
        self.assertEqual(linked, "Gen.1.1 Gen.1.2 Gen.2.1")
        self.assertEqual(context, 1)
        self.assertEqual(reason, "complete_printed_list")

    def test_every_missing_explicit_or_contextual_target_refuses_entire_note(self):
        labels = (
            "Ge 1:1. Ex 2:99.", "Ge 1:1, 99.", "Ge 1:1; 2:99.",
            "Ge 1:1. Unknown 2:1.", "Ge 1:1; v. 2.",
            "Ge 1:1, etc.", "Ge 1:2, 1:1.",
        )
        aliases = {"Ge":"Gen","Ex":"Exod"}
        verses={"Gen.1.1","Gen.1.2","Gen.2.1","Exod.2.1"}
        for label in labels:
            with self.subTest(label=label):
                linked, reason, _ = _complete_printed_destinations(
                    label, aliases, verses)
                self.assertIsNone(linked)
                self.assertNotEqual(reason, "complete_printed_list")

    def test_multi_target_list_writes_only_one_safe_reference_attribute(self):
        original = self.fixture(clean_dest="Ge 1:1, 2; 2:1.",
                                original_dest="Ge 1:1, 2; 2:1.")
        candidate, report = self.apply(aliases=self.aliases(), complete_lists=True)
        self.assertEqual(report["resolved_original_destination_labels"], 1)
        self.assertEqual(report["resolved_destination_target_tokens"], 3)
        self.assertEqual(report["multi_target_reference_labels"], 1)
        self.assertEqual(report["explicit_semicolon_contexts_used"], 1)
        self.assertEqual(report["candidate_additions"], 3)
        self.assertIn(
            b'osisRef="Gen.1.1 Gen.1.2 Gen.2.1">Ge 1:1, 2; 2:1.',
            candidate)
        self.assertEqual("".join(etree.fromstring(original).itertext()),
                         "".join(etree.fromstring(candidate).itertext()))

    def test_multi_target_compilation_candidate_is_idempotent(self):
        self.fixture(clean_dest="Ge 1:1. Ge 1:2.",
                     original_dest="Ge 1:1. Ge 1:2.")
        aliases = self.aliases()
        first, report = self.apply(aliases=aliases, complete_lists=True)
        self.assertEqual(report["resolved_original_destination_labels"], 1)
        self.cleaned.write_bytes(first)
        manifest = json.loads(self.manifest.read_text())
        manifest["cleaned_osis_sha256"] = sha256(first).hexdigest()
        self.manifest.write_text(json.dumps(manifest))
        second, report = self.apply(aliases=aliases, complete_lists=True)
        self.assertEqual(first, second)
        self.assertEqual(report["candidate_additions"], 0)

    def test_complete_list_mode_requires_printed_witness(self):
        self.fixture()
        with self.assertRaisesRegex(ReviewError, "require a pinned"):
            self.apply(complete_lists=True)

    def test_real_1910_printed_table_has_unambiguous_full_book_identity(self):
        source = json.loads(
            (ROOT / "config/lsg-1910-printed-book-aliases.json").read_text(
                encoding="utf-8"))
        crosswalk = json.loads(
            (ROOT / "config/standard_usfm_osis_66.json").read_text(
                encoding="utf-8"))
        mapping = source["aliases"]
        self.assertEqual(len(mapping), 66)
        self.assertEqual(len(set(mapping.values())), 66)
        self.assertEqual(set(mapping.values()),
                         {entry["osis"] for entry in crosswalk["books"]})
        self.assertEqual(mapping["Ph"], "Phil")
        self.assertEqual(mapping["Phm"], "Phlm")
        self.assertEqual(mapping["Ma"], "Mal")
        self.assertEqual(mapping["Jé"], "Jer")
        self.assertEqual(mapping["1 Co"], "1Cor")
        self.assertEqual(mapping["2 Co"], "2Cor")
        self.assertNotIn("Mal", mapping)  # not the printed 1910 abbreviation

    def test_provider_variant_is_distinct_from_printed_alias_and_pinned(self):
        self.fixture(clean_dest="Gen 1:2.", original_dest="Gen 1:2.")
        path = self.aliases()
        doc = json.loads(path.read_text())
        doc["source_attested_digital_variants"] = {
            "status": "source_provider_spelling_not_printed_edition_abbreviation",
            "witness_usfx_zip_sha256": sha256(self.original.read_bytes()).hexdigest(),
            "evidence": "Source-original contains this unambiguous alternate spelling.",
            "aliases": {"Gen": "Gen"},
        }
        self.assertNotIn("Gen", doc["aliases"])
        path.write_text(json.dumps(doc))
        candidate, report = self.apply(aliases=path, complete_lists=True)
        self.assertIn(b'osisRef="Gen.1.2">Gen 1:2.</reference>', candidate)
        self.assertEqual(report["resolved_original_destination_labels"], 1)
        self.assertEqual(report["unlinked_original_destination_labels_preserved"], 0)

        doc["source_attested_digital_variants"]["witness_usfx_zip_sha256"] = "0" * 64
        path.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ReviewError, "pinned original evidence"):
            self.apply(aliases=path, complete_lists=True)

    def test_provider_alias_must_actually_appear_in_original_citations(self):
        self.fixture(clean_dest="Ge 1:2.", original_dest="Ge 1:2.")
        path = self.aliases()
        doc = json.loads(path.read_text())
        doc["source_attested_digital_variants"] = {
            "status": "source_provider_spelling_not_printed_edition_abbreviation",
            "witness_usfx_zip_sha256": sha256(self.original.read_bytes()).hexdigest(),
            "evidence": "The correct pinned original must contain the supposed abbreviation in a real citation.",
            "aliases": {"Gen": "Gen"},
        }
        path.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ReviewError, "not present in original citation"):
            self.apply(aliases=path, complete_lists=True)

    def test_provider_variant_cannot_override_printed_alias(self):
        self.fixture()
        path = self.aliases()
        doc = json.loads(path.read_text())
        doc["source_attested_digital_variants"] = {
            "status": "source_provider_spelling_not_printed_edition_abbreviation",
            "witness_usfx_zip_sha256": sha256(self.original.read_bytes()).hexdigest(),
            "evidence": "An alternate spelling has independently checked source evidence.",
            "aliases": {"Ge": "Gen"},
        }
        path.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ReviewError, "ambiguous provider-specific"):
            self.apply(aliases=path, complete_lists=True)

    def test_wrong_source_sha_blocks(self):
        self.fixture()
        self.manifest.write_text('{"cleaned_osis_sha256": "wrong"}')
        with self.assertRaises(ReviewError):
            self.apply()

    def test_mismatched_printed_destinations_block(self):
        self.fixture(original_dest="Ps 99:99.")
        with self.assertRaisesRegex(ReviewError, "Mismatch in callout"):
            self.apply()

    def test_mismatched_origin_blocks(self):
        self.fixture(original_origin="1.2")
        with self.assertRaisesRegex(ReviewError, "Mismatch in callout"):
            self.apply()

    def test_unrecognized_origin_is_not_guessed(self):
        self.fixture(original_origin="ch.1", clean_origin="ch.1")
        with self.assertRaisesRegex(ReviewError, "Unrecognized"):
            self.apply()

    def test_missing_introduction_endpoint_is_preserved_and_reported(self):
        original = self.fixture(include_last=False)
        candidate, report = self.apply()
        self.assertEqual(report["candidate_additions"], 1)
        self.assertEqual(report["unlinked_introduction_spans_preserved"], 1)
        self.assertEqual(report["unresolved_source_introduction_spans"][0]["reason"], "unattested_end")
        self.assertIn(b'<reference subType="x-introduction">', candidate)
        self.assertIn(b'osisRef="Gen.1.1"', candidate)
        self.assertEqual("".join(etree.fromstring(original).itertext()),
                         "".join(etree.fromstring(candidate).itertext()))

    def test_reversed_introduction_range_blocks(self):
        self.fixture(intro="2:1–1:1")
        with self.assertRaisesRegex(ReviewError, "Reversed introduction range"):
            self.apply()

    def test_source_conflict_blocks(self):
        self.fixture(note_ref=' osisRef="Exod.2.1"')
        with self.assertRaisesRegex(ReviewError, "Origin conflicts"):
            self.apply()

    def test_wrong_book_mapping_blocks(self):
        self.fixture()
        self.crosswalk.write_text('{"books":[{"usfm":"GEN","osis":"Exod"}]}')
        with self.assertRaisesRegex(ReviewError, "book identity"):
            self.apply()

    def test_refuse_to_overwrite_existing_cleaned_master(self):
        self.fixture()
        with self.assertRaisesRegex(ReviewError, "Refusing to overwrite"):
            self.apply(output=self.cleaned)


if __name__ == "__main__":
    unittest.main()
