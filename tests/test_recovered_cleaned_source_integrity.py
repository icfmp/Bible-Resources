"""Prevent re-loss or silent replacement of recovered, source-attested OSIS editions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
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
