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
from normalize_bible_references import ReviewError, run  # noqa: E402

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

    def apply(self, output=None):
        return run(cleaned_path=self.cleaned, usfx_zip=self.original,
                   manifest_path=self.manifest, crosswalk_path=self.crosswalk,
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

    def test_missing_introduction_endpoint_blocks(self):
        self.fixture(include_last=False)
        with self.assertRaisesRegex(ReviewError, "Unattested introduction end"):
            self.apply()

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
