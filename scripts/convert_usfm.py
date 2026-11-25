#!/usr/bin/env python3
"""Convert a registered immutable USFM/USFX source pair to a private OSIS candidate.

No source changes, semantic target inference, compilation or publication.
Supported original grammar is determined by the independent witnesses.
"""
from __future__ import annotations
import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import traceback
import zipfile

from guard_osis import ROOT, _schema
from pilot_preflight import inspect_archive
from source_osis_inventory import source_inventory, _source_tree
from research.bible.original_authorial_key_inventory import usfm, usfx, compare
from research.bible.usfm_source_projection import project
from research.bible.usfm_converter_patch import deterministic_patch

def work_id(module_id):
    """A work ID is an OSIS identifier, not a hyphenated repository slug."""
    if not isinstance(module_id,str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*",module_id):
        raise ValueError("A registered alphanumeric OSIS work identifier is required")
    return "Bible."+module_id


def run(resource, upstream, schema_path, epoch, report, *, root=ROOT):
    if sys.flags.optimize:
        raise RuntimeError("Conversion requires active validation assertions")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}",resource) or not 0<=epoch<=253402300799:
        raise ValueError("Invalid registered resource ID or generation epoch")
    a=json.loads((root/"config/original-bible-content-adapters.json").read_text())["resources"][resource]
    m=json.loads((root/"modules"/resource/"metadata.json").read_text())
    language=m["language"]
    identity=work_id(m["sword_id"])
    assert re.fullmatch(r"[A-Za-z0-9-]{1,35}",language)
    folder=root/"sources/original/bibles"/language/resource
    p=json.loads((folder/"PROVENANCE.json").read_text())
    w=p["additional_original_witness"]
    assert p["format"]=="USFM" and w["format"]=="USFX"
    fm=folder/p["original_file"]; fx=folder/w["filename"]
    for path,digest,size in ((fm,p["original_sha256"],p["original_size_bytes"]),(fx,w["sha256"],w["size_bytes"])):
        receipt=inspect_archive(path,source_kind="authored")
        assert receipt["archive_sha256"]==digest and receipt["archive_bytes"]==size
    assert a["usfm_sha256"]==p["original_sha256"] and a["usfx_sha256"]==w["sha256"]
    crosswalk_raw=(root/a["crosswalk"]).read_bytes()
    crosswalk=json.loads(crosswalk_raw)
    mapping={x["usfm"]:x["osis"] for x in crosswalk["books"]}
    assert len(mapping)==len(crosswalk["books"])==len(set(mapping.values()))
    policy=json.loads((root/"config/osis-policy.json").read_text())
    schema,schema_hash=_schema(policy,schema_path.absolute())
    raw_converter=upstream.read_bytes()
    reviewed=deterministic_patch(raw_converter)
    report.update(resource=resource,osis_work_id=identity,source_usfm_sha256=a["usfm_sha256"],
        source_usfx_sha256=a["usfx_sha256"],crosswalk_sha256=sha256(crosswalk_raw).hexdigest(),
        original_converter_sha256=sha256(raw_converter).hexdigest(),
        converter_sha256=sha256(reviewed).hexdigest(),source_date_epoch=epoch,
        python_version=sys.version.split()[0],published=False,approved_for_publication=False,
        conversion_fidelity_certified=False)
    with tempfile.TemporaryDirectory(prefix="bible-usfm-conversion-") as temp,zipfile.ZipFile(fm) as zfm,zipfile.ZipFile(fx) as zfx:
        directory=Path(temp)
        left,_=usfm(zfm);right,_=usfx(zfx,a["usfx_member"])
        assert compare(left,right)["ordered_labels_within_every_book_equal"]
        assert set(left)<=set(mapping)
        source_xml=zfx.read(a["usfx_member"])
        converter=directory/"reviewed.py";converter.write_bytes(reviewed)
        files=[]
        for item in zfm.infolist():
            if item.is_dir() or PurePosixPath(item.filename).suffix.lower() not in {".usfm",".sfm"}:continue
            dest=directory/"input"/PurePosixPath(item.filename)
            assert dest.resolve().is_relative_to((directory/"input").resolve())
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open("xb") as out:out.write(zfm.read(item))
            files.append(dest)
        assert len(files)==len(left)
        candidate=directory/"candidate.osis.xml"
        command=[sys.executable,str(converter),identity,"-l",language,"-x","-o",str(candidate),*map(str,sorted(files))]
        environment=dict(os.environ,SOURCE_DATE_EPOCH=str(epoch),PYTHONHASHSEED="0",TZ="UTC",LOGNAME="BibleResources",USERNAME="BibleResources")
        generated=[]
        for _ in range(2):
            with tempfile.TemporaryFile() as log:
                proc=subprocess.run(command,cwd=directory,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=180,check=False)
                assert log.tell()<=128*1024*1024
            assert proc.returncode==0 and candidate.is_file() and candidate.stat().st_size<=128*1024*1024
            generated.append(candidate.read_bytes());candidate.unlink()
        assert generated[0]==generated[1],"Converter is not byte reproducible"
        report["repeated_conversion_byte_identical"]=True
        report["raw_candidate_sha256"]=sha256(generated[0]).hexdigest()
        keys,_=source_inventory(generated[0])
        expected=[mapping[book]+"."+chapter+"."+verse for book,rows in right.items() for chapter,verse in rows]
        assert keys.splitlines()==expected,"Original numbering/order changed"
        final=project(source_xml,generated[0],mapping,zfm,report)
        # Verify the entire post-conversion transformation twice, independently.
        repeated={}
        assert project(source_xml,generated[1],mapping,zfm,repeated)==final
        report["repeated_projected_candidate_byte_identical"]=True
        assert source_inventory(final)[0].splitlines()==expected
        schema_valid=schema.validate(_source_tree(final))
        report["official_xsd"]={"sha256":schema_hash,"valid":schema_valid,
            "error_count":len(schema.error_log),"error_types":dict(Counter(e.type_name for e in schema.error_log)),
            "first_error_lines":[e.line for e in list(schema.error_log)[:10]],
            "first_error_paths":[e.path for e in list(schema.error_log)[:10]]}
        assert schema_valid,"Converted candidate fails official XSD"
        assert sha256(fm.read_bytes()).hexdigest()==a["usfm_sha256"] and sha256(fx.read_bytes()).hexdigest()==a["usfx_sha256"]
        report["candidate_sha256"]=sha256(final).hexdigest()
        report["supported_source_conversion_verified"]=True
        report["status"]="private_candidate_verified_not_approved"
        report["limitations"]=["Explicit reference destination semantics require a separate original-source review",
            "Exact typography, unsupported grammar and SWORD reader acceptance are separate checks",
            "No redistribution or editorial approval is inferred"]
        return final

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource",required=True)
    parser.add_argument("--converter",type=Path,required=True,help="Exact pinned upstream u2o.py")
    parser.add_argument("--schema",type=Path,required=True)
    parser.add_argument("--source-date-epoch",type=int,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True)
    args=parser.parse_args(argv)
    if args.output.resolve()==args.report.resolve() or any(p.exists() or p.is_symlink() for p in (args.output,args.report)):
        parser.error("Refusing to overwrite a source, report or candidate")
    report={"status":"blocked","published":False}
    try:
        final=run(args.resource,args.converter,args.schema,args.source_date_epoch,report)
        with args.output.open("xb") as stream:stream.write(final)
    except Exception as exc:
        report["status"]="blocked"
        report["audit_blocked_by"]=type(exc).__name__
        report["audit_blocked_frames"]=[{"function":f.name,"line":f.lineno} for f in traceback.extract_tb(exc.__traceback__)[-8:]]
    with args.report.open("x",encoding="utf-8") as stream:json.dump(report,stream,sort_keys=True,indent=2)
    print("GENERIC_USFM_CONVERSION",json.dumps(report,sort_keys=True),flush=True)
    return 0 if report["status"]=="private_candidate_verified_not_approved" else 1

if __name__=="__main__":
    raise SystemExit(main())
