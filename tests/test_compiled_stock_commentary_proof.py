"""Offline regression tests for generic byte-attested compiled commentary releases."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from compiled_stock_commentary_proof import (
    compiled_stock_commentary_errors, SUFFIXES
)
from stage_verified_stock_commentary import reviewed_curated_version
from pilot_preflight import PilotError

DIGEST_A = "a"*64
DIGEST_B = "b"*64
DIGEST_C = "c"*64


class StockCommentaryReleaseTests(unittest.TestCase):
    def test_curated_conf_allows_only_one_version_line(self):
        original=(b"[Curated]\nDataPath=./modules/comments/zcom/curated/\n"
                  b"Version=2.0\r\nDistributionLicense=Public Domain\n"
                  b"TextSource=https://example.org/upstream\n")
        result=reviewed_curated_version(original,source_version="2.0",
                                        curated_version="0.1.0")
        self.assertEqual(result,original.replace(b"Version=2.0\r\n",
                                                 b"Version=0.1.0\r\n"))
        self.assertIn(b"DistributionLicense=Public Domain",result)
        for broken in (original.replace(b"Version=2.0",b"Version=1.9"),
                       original+b"Version=2.0\n",
                       original.replace(b"Version=2.0",b"Version=2.0\nVersion=2.0")):
            with self.assertRaises(PilotError):
                reviewed_curated_version(broken,source_version="2.0",
                                        curated_version="0.1.0")
        with self.assertRaises(PilotError):
            reviewed_curated_version(original,source_version="2.0",
                                    curated_version="unreviewed")

    def fixture(self, root):
        source=root/"config/commentary-intake"
        source.mkdir(parents=True)
        original={
            "category":"commentary","provider":"crosswire",
            "module_id":"Upstream","version":"2.0",
            "archive_sha256":DIGEST_A,
            "stock_conf_sha256":DIGEST_B,
            "native_raw_corpus_sha256":DIGEST_C,
            "source_page_url":"https://example.org/source",
            "rights":{"upstream_license_claim":"Public Domain--Copy Freely"},
        }
        (source/"test-stock.json").write_text(json.dumps(original))
        directory=root/"modules/curated"
        data=directory/"payload/modules/comments/zcom/curated"
        data.mkdir(parents=True)
        files={suffix:sha256((b"Original payload "+suffix.encode())).hexdigest()
               for suffix in SUFFIXES}
        for suffix in SUFFIXES:
            (data/suffix).write_bytes(b"Original payload "+suffix.encode())
        conf=(directory/"payload/mods.d/curated.conf")
        conf.parent.mkdir(parents=True)
        conf.write_text("[Curated]\nVersion=0.1.0\nDistributionLicense=Public Domain\n")
        m={
            "sword_id":"Curated","version":"0.1.0",
            "origin":{"url":"https://example.org/source"},
            "rights":{"license":"Public Domain"},
            "upstreams":[{
                "module_id":"Upstream","provider":"crosswire",
                "last_integrated_version":"2.0",
                "last_integrated_conf_sha256":DIGEST_B,
            }],
        }
        proof={
            "schema_version":1,"status":"validated",
            "source_kind":"compiled_sword_stock",
            "source_intake_manifest":"config/commentary-intake/test-stock.json",
            "upstream_module_id":"Upstream","curated_module_id":"Curated",
            "upstream_version":"2.0","curated_version":"0.1.0",
            "upstream_archive_sha256":DIGEST_A,
            "upstream_conf_sha256":DIGEST_B,
            "native_raw_corpus_sha256":DIGEST_C,
            "native_key_count":50,
            "compressed_members_sha256_by_filename":files,
            "curated_conf_sha256":sha256(conf.read_bytes()).hexdigest(),
            "all_original_compressed_files_byte_identical":True,
            "all_native_original_keys_byte_identical":True,
            "only_source_metadata_relabelled":["section_id","DataPath","Version"],
            "no_original_source_text_edited":True,
            "historical_print_or_ccel_parity_claimed":False,
            "gui_other_reader_compatibility_claimed":False,
        }
        (directory/"SOURCE_VALIDATION.json").write_text(json.dumps(proof))
        conf_options={"DistributionLicense":"Public Domain","ModDrv":"zCom",
                      "Versification":"KJV","SourceType":"OSIS"}
        return directory, m, conf_options, proof, original, data, conf

    def test_compiled_original_acceptance_checks_every_byte(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            directory,m,conf,proof,orig,data,confpath=self.fixture(root)
            self.assertEqual(compiled_stock_commentary_errors(directory,root,m,conf),[])
            (data/"nt.bzs").write_bytes(b"Changed source text")
            errors=compiled_stock_commentary_errors(directory,root,m,conf)
            self.assertTrue(any("STOCK_CONTENT_CHANGED" in v for v in errors))
            self.assertNotIn("Changed source text",str(errors))

    def test_fake_upstream_original_and_licence_are_not_accepted(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            directory,m,conf,proof,orig,data,confpath=self.fixture(root)
            conf["DistributionLicense"]="CC0" # no right to relicense source
            self.assertTrue(compiled_stock_commentary_errors(directory,root,m,conf))
            conf["DistributionLicense"]="Public Domain"
            orig["archive_sha256"]=DIGEST_C
            (root/"config/commentary-intake/test-stock.json").write_text(json.dumps(orig))
            self.assertTrue(compiled_stock_commentary_errors(directory,root,m,conf))
            orig["archive_sha256"]=DIGEST_A
            (root/"config/commentary-intake/test-stock.json").write_text(json.dumps(orig))
            proof["all_native_original_keys_byte_identical"]=False
            (directory/"SOURCE_VALIDATION.json").write_text(json.dumps(proof))
            self.assertTrue(compiled_stock_commentary_errors(directory,root,m,conf))

    def test_refuse_unattested_osis_source_or_missing_original_binary(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            directory,m,conf,proof,orig,data,confpath=self.fixture(root)
            proof["source_kind"]="synthetic_fake_osis"
            (directory/"SOURCE_VALIDATION.json").write_text(json.dumps(proof))
            self.assertTrue(compiled_stock_commentary_errors(directory,root,m,conf))
            (directory/"SOURCE_VALIDATION.json").unlink()
            self.assertTrue(compiled_stock_commentary_errors(directory,root,m,conf))
            self.assertNotIn("Original payload",str(compiled_stock_commentary_errors(
                directory,root,m,conf)))
