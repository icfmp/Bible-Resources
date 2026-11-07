#!/usr/bin/env python3
"""Disposable real eBible OSIS -> SWORD candidate compiler (no publication).

Input is already independently XSD/structure-validated by the caller.
Never writes to the user's installed SWORD modules, public repositories,
or releases. Returns only text-free metadata; original OSIS remains unchanged.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile

from pilot_preflight import PilotError
from pilot_subprocess import query,present_key

MAX_COMPILER_LOG=6*1024*1024
MAX_COMPILE_SECONDS=180
SAMPLES=[
    ("Genesis 1:1","Genesis 1:1:"),
    ("Exodus 7:26","Exodus 7:26:"),
    ("Exodus 7:29","Exodus 7:29:"),
    ("Psalms 3:9","Psalms 3:9:"),
    ("Psalms 23:1","Psalms 23:1:"),
    ("John 3:16","John 3:16:"),
]


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def compile_candidate(osis: Path, *, compiler="osis2mod", reader="diatheke") -> dict:
    before=osis.read_bytes()
    report={
        "status":"rebuild_probe_not_approved",
        "original_osis_sha256":_sha(before),
        "source_file_unchanged":True,
        "published":False,
        "approved_for_publication":False,
        "versification":"Segond",
        "module_id":"fraLSG1910eb",
        "real_module_rebuilt_in_temporary_directory":False,
        "all_source_verses_and_annotations_checked":False,
    }
    with tempfile.TemporaryDirectory(prefix="bible-lsg-segond-real-") as home:
        root=Path(home)
        data=root/"modules/texts/rawtext/fralsg1910eb"
        data.mkdir(parents=True)
        result=subprocess.run(
            [compiler,str(data),str(osis),"-v","Segond"],
            capture_output=True,check=False,timeout=MAX_COMPILE_SECONDS,
        )
        logs=result.stdout+result.stderr
        report["compiler_exit_code"]=result.returncode
        report["compiler_output_sha256"]=_sha(logs)
        report["compiler_output_bytes"]=len(logs)
        # Record only canonical source references in compiler messages;
        # never upload raw compiler logs that may contain Bible text.
        known_refs=sorted(set(m.decode("ascii") for m in re.findall(
            rb"\b(?:Gen|Exod|Lev|Num|Deut|Josh|Judg|Ruth|1Sam|2Sam|"
            rb"1Kgs|2Kgs|1Chr|2Chr|Ezra|Neh|Esth|Job|Ps|Prov|Eccl|Song|"
            rb"Isa|Jer|Lam|Ezek|Dan|Hos|Joel|Amos|Obad|Jonah|Mic|"
            rb"Nah|Hab|Zeph|Hag|Zech|Mal|Matt|Mark|Luke|John|Acts|"
            rb"Rom|1Cor|2Cor|Gal|Eph|Phil|Col|1Thess|2Thess|"
            rb"1Tim|2Tim|Titus|Phlm|Heb|Jas|1Pet|2Pet|1John|"
            rb"2John|3John|Jude|Rev)\.\d+\.\d+\b",
            logs,
        )))
        report["compiler_source_ref_mentions"]=known_refs[:70]
        report["compiler_diagnostics_count"]={
            "fatal":len(re.findall(rb"(?m)(?:^|\n)FATAL\(",logs)),
            "error":len(re.findall(rb"(?m)(?:^|\n)ERROR\(",logs)),
            "warning":len(re.findall(rb"(?m)(?:^|\n)WARNING\(",logs)),
            "v11n_outside":len(re.findall(rb"not in the Segond versification",logs)),
        }
        files=[p for p in data.rglob("*") if p.is_file()]
        report["module_file_count"]=len(files)
        report["module_total_bytes"]=sum(p.stat().st_size for p in files)
        report["real_module_rebuilt_in_temporary_directory"]=(
            result.returncode==0 and bool(files)
        )
        if len(logs)>MAX_COMPILER_LOG or result.returncode or not files:
            report["status"]="blocked_compiler_or_unbounded_diagnostics"
            return report
        conf=root/"mods.d/fralsg1910eb.conf"
        conf.parent.mkdir(parents=True)
        conf.write_text(
            "[fraLSG1910eb]\n"
            "Description=Nonpublished eBible Louis Segond conversion trial\n"
            "Version=0.0\n"
            "DataPath=./modules/texts/rawtext/fralsg1910eb/\n"
            "ModDrv=RawText\n"
            "Encoding=UTF-8\n"
            "Lang=fr\n"
            "SourceType=OSIS\n"
            "Versification=Segond\n"
            "DistributionLicense=Public Domain\n",
            encoding="utf-8",
        )
        probes=[]
        for key,header in SAMPLES:
            code,body=query("fraLSG1910eb",key,fmt="plain",root=root,exe=reader,
                            limit=256*1024,timeout=30)
            decoded=body.decode("utf-8",errors="replace")
            heading=decoded.splitlines()[0] if decoded.splitlines() else ""
            matched=heading.startswith(header)
            # A nonempty chapter/verse heading with zero actual content must
            # NEVER be taken as a successful reader round trip.
            content=decoded[len(heading):] if matched else decoded
            has_text=bool(content.strip()) or bool(heading[len(header):].strip())
            probes.append({
                "requested":key,
                "reader_return_code":code,
                "reference_header_preserved":matched,
                "has_nonempty_verse_body":has_text and present_key(key,body,code),
                "output_sha256":_sha(body),
                "output_bytes":len(body),
            })
        report["reader_probes"]=probes
        report["all_sample_keys_have_text"]=all(
            q["reference_header_preserved"] and q["has_nonempty_verse_body"]
            for q in probes
        )
        report["status"]=(
            "actual_text_module_compiled_and_samples_read_not_approved"
            if report["all_sample_keys_have_text"] and not any(
               report["compiler_diagnostics_count"][x] for x in ("fatal","error","v11n_outside")
            )
            else "compiled_but_sample_or_v11n_errors_block"
        )
        report["source_file_unchanged"]=_sha(osis.read_bytes())==report["original_osis_sha256"]
        if not report["source_file_unchanged"]:
            raise PilotError("Original OSIS source modified during compiler trial")
    return report
