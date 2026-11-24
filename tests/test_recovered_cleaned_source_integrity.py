"""Prevent re-loss or silent replacement of recovered, source-attested OSIS editions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    (
        "bibles/fr/lsg-1910/lsg-1910.osis.xml",
        "bibles/fr/lsg-1910/CLEANUP_MANIFEST.json",
        "modules/lsg-1910/SOURCE_VALIDATION.json",
        "source_sha256",
        "cleaned_osis_sha256",
    ),
    (
        "bibles/fr/darby-jnd-2024/bible_jnd_2_0.osis.xml",
        "bibles/fr/darby-jnd-2024/CLEANUP_MANIFEST.json",
        "modules/darby-jnd-2024/RELEASE_PROVENANCE.json",
        "corrected_candidate_osis_sha256",
        "cleaned_source_sha256",
    ),
    (
        "commentaries/en/mhc-crosswire/mhc.osis.xml",
        "commentaries/en/mhc-crosswire/CLEANUP_MANIFEST.json",
        None,
        None,
        "approved_cleaned_sha256",
    ),
    (
        "commentaries/en/hmcc-modern/hmcc-modern.osis.xml",
        "commentaries/en/hmcc-modern/CLEANUP_MANIFEST.json",
        "config/commentary-rebuilds/hmcc-modern.json",
        "source_approved_osis_sha256",
        "approved_source_sha256",
    ),
)
MHC_ACCEPTED_SHA = "c64891f4fb2c3bd3a7e5e6cca992d80675849e7b3615f80ee95121461ef385f4"


class RecoveredSourceIntegrity(unittest.TestCase):
    def test_exact_approved_sources_are_present_and_unchanged(self):
        for rel, manifest_rel, approval_path, approval_key, manifest_key in SOURCES:
            with self.subTest(source=rel):
                path = ROOT / "sources/cleaned" / rel
                self.assertTrue(path.is_file(), f"Missing curated source: {rel}")
                self.assertFalse(path.is_symlink())
                report = json.loads((ROOT / "sources/cleaned" / manifest_rel).read_text())
                approved = (
                    json.loads((ROOT / approval_path).read_text())[approval_key]
                    if approval_path is not None else MHC_ACCEPTED_SHA
                )
                self.assertEqual(report[manifest_key], approved)
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                self.assertEqual(digest.hexdigest(), approved,
                                 f"Previously approved editable OSIS was altered: {rel}")

    def test_classic_mhcc_source_reconstruction_is_real_and_source_attested(self):
        """The classic MHCC OSIS is a NEW verified derivative, not a rescued original."""
        path = ROOT / "sources/cleaned/commentaries/en/mhcc-crosswire/mhcc.osis.xml"
        manifest_path = path.with_name("CLEANUP_MANIFEST.json")
        self.assertTrue(path.is_file())
        self.assertFalse(path.is_symlink())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024*1024), b""):
                digest.update(chunk)
        self.assertEqual(digest.hexdigest(), "6e692fe887b0952bda540599b99c2c39d4b71a9f3d8e32a443db405bf53da52e")
        previous = json.loads((path.parent / "editorial/evidence/release-0.1.1/CLEANUP_MANIFEST.json").read_text())
        self.assertEqual(previous["reconstructed_source_sha256"], "6aca55c36789f6f7d081b7cba2a167a8006cad9447ae8b50d619ad0de32dfb39")
        self.assertEqual(manifest["previous_reconstructed_source_sha256"], previous["reconstructed_source_sha256"])
        self.assertEqual(manifest["reconstructed_source_sha256"], digest.hexdigest())
        self.assertEqual(manifest["reconstructed_source_size"], path.stat().st_size)
        self.assertEqual(manifest["source_kind"], "native_source_attested_reconstructed_osis_not_original_authoring_osis")
        self.assertIs(manifest["original_crosswire_authoring_osis_recovered"], False)
        self.assertIs(manifest["canonical_source_full_native_recompile_semantic_parity"], True)
        self.assertEqual(manifest["source_header_work_id"], "MHCC")
        native = json.loads((ROOT/"modules/mhcc-crosswire/SOURCE_VALIDATION.json").read_text())
        self.assertEqual(native["candidate_native_corpus_sha256"], manifest["source_native_corpus_sha256"])
        self.assertEqual(manifest["source_native_key_counts"], {"K":28742,"I":1255,"TOP":2})
