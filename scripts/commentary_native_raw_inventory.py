#!/usr/bin/env python3
"""Read every exact unfiltered occupied stock SWORD commentary entry privately.

Generic RawCom/zCom companion to the Bible native raw-corpus guard.  Never
rebuilds or rewrites the module, normalizes text, or publishes a commentary.
A full corpus SHA/occupancy audit is NOT a source-to-compiled fidelity proof.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
import zipfile

from commentary_intake import load_manifest
from commentary_native_inventory import parse_index
from pilot_fetch import fetch
from pilot_preflight import PilotError, inspect_archive
from sword_native_raw_corpus_inventory import RawCorpusError, parse_native_raw_corpus

MAX_KEY_REPORT = 20
MAX_TOTAL_SECONDS = 360


def _safe_stock_install(zip_path: Path, records: list[dict], root: Path) -> None:
    """Install the independently preflighted original in disposable storage."""
    root.mkdir()
    with zipfile.ZipFile(zip_path) as archive:
        for member in records:
            name = member["name"]
            target = root / PurePosixPath(name)
            if not target.resolve().is_relative_to(root.resolve()):
                raise PilotError("Untrusted original SWORD archive member path")
            target.parent.mkdir(parents=True, exist_ok=True)
            if not name.endswith("/"):
                with archive.open(name) as src, target.open("xb") as dst:
                    shutil.copyfileobj(src, dst, length=256 * 1024)


def private_crosscheck(index: bytes, module_id: str, content_rows: list[tuple[str,str]],
                       raw_stats: dict) -> dict:
    """A second native tool must independently agree on every occupied slot."""
    index_report = parse_index(index, module_id)
    try:
        rows = [tuple(line.split("\t")) for line in index.decode("ascii").splitlines()[1:-1]]
    except UnicodeError:
        raise PilotError("Native occupied keys are not verified ASCII") from None
    if any(len(row)!=2 for row in rows) or rows!=content_rows:
        raise PilotError("Full raw-entry stream diverged from independently enumerated stock SWORD keys")
    if (raw_stats["actual_occupied_numbered_entry_count"] != index_report["occupied_numbered_slots"]
        or raw_stats["actual_occupied_intro_entry_count"] != index_report["occupied_intro_slots"]
        or raw_stats["actual_occupied_anonymous_top_entry_count"] != index_report["occupied_anonymous_top_slots"]):
        raise PilotError("Native raw content stream counts disagree with complete independent index")
    return {
        "native_key_order_sha256": index_report["ordered_occupied_key_sha256"],
        "native_engine_version": index_report["libsword_version"],
        "native_versification": index_report["native_versification"],
        "native_driver": index_report["driver"],
        "exact_all_occupied_stock_keys_read_and_crosschecked": True,
        "all_stock_occupied_keys_count": len(rows),
    }


def inspect_raw_content(resource_id: str, *, index_binary: Path, raw_binary: Path,
                        directory: Path | None = None) -> dict:
    manifest = load_manifest(resource_id, directory)
    expected_sha = manifest.get("archive_sha256")
    if not expected_sha:
        raise PilotError("Official SWORD original must be SHA-pinned")
    if any(not path.is_file() or path.is_symlink() for path in (index_binary, raw_binary)):
        raise PilotError("Trusted native index and raw-frame binaries required")
    with tempfile.TemporaryDirectory(prefix="commentary-stock-full-raw-") as temp:
        root = Path(temp)
        original = root/"stock.zip"
        download = fetch(manifest["sword_zip_url"], original, manifest["provider"])
        if download["sha256"]!=expected_sha:
            raise PilotError("Upstream stock SWORD commentary archive changed; abort")
        archive=inspect_archive(original,source_kind="sword",
                                expected_module_id=manifest["module_id"],
                                expected_category="commentary")
        conf=archive["sword_conf"]
        if conf["version"]!=manifest["version"] or conf["language"]!=manifest["language"]:
            raise PilotError("Stock module identity changed")
        installed=root/"installed"
        _safe_stock_install(original,archive["members"],installed)
        env=dict(os.environ,SWORD_PATH=str(installed))
        try:
            key_probe=subprocess.run([str(index_binary),manifest["module_id"]],
                                    capture_output=True,timeout=60,env=env,check=False)
        except subprocess.TimeoutExpired:
            raise PilotError("Independent commentary index timed out") from None
        if key_probe.returncode or len(key_probe.stdout)>12*1024*1024:
            raise PilotError("Independent commentary index failed or exceeded output bounds")
        # The original source text leaves the subprocess ONLY via this private
        # pipe, never through a shell step, job log or public artifact.
        command=["timeout",f"{MAX_TOTAL_SECONDS}s",str(raw_binary),manifest["module_id"]]
        process=None
        ordered_rows=[]
        raw_sha_count=Counter()
        zero_length_count=0
        whitespace_only_count=0
        per_book=defaultdict(lambda: {"entries":0,"raw_bytes":0,"nonempty_raw_entries":0})
        try:
            process=subprocess.Popen(command,stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL,env=env)
            if process.stdout is None:
                raise PilotError("Cannot privately receive SWORD raw-entry stream")
            def examine(kind: str, ref: str, content: bytes) -> None:
                nonlocal zero_length_count, whitespace_only_count
                ordered_rows.append((kind,ref))
                raw_sha_count[sha256(content).hexdigest()]+=1
                if not content:
                    zero_length_count+=1
                if not content.strip():
                    whitespace_only_count+=1
                name=ref.split(".",1)[0] if kind!="U" else "_OPAQUE_TOP"
                stats=per_book[name]
                stats["entries"]+=1
                stats["raw_bytes"]+=len(content)
                if content.strip():
                    stats["nonempty_raw_entries"]+=1
            raw, keys, intros, top=parse_native_raw_corpus(process.stdout,on_entry=examine)
            process.stdout.close()
            result_code=process.wait(timeout=15)
            if result_code!=0:
                raise PilotError("Native commentary raw reader stopped before complete corpus terminator")
        except BaseException:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
            raise
        proof=private_crosscheck(key_probe.stdout, manifest["module_id"],ordered_rows,raw)
        if proof["native_driver"]!=conf["driver"] or proof["native_versification"]!=(conf["versification"] or "KJV"):
            raise PilotError("Real SWORD driver or versification differs from pinned source metadata")
        duplicates=sum(count-1 for count in raw_sha_count.values() if count>1)
        return {
            "schema_version":1,
            "status":"all_stock_native_raw_commentary_entries_hashed_not_authorial_parity",
            "resource_id":resource_id,
            "stock_sword_original_sha256":download["sha256"],
            "stock_sword_conf_sha256":conf["conf_sha256"],
            "native_raw_corpus_ordered_sha256":raw["all_native_raw_entries_ordered_sha256"],
            "total_native_raw_entry_bytes":raw["actual_native_unfiltered_raw_bytes_total"],
            "raw_entry_count":raw["all_actual_raw_entries_scanned"],
            "raw_numbered_slots":raw["actual_occupied_numbered_entry_count"],
            "raw_introduction_slots":raw["actual_occupied_intro_entry_count"],
            "raw_opaque_top_slots":raw["actual_occupied_anonymous_top_entry_count"],
            "zero_length_native_raw_entries":zero_length_count,
            "raw_entries_with_only_whitespace":whitespace_only_count,
            "number_of_identical_raw_hash_extra_occurrences":duplicates,
            "by_book_or_special":{
                key:per_book[key] for key in sorted(per_book)
            },
            "native_correspondence":proof,
            "source_scripCom_references_compared":False,
            "source_text_punctuation_semantics_compared":False,
            "source_and_stock_paragraph_order_compared":False,
            "source_and_stock_note_bodies_compared":False,
            "edition_equivalence_approved":False,
            "rights_review_approved":False,
            "reader_GUI_testing_completed":False,
            "published":False,
            "original_text_disclosed":False,
            "original_bytes_changed":False,
        }


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-id",required=True)
    p.add_argument("--native-index-binary",required=True,type=Path)
    p.add_argument("--native-raw-binary",required=True,type=Path)
    p.add_argument("--report",required=True,type=Path)
    a=p.parse_args(argv)
    try:
        result=inspect_raw_content(a.resource_id,index_binary=a.native_index_binary,
                                    raw_binary=a.native_raw_binary)
        code=0
    except (ValueError,OSError,RuntimeError,zipfile.BadZipFile,RawCorpusError) as exc:
        result={"status":"blocked","resource_id":a.resource_id,"reason":str(exc),
                "published":False,"source_text_punctuation_semantics_compared":False}
        code=1
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("Read-only commentary stock raw corpus: "+result["status"]+" (text never logged)")
    return code


if __name__=="__main__":
    raise SystemExit(main())
