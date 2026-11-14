"""Regression tests for one fail-closed catalogue + GitHub Releases publication."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from subprocess import CompletedProcess

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from catalogue_release_coverage import coverage, ReleaseCoverageError
from publish_reviewed_release import verify_historical_release, ReleaseError

ROOT = Path(__file__).resolve().parents[1]
SHA = sha256(b"approved deterministic module ZIP").hexdigest()


class PublicationCoverageTests(unittest.TestCase):
    def fixture(self, root):
        mdir=root/"modules/sample"
        mdir.mkdir(parents=True)
        metadata={"id":"sample","sword_id":"BRSAMPLE","version":"0.1.0",
                  "quality":{"status":"approved"}}
        (mdir/"metadata.json").write_text(json.dumps(metadata),encoding="utf-8")
        cdir=root/"catalog/v1"
        cdir.mkdir(parents=True)
        catalogue={"schema_version":1,"modules":[{
            "id":"sample","sword_id":"BRSAMPLE","version":"0.1.0",
            "download":{"url":"https://icfmp.github.io/Bible-Resources/sword/packages/BRSAMPLE.zip",
                        "sha256":SHA,"size_bytes":len(b"approved deterministic module ZIP")}
        }]}
        (cdir/"catalog.json").write_text(json.dumps(catalogue),encoding="utf-8")
        plans=root/"config/release-plans"
        plans.mkdir(parents=True)
        plan={"schema_version":1,"module_id":"sample","sword_id":"BRSAMPLE",
              "tag":"sample-0.1.0","version":"0.1.0",
              "package_sha256":SHA,
              "package_size_bytes":len(b"approved deterministic module ZIP"),
              "authorization":{"reviewed_by":"Project owner"}}
        (plans/"sample-0.1.0.json").write_text(json.dumps(plan),encoding="utf-8")
        legacy=root/"config/release-legacy-bindings.json"
        legacy.write_text(json.dumps({
            "schema_version":1,"purpose":"Historical migration",
            "reviewed_by":"Project owner","entries":[]
        }),encoding="utf-8")
        return plan,catalogue,legacy

    def test_exact_reviewed_release_required_and_matches_catalogue(self):
        with TemporaryDirectory() as temporary:
            root=Path(temporary)
            plan,catalogue,_=self.fixture(root)
            result=coverage(root)
            self.assertEqual(result["module_count"],1)
            self.assertEqual(len(result["planned"]),1)
            self.assertEqual(result["legacy"],[])
            (root/"config/release-plans/sample-0.1.0.json").unlink()
            with self.assertRaisesRegex(ReleaseCoverageError,"missing="):
                coverage(root)

    def test_reject_mismatch_unapproved_or_orphaned_release_plan(self):
        with TemporaryDirectory() as temporary:
            root=Path(temporary)
            plan,catalogue,_=self.fixture(root)
            plan["package_sha256"]="0"*64
            (root/"config/release-plans/sample-0.1.0.json").write_text(json.dumps(plan))
            with self.assertRaisesRegex(ReleaseCoverageError,"planned GitHub Release"):
                coverage(root)
            plan["package_sha256"]=SHA
            (root/"config/release-plans/sample-0.1.0.json").write_text(json.dumps(plan))
            mpath=root/"modules/sample/metadata.json"
            data=json.loads(mpath.read_text())
            data["quality"]["status"]="draft"
            mpath.write_text(json.dumps(data))
            with self.assertRaisesRegex(ReleaseCoverageError,"Approved modules and catalogue"):
                coverage(root)

    def test_actual_package_must_match_both_byte_length_and_digest(self):
        with TemporaryDirectory() as temporary:
            root=Path(temporary)
            self.fixture(root)
            built=root/"dist/sword/packages"
            built.mkdir(parents=True)
            p=built/"BRSAMPLE.zip"
            p.write_bytes(b"approved deterministic module ZIP")
            self.assertEqual(coverage(root,built=root/"dist")["module_count"],1)
            p.write_bytes(b"approved deterministic module ziP")
            with self.assertRaisesRegex(ReleaseCoverageError,"actual generated package differs"):
                coverage(root,built=root/"dist")

    def test_historical_mismatch_must_be_declared_and_release_is_not_replaced(self):
        with TemporaryDirectory() as temporary:
            root=Path(temporary)
            plan,catalogue,legacy_file=self.fixture(root)
            (root/"config/release-plans/sample-0.1.0.json").unlink()
            record={
              "module_id":"sample","sword_id":"BRSAMPLE","version":"0.1.0",
              "tag":"sample-0.1.0","asset_name":"BRSAMPLE-0.1.0.zip",
              "release_sha256":"f"*64,"release_size_bytes":22,
              "catalogue_sha256":SHA,
              "catalogue_size_bytes":len(b"approved deterministic module ZIP"),
              "legacy_package_differs":True,
              "evidence_url":"https://github.com/icfmp/Bible-Resources/releases/tag/sample-0.1.0",
              "notes":"Historically different published module ZIP. Exact authorial equality not established."
            }
            doc=json.loads(legacy_file.read_text())
            doc["entries"]=[record]
            legacy_file.write_text(json.dumps(doc))
            result=coverage(root)
            self.assertEqual(len(result["legacy"]),1)
            doc["entries"][0]["legacy_package_differs"]=False
            legacy_file.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ReleaseCoverageError,"explicitly recorded"):
                coverage(root)

    def test_workflow_order_guards_against_catalogue_before_release(self):
        workflow=(ROOT/".github/workflows/pages.yml").read_text(encoding="utf-8")
        self.assertLess(workflow.index("scripts/catalogue_release_coverage.py"),
                        workflow.index("scripts/publish_reviewed_release.py"))
        self.assertLess(workflow.index("scripts/publish_reviewed_release.py"),
                        workflow.index("actions/deploy-pages@v4"))
        self.assertIn("contents: write",workflow)
        self.assertIn("github.ref == 'refs/heads/main'",workflow)
        self.assertFalse((ROOT/".github/workflows/publish-reviewed-sword-releases.yml").exists())
        self.assertTrue((ROOT/"config/release-legacy-bindings.json").is_file())

    def test_real_repository_release_coverage_has_no_unreviewed_module(self):
        result=coverage(ROOT)
        self.assertGreaterEqual(result["module_count"],3)
        self.assertEqual(len(result["planned"])+len(result["legacy"]),
                         result["module_count"])

    def test_real_historical_release_download_requires_byte_identity(self):
        data=b"original legacy archive"
        record={"tag":"old-0.1.0","asset_name":"TEST-0.1.0.zip",
                "release_sha256":sha256(data).hexdigest(),
                "release_size_bytes":len(data)}
        def pretend_gh(*args,**_):
            if args[0:2] == ("release","view"):
                return CompletedProcess(args,0,'{"isDraft":false,"assets":[{"name":"TEST-0.1.0.zip"}]}',"")
            if args[0:2] == ("release","download"):
                folder=Path(args[args.index("--dir")+1])
                (folder/record["asset_name"]).write_bytes(data)
                return CompletedProcess(args,0,"","")
            raise AssertionError(f"Unexpected GitHub operation: {args}")
        with patch("publish_reviewed_release.gh",side_effect=pretend_gh):
            verify_historical_release(record,repository="icfmp/Bible-Resources")
            record["release_sha256"]="1"*64
            with self.assertRaisesRegex(ReleaseError,"bytes differ"):
                verify_historical_release(record,repository="icfmp/Bible-Resources")


if __name__=="__main__":
    unittest.main()
