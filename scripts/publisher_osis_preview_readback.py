#!/usr/bin/env python3
"""Independently reinstall a tested zText ZIP and read it through stock SWORD.

No reader output, verse text or note content is logged, stored or uploaded.
A successful preview is NOT independent GUI, note-click or visual approval.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile
from zipfile import ZipFile

from publisher_osis_preview_package import COMPRESSED_FILES
from sword_native_inventory import collect_native_inventory

TEST_PASSAGES=(
    "Genesis 1:1", "Psalms 23:1", "Matthew 1:1",
    "John 3:16", "Revelation 22:21",
)


class PreviewReaderError(ValueError):
    """Installed preview cannot be independently verified."""


def test_preview(zip_path:Path, report_path:Path, native_index:Path,diatheke:Path):
    source=json.loads(report_path.read_text(encoding="utf-8"))
    candidates=source.get("candidate_research_results",[])
    if len(candidates)!=1:
        raise PreviewReaderError("Exactly one pinned candidate is required")
    candidate=candidates[0]
    preview=candidate.get("test_only_preview_archive")
    if (not isinstance(preview,dict)
            or preview.get("preview_only") is not True
            or preview.get("release_approved") is not False
            or preview.get("status") !=
               "exact_audited_source_bytes_packaged_for_reader_testing_only"
            or candidate.get("candidate_status")!=
               "full_numbered_text_and_note_preflight_equal_not_approved"
            or candidate.get("candidate_versification")!="Luther"
            or candidate.get("compiled_native_milestone_closure_metadata_only",{}).get(
                "status")!="compiled_milestone_pairs_verified_only"
            or not candidate.get("source_native_body_boundary_positions",{}).get(
                "all_title_text_and_nonspace_placement_equal")):
        raise PreviewReaderError("Original publisher parity gate has not passed")
    module=preview["module_id"]
    if module!="JND2024Research" or not zip_path.is_file() or zip_path.is_symlink():
        raise PreviewReaderError("Unreviewed preview module")
    data=zip_path.read_bytes()
    digest=sha256(data).hexdigest()
    if digest!=preview.get("zip_sha256") or len(data)!=preview.get("zip_bytes"):
        raise PreviewReaderError("Preview ZIP changed after verified compilation")
    conf=f"mods.d/{module.lower()}.conf"
    prefix=f"modules/texts/ztext/{module.lower()}/"
    expected={conf}|{prefix+k for k in COMPRESSED_FILES}
    with tempfile.TemporaryDirectory(prefix="publisher-private-reader-preview-") as folder:
        root=Path(folder)
        payload=root/"payload"
        with ZipFile(zip_path) as source_zip:
            members=source_zip.infolist()
            if (len(members)!=len(expected)
                    or set(x.filename for x in members)!=expected
                    or source_zip.testzip() is not None
                    or any(x.is_dir() or (x.external_attr >> 16)&0o170000
                           not in {0,0o100000} for x in members)):
                raise PreviewReaderError("Unexpected or malformed preview archive")
            for item in members:
                blob=source_zip.read(item)
                if sha256(blob).hexdigest()!=preview["member_sha256"].get(item.filename):
                    raise PreviewReaderError("Audited SWORD payload byte identity lost")
                path=payload/item.filename
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(blob)
        native_keys,_native_report,inventory=collect_native_inventory(native_index,root,module)
        references=set(native_keys.splitlines())
        if (len(references)!=31166
                or inventory.get("module_driver")!="zText"):
            raise PreviewReaderError("Isolated SWORD engine cannot read verified index")
        env=dict(os.environ,SWORD_PATH=str(payload))
        for passage in TEST_PASSAGES:
            try:
                cmd=[str(diatheke.resolve(strict=True)),"-b",module,
                     "-k",passage,"-f","plain"]
                process=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,
                                       stderr=subprocess.DEVNULL,timeout=40,
                                       check=False)
            except (OSError,subprocess.TimeoutExpired) as exc:
                raise PreviewReaderError("Stock diatheke preview invocation failed") from exc
            # A synthetic empty/error page is not successful reader coverage.
            rendered=process.stdout.decode("utf-8",errors="replace")
            if (process.returncode!=0 or len(rendered.strip())<30
                    or len(rendered)>1_000_000
                    or "module not found" in rendered.casefold()
                    or "not installed" in rendered.casefold()):
                raise PreviewReaderError("Stock diatheke did not render a representative passage")
        return {
            "status":"test_zip_reinstalled_and_stock_sword_diatheke_readback_verified",
            "candidate_preview_sha256":digest,
            "source_to_archive_module_bytes_verified":True,
            "stock_native_sword_numbered_reference_keys":len(references),
            "stock_diatheke_passage_ids_read":list(TEST_PASSAGES),
            "stock_diatheke_count":len(TEST_PASSAGES),
            "independent_visual_gui_xiphos_or_bible_tested":False,
            "notes_click_navigation_tested":False,
            "published":False,
            "private_text_or_note_contents_exposed":False,
        }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--zip",type=Path,required=True)
    p.add_argument("--source-report",type=Path,required=True)
    p.add_argument("--native-index",type=Path,required=True)
    p.add_argument("--diatheke",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink() or not a.output.parent.is_dir():
        p.error("Use a fresh metadata-only report path")
    result=test_preview(a.zip,a.source_report,a.native_index,a.diatheke)
    a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",
                        encoding="utf-8")
    print("Private SWORD preview verified by isolated stock native reader and diatheke")
    print("No Scripture, headings, note contents, or unapproved release uploaded")


if __name__=="__main__":
    main()
