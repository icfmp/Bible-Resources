"""Fail-closed exact-final Darby ZIP identity before Android UI import.

No Android emulator or BPC text is needed by these synthetic tests.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase
from zipfile import ZipFile, ZIP_DEFLATED

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from probe_darby_011_final_android import (
    EXPECTED, FinalDarbyAndroidError, verify_final_candidate,
)


def fixture(root: Path):
    path = root / "BRJND2024-0.1.1.zip"
    parts = {}
    for name in EXPECTED:
        if name.startswith("mods.d/"):
            parts[name] = (b"[BRJND2024]\nVersion=0.1.1\nModDrv=zText\n"
                           b"Versification=Luther\n")
        else:
            parts[name] = ("synthetic:" + name).encode()
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        for name in sorted(parts):
            archive.writestr(name, parts[name])
    metadata = {
        "status": "reproducible_private_final_module_id_0_1_1_preflight_verified",
        "private_final_candidate_sword_zip_sha256": sha256(path.read_bytes()).hexdigest(),
        "independently_inspected_final_module_id": "BRJND2024",
        "final_conf_version": "0.1.1",
        "native_verse_index_verified": True,
        "source_verse_keys": 31166,
        "source_note_count": 6340,
        "all_521_division_metadata_source_native_pairs_verified": True,
        "binary_data_unchanged_during_identity_promotion": True,
        "six_ztext_member_hashes": {
            n: sha256(parts[n]).hexdigest()
            for n in parts if n.startswith("modules/")
        },
        "owner_release_approval": False,
        "published": False,
    }
    return path, metadata


class TestDarby011FinalAndroidIdentity(TestCase):
    def test_accepted_exact_final_id_and_module_bytes(self):
        with TemporaryDirectory() as d:
            path, meta = fixture(Path(d))
            result = verify_final_candidate(path, meta)
            self.assertEqual(result["module_id"], "BRJND2024")
            self.assertEqual(result["checked_sword_member_hashes"], 6)
            self.assertTrue(result["not_published"])

    def test_reject_changed_zip_digest(self):
        with TemporaryDirectory() as d:
            path, meta = fixture(Path(d))
            meta["private_final_candidate_sword_zip_sha256"] = "0" * 64
            with self.assertRaises(FinalDarbyAndroidError):
                verify_final_candidate(path, meta)

    def test_reject_false_editorial_or_native_proof(self):
        with TemporaryDirectory() as d:
            path, meta = fixture(Path(d))
            meta["all_521_division_metadata_source_native_pairs_verified"] = False
            with self.assertRaises(FinalDarbyAndroidError):
                verify_final_candidate(path, meta)

    def test_reject_published_or_authorized_candidate(self):
        with TemporaryDirectory() as d:
            path, meta = fixture(Path(d))
            meta["published"] = True
            with self.assertRaises(FinalDarbyAndroidError):
                verify_final_candidate(path, meta)

    def test_reject_changed_member_hash_even_if_zip_rehashed(self):
        with TemporaryDirectory() as d:
            path, meta = fixture(Path(d))
            key = next(iter(meta["six_ztext_member_hashes"]))
            meta["six_ztext_member_hashes"][key] = "0" * 64
            with self.assertRaises(FinalDarbyAndroidError):
                verify_final_candidate(path, meta)

    def test_reject_research_id_fraud(self):
        with TemporaryDirectory() as d:
            path, meta = fixture(Path(d))
            meta["independently_inspected_final_module_id"] = "JND2024RepairResearch"
            with self.assertRaises(FinalDarbyAndroidError):
                verify_final_candidate(path, meta)
