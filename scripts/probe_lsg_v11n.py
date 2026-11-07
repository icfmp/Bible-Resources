#!/usr/bin/env python3
"""Read-only comparison of source verse keys against official SWORD versifications.

Uses generated NON-BIBLICAL placeholder text, never modifies the actual
Bible or its compiled module. This is a compatibility probe, not a converter.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from xml.etree import ElementTree as ET

from lsg_source_compare import read_source_xml, scan_usfx
from pilot_preflight import PilotError, ROOT
from pilot_subprocess import query, present_key

NS="http://www.bibletechnologies.net/2003/OSIS/namespace"
BOOK=re.compile(r"^[1-4]?[A-Za-z][A-Za-z0-9]*$")
MAX_SUBPROCESS_OUTPUT=2*1024*1024
MAX_CASES=30
MAX_KEYS=1000


def make_fixture(spec:dict, actual_keys:list[tuple[str,int,int]]) -> tuple[bytes,list[str]]:
    if spec.get("schema_version")!=1 or spec.get("schemes")!=["NRSV","Segond"]:
        raise PilotError("Unreviewed official SWORD-versification probe configuration")
    cases=spec.get("cases")
    if not isinstance(cases,list) or not 1<=len(cases)<=MAX_CASES:
        raise PilotError("Invalid v11n probe case list")
    existing=set(actual_keys)
    seen=set()
    osis=ET.Element(f"{{{NS}}}osis")
    text=ET.SubElement(osis,f"{{{NS}}}osisText",{
        "osisIDWork":"SyntheticV11nProbe",
        "osisRefWork":"Bible",
        "{http://www.w3.org/XML/1998/namespace}lang":"en",
    })
    count=0
    references=[]
    for entry in cases:
        book=entry.get("source_usfx_book")
        osis_id=entry.get("osis_book")
        sword_name=entry.get("sword_book")
        chapter=entry.get("chapter")
        verses=entry.get("verses")
        if (not isinstance(book,str) or not isinstance(osis_id,str)
                or not BOOK.fullmatch(osis_id)
                or not isinstance(sword_name,str) or not sword_name.strip()
                or type(chapter) is not int or chapter<1
                or not isinstance(verses,list) or not verses):
            raise PilotError("Invalid or ambiguous SWORD source key probe")
        if (any(type(v) is not int or v<1 for v in verses)
                or verses!=sorted(set(verses))):
            raise PilotError("Unreviewed/repeated probe verses")
        div=ET.SubElement(text,f"{{{NS}}}div",{"type":"book","osisID":osis_id})
        chap=ET.SubElement(div,f"{{{NS}}}chapter",{"osisID":f"{osis_id}.{chapter}"})
        for verse in verses:
            if (book,chapter,verse) not in existing:
                raise PilotError(f"Probe key not present in publisher USFX: {book}.{chapter}.{verse}")
            key=f"{osis_id}.{chapter}.{verse}"
            if key in seen:
                raise PilotError("Duplicated source reference in probe")
            seen.add(key)
            # Explicitly synthetic marker, NOT copied Scripture.
            ET.SubElement(chap,f"{{{NS}}}verse",{"osisID":key}).text="SYNTHETIC_"+osis_id+"_"+str(chapter)+"_"+str(verse)
            references.append(key)
            count+=1
            if count>MAX_KEYS:
                raise PilotError("Probe exceeds reviewed key limit")
    result=ET.tostring(osis,encoding="utf-8",xml_declaration=True)
    return result,references


def compile_probe(fixture:bytes, scheme:str, *, exe:str="osis2mod",
                  reader:str="diatheke", checks:list[dict] | None=None) -> dict:
    if scheme not in ("NRSV","Segond"):
        raise PilotError("Unsupported experimental versification")
    with tempfile.TemporaryDirectory(prefix="bible-v11n-fixture-") as workspace:
        root=Path(workspace)
        source=root/"synthetic.osis.xml"
        target=root/"modules/texts/rawtext/v11nprobe"
        target.mkdir(parents=True)
        source.write_bytes(fixture)
        proc=subprocess.run(
            [exe,str(target),str(source),"-v",scheme],
            capture_output=True,timeout=45,check=False,
        )
        if len(proc.stdout)+len(proc.stderr)>MAX_SUBPROCESS_OUTPUT:
            raise PilotError("Unexpectedly large SWORD tool output")
        diagnostics=(proc.stdout+proc.stderr).decode("utf-8",errors="replace").splitlines()
        counts=Counter()
        outside=[]
        invalid=[]
        for line in diagnostics:
            if re.search(r"(?:INFO|WARNING|ERROR|FATAL)\(V11N\)",line):
                counts["v11n_diagnostic_lines"]+=1
                if "not in" in line.lower() or "appending content" in line.lower():
                    counts["outside_versification_diagnostics"]+=1
                    # Only report source reference IDs, no output text.
                    found=re.search(r"\b(?:Exod|Ps)\.\d+\.\d+\b",line)
                    if found and len(outside)<30:
                        outside.append(found.group(0))
            if re.search(r"(?<!\w)(ERROR|FATAL)\(",line):
                counts["tool_error_lines"]+=1
                if len(invalid)<5:
                    invalid.append(line.split(":",1)[0][:120])
        files=[p for p in target.rglob("*") if p.is_file()]
        evidence=[]
        if checks is not None and proc.returncode==0 and files:
            conf=root/"mods.d/v11nprobe.conf"
            conf.parent.mkdir(parents=True,exist_ok=True)
            conf.write_text(
                "[V11NPROBE]\n"
                "Description=Synthetic SWORD verse reference probe\n"
                "Version=1.0\n"
                "ModDrv=RawText\n"
                "DataPath=./modules/texts/rawtext/v11nprobe/\n"
                "Encoding=UTF-8\n"
                "SourceType=OSIS\n"
                "Lang=en\n"
                f"Versification={scheme}\n",
                encoding="utf-8",
            )
            marker_pattern=re.compile(r"SYNTHETIC_[A-Za-z0-9]+_\d+_\d+")
            for item in checks:
                return_code,content=query("V11NPROBE",item["request"],
                    fmt="plain",root=root,exe=reader,limit=4096,timeout=12)
                markers=sorted(set(marker_pattern.findall(content.decode("utf-8",errors="replace"))))
                evidence.append({
                    "source_reference":item["source_key"],
                    "sword_query":item["request"],
                    "reader_return_code":return_code,
                    "key_found_in_output":present_key(item["request"],content,return_code),
                    "marker_for_original_key_present":item["marker"] in markers,
                    "synthetic_markers_in_returned_entry":markers,
                })
        return {
            "scheme":scheme,
            "tool_return_code":proc.returncode,
            "module_created":bool(files),
            "generated_file_count":len(files),
            "generated_bytes":sum(p.stat().st_size for p in files),
            "v11n_diagnostics":dict(counts),
            "sample_out_of_range_source_keys":outside,
            "tool_error_prefixes":invalid,
            "reader_key_evidence":evidence,
            "reader_was_checked":checks is not None,
            "complete_source_text_checked":False,
            "candidate_text_approval":False,
        }


def run(archive:Path,config:dict,*,compiler="osis2mod",reader="diatheke") -> dict:
    raw, source=read_source_xml(archive,source_format="usfx")
    structure,actual_keys=scan_usfx(raw)
    fixture,refs=make_fixture(config,actual_keys)
    checks=[
        {"source_key":f'{entry["osis_book"]}.{entry["chapter"]}.{v}',
         "request":f'{entry["sword_book"]} {entry["chapter"]}:{v}',
         "marker":f'SYNTHETIC_{entry["osis_book"]}_{entry["chapter"]}_{v}'}
        for entry in config["cases"] for v in entry["verses"]
    ]
    evaluations=[compile_probe(fixture,scheme,exe=compiler,
                               reader=reader,checks=checks)
                 for scheme in config["schemes"]]
    return {
        "schema_version":1,
        "status":"reference_probe_only",
        "source_usfx_sha256":source["sha256"],
        "source_verse_keys":len(actual_keys),
        "synthetic_fixture_sha256":hashlib.sha256(fixture).hexdigest(),
        "synthetic_keys":refs,
        "schemes":evaluations,
        "preferred_scheme_not_approved":True,
        "source_text_modified":False,
        "real_module_recompiled":False,
        "note":"Official SWORD importer's behavior on synthetic reference keys only. This does not prove a corrected LSG module, verse mapping, notes or GTK rendering.",
    }


def main(argv=None)->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--usfx-zip",type=Path,required=True)
    ap.add_argument("--config",type=Path,default=ROOT/"config/lsg-v11n-probes.json")
    ap.add_argument("--report",type=Path,required=True)
    args=ap.parse_args(argv)
    try:
        config=json.loads(args.config.read_text(encoding="utf-8"))
        result=run(args.usfx_zip,config)
        code=0 if all(x["tool_return_code"]==0 and x["module_created"] and
                      x["reader_was_checked"] and any(z["marker_for_original_key_present"]
                                                     for z in x["reader_key_evidence"])
                      for x in result["schemes"]) else 1
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:
        result={"status":"blocked","error":str(exc),"source_text_modified":False}
        code=1
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(f"Segond reference probe: {result['status']} — {args.report}")
    return code


if __name__=="__main__":
    sys.exit(main())
