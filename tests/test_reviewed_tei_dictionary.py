"""Fail-closed source/TEI/native proof tests, independent of an actual edition."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reviewed_tei_dictionary import dictionary_proof_errors


class DictionaryProofTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.folder = self.root / "modules" / "sample"
        self.payload = self.folder / "payload"
        self.metadata = {
            "category": "dictionary", "sword_id": "DEMO", "version": "1.0.0",
            "canonical_edition_id": "sample-dictionary-edition",
            "origin": {"url": "https://github.com/example/example/releases/tag/v1.0.0"},
            "quality": {"smoke_key": "ALPHA"},
        }
        self.conf = {"SourceType": "TEI", "ModDrv": "zLD", "CompressType": "ZIP",
                     "DataPath": "./modules/lexdict/zld/demo/dict"}
        self.policy = {"schema_version": 1, "standard": "TEI P5",
                       "version": "4.12.0", "rng_sha256": "a"*64,
                       "schematron_sha256": "b"*64}
        self.write(self.root / "config/tei-policy.json", self.policy)
        members = {}
        paths = ["mods.d/demo.conf"] + [
            "modules/lexdict/zld/demo/dict"+ext
            for ext in (".dat", ".idx", ".zdt", ".zdx")]
        for name in paths:
            p = self.payload / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(name.encode())
            members[name] = {"sha256": sha256(p.read_bytes()).hexdigest(),
                             "size_bytes": p.stat().st_size}
        self.proof = {
            "schema_version": 1, "status": "validated", "source_kind": "dictionary",
            "sword_id": "DEMO", "version": "1.0.0",
            "canonical_edition_id": "sample-dictionary-edition",
            "source_sha256": "c"*64, "adapter_sha256": "d"*64,
            "original_archive_sha256": "e"*64, "entry_count": 2,
            "upstream_release": {"url": self.metadata["origin"]["url"],
                "verified_public": True, "draft": False, "prerelease": False,
                "package_sha256": "1"*64, "source_archive_sha256": "2"*64,
                "package_size_bytes": 123},
            "schema_validation": dict(self.policy, source_sha256="c"*64,
                relax_ng_passed=True, schematron_passed=True,
                relax_ng_negative_control_rejected=True,
                schematron_negative_control_rejected=True,
                schematron_positive_counts={"active_patterns": 1, "fired_rules": 2,
                    "failed_assertions": 0, "successful_reports": 0},
                schematron_negative_counts={"failed_assertions": 1, "successful_reports": 0}),
            "native_roundtrip": {"schema_version": 1, "expected_tei_sha256": "d"*64,
                "native_imp_sha256": "3"*64, "expected_keys": 2, "native_keys": 2,
                "native_roundtrip_verified": True,
                **dict.fromkeys(("missing_key_count", "unexpected_key_count", "malformed_count",
                               "unicode_text_mismatch_count", "xml_structure_mismatch_count"), 0)},
            "reader_samples": {key: {"bytes": 10, "sha256": "4"*64}
                               for key in ("ALPHA", "BETA")},
            "evidence_url": "https://github.com/example/example/actions/runs/1",
            "reader_evidence_url": "https://github.com/example/example/actions/runs/2",
            "payload_members": members,
        }

    @staticmethod
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def errors(self, proof=None):
        self.write(self.folder / "SOURCE_VALIDATION.json",
                   self.proof if proof is None else proof)
        return dictionary_proof_errors(self.folder, self.root, self.metadata, self.conf)

    def test_complete_generic_proof(self):
        self.assertEqual(self.errors(), [])

    def test_reject_changed_or_extra_member(self):
        path = self.payload / "modules/lexdict/zld/demo/dict.dat"
        original = path.read_bytes()
        path.write_bytes(b"altered native record")
        self.assertTrue(self.errors())
        path.write_bytes(original)
        (self.payload / "mods.d/extra.conf").write_text("unexpected")
        self.assertTrue(self.errors())

    def test_reject_schema_and_native_mismatches(self):
        for section, field, value in (
            ("schema_validation", "source_sha256", "9"*64),
            ("schema_validation", "rng_sha256", "9"*64),
            ("schema_validation", "schematron_negative_control_rejected", False),
            ("schema_validation", "relax_ng_passed", False),
            ("native_roundtrip", "expected_tei_sha256", "9"*64),
            ("native_roundtrip", "native_keys", 1),
            ("native_roundtrip", "missing_key_count", 1),
            ("native_roundtrip", "xml_structure_mismatch_count", 1),
            ("native_roundtrip", "unicode_text_mismatch_count", 1),
            ("native_roundtrip", "native_roundtrip_verified", False),
            ("upstream_release", "draft", True),
            ("upstream_release", "verified_public", False),
        ):
            with self.subTest(section=section, field=field):
                proof = copy.deepcopy(self.proof)
                proof[section][field] = value
                self.assertTrue(self.errors(proof))

    def test_reject_wrong_identity_format_or_reader_receipt(self):
        for field, value in (("version", "2.0.0"), ("sword_id", "OTHER"),
                             ("source_kind", "bible"), ("reader_samples", {})):
            with self.subTest(field=field):
                proof = copy.deepcopy(self.proof)
                proof[field] = value
                self.assertTrue(self.errors(proof))
        self.conf["SourceType"] = "OSIS"
        self.assertTrue(self.errors())

    def test_missing_proof_fails_closed(self):
        self.assertTrue(dictionary_proof_errors(
            self.folder, self.root, self.metadata, self.conf))


if __name__ == "__main__":
    unittest.main()
