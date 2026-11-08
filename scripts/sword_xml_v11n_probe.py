#!/usr/bin/env python3
"""No-Bible-text compatibility proof: dynamic XML SWORD HEAD vs stock SWORD 1.9.

The proof compiles ONLY synthetic labels into a disposable SWORD module.
It demonstrates whether a module carrying XML-defined verse limits can
be read correctly by the installed stable library/Xiphos equivalent.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import os
import subprocess
import tempfile

from lsg_source_v11n_delta import build_v11n_delta
from pilot_preflight import PilotError


def checked_run(args, env=None, timeout=75):
    r=subprocess.run(args,env=env,stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,timeout=timeout,check=False)
    if len(r.stdout)+len(r.stderr)>2_000_000:
        raise PilotError("Unbounded synthetic SWORD output")
    return r


def synthetic_osis() -> bytes:
    root='http://www.bibletechnologies.net/2003/OSIS/namespace'
    return (f'<?xml version="1.0" encoding="utf-8"?>'
            f'<osis xmlns="{root}"><osisText osisIDWork="SyntheticV11n" osisRefWork="Bible">'
            '<header><work osisWork="SyntheticV11n">'
            '<title>Synthetic only</title><identifier type="OSIS">SyntheticV11n</identifier>'
            '<refSystem>Bible</refSystem></work></header>'
            '<div type="book" osisID="Job"><chapter osisID="Job.34">'
            '<verse osisID="Job.34.36">SYNTH_JOB36_END</verse>'
            '</chapter></div>'
            '<div type="book" osisID="Mark"><chapter osisID="Mark.10">'
            '<verse osisID="Mark.10.52">SYNTH_MARK52_END</verse>'
            '<verse osisID="Mark.10.53">SYNTH_MARK53_END</verse>'
            '</chapter></div></osisText></osis>').encode("utf-8")


def run(head_prefix: Path, stable_diatheke: str) -> dict:
    binary_dir=head_prefix/"bin"
    exe=binary_dir/"osis2mod"
    reader=binary_dir/"diatheke"
    if not (exe.is_file() and reader.is_file()):
        raise PilotError("Pinned SWORD HEAD compiler or reader not found")
    # This fixture deliberately uses the two *synthetic* chapter maxima
    # and no original Scripture, annotations or translation data.
    authored=[("JOB",34,v) for v in range(1,37)]+[
        ("MRK",10,v) for v in range(1,54)]
    xml,delta_audit=build_v11n_delta(
        authored,{"JOB":"Job","MRK":"Mark"},
        {("Job",34):37,("Mark",10):52},
        base_name="Segond",edition_id="BRV11nSynthetic",
        book_order=["JOB","MRK"],new_testament_first="Mark")
    report={
        "status":"not_run",
        "experimental_delta":delta_audit,
        "head_reads_verse_53_separately":False,
        "stock_reads_verse_53_separately":False,
        "stock_runtime_supports_module_exactly":False,
        "contains_real_bible_text":False,
        "published":False,
    }
    with tempfile.TemporaryDirectory(prefix="sword-dynamic-compat-") as temp:
        home=Path(temp)
        root=home/"modules-root"
        data=root/"modules/texts/rawtext/brv11nsynthetic"
        conf=root/"mods.d/brv11nsynthetic.conf"
        data.mkdir(parents=True)
        conf.parent.mkdir(parents=True)
        osis=home/"synthetic.osis.xml"
        xml_path=home/"synthetic-v11n.xml"
        osis.write_bytes(synthetic_osis())
        xml_path.write_bytes(xml)
        conf.write_text(
            "[BRV11nSynthetic]\n"
            "Description=Generated synthetic XML-v11n compatibility probe, never Scripture\n"
            "DataPath=./modules/texts/rawtext/brv11nsynthetic/\n"
            "ModDrv=RawText\n"
            "SourceType=OSIS\n"
            "Encoding=UTF-8\n"
            "Lang=en\n"
            "Versification=BRV11nSynthetic\n"
            "DistributionLicense=Public Domain\n",encoding="utf-8")
        environment=dict(os.environ)
        environment["LD_LIBRARY_PATH"]=str(head_prefix/"lib")+(
            ":"+environment["LD_LIBRARY_PATH"] if environment.get("LD_LIBRARY_PATH") else "")
        environment["SWORD_PATH"]=str(root)
        compiled=checked_run([str(exe),str(data),str(osis),"-v",str(xml_path)],env=environment)
        report["head_compiler_exit_code"]=compiled.returncode
        report["head_compiler_output_bytes"]=len(compiled.stdout)+len(compiled.stderr)
        report["synthetic_module_file_count"]=sum(p.is_file() for p in data.rglob("*"))
        if compiled.returncode or not any(p.is_file() for p in data.rglob("*")):
            report["status"]="head_compiler_rejected_synthetic_xml_v11n"
            return report
        (data/"v11n.xml").write_bytes(xml)
        checks=[("Mark 10:52","SYNTH_MARK52_END"),
                ("Mark 10:53","SYNTH_MARK53_END"),
                ("Job 34:36","SYNTH_JOB36_END")]
        for kind,cmd,env in [
            ("head",str(reader),environment),
            ("stable",stable_diatheke,dict(os.environ,SWORD_PATH=str(root)))
        ]:
            passing=[]
            for ref,secret in checks:
                run=checked_run([cmd,"-b","BRV11nSynthetic","-f","plain","-k",ref],env=env)
                content=run.stdout.decode("utf-8","replace")
                passing.append(run.returncode==0 and secret in content)
            report[kind+"_passing_distinct_reference_keys"]=sum(passing)
            report[kind+"_all_exact_reference_keys"]=all(passing)
        report["head_reads_verse_53_separately"]=report["head_all_exact_reference_keys"]
        report["stock_reads_verse_53_separately"]=report["stable_all_exact_reference_keys"]
        report["stock_runtime_supports_module_exactly"]=report["stable_all_exact_reference_keys"]
        report["status"]="synthetic_head_and_stable_runtime_compared"
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--head-prefix",type=Path,required=True)
    ap.add_argument("--stable-diatheke",default="/usr/bin/diatheke")
    args=ap.parse_args()
    report=run(args.head_prefix,args.stable_diatheke)
    print(json.dumps(report,indent=2,sort_keys=True))
    if report["status"]!="synthetic_head_and_stable_runtime_compared":
        raise SystemExit(1)


if __name__=="__main__":
    main()
