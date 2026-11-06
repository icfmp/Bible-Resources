#!/usr/bin/env python3
"""Build an HTTPS JSON catalogue and a standard SWORD repository deterministically."""
from pathlib import Path
import argparse
import gzip
import hashlib
import io
import json
import shutil
import tarfile
import zipfile
from urllib.parse import urlparse
from validate import ROOT,validate

def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def build(root=ROOT, output=None, base_url="https://icfmp.github.io/Bible-Resources/"):
    output = Path(output) if output else root/"dist"
    p=urlparse(base_url)
    if p.scheme!="https" or not p.netloc or p.query or p.fragment:
        raise ValueError("HTTPS base URL required")
    base_url=base_url.rstrip("/")+"/"
    modules,errors=validate(root)
    if errors: raise ValueError("\n".join(errors))
    output=output.resolve()
    if output==root.resolve() or root.resolve().is_relative_to(output):
        raise ValueError("unsafe output location")
    if output.exists():shutil.rmtree(output)
    sword=output/"sword"
    for sub in ("mods.d","modules","packages"): (sword/sub).mkdir(parents=True,exist_ok=True)
    (output/"catalog/v1").mkdir(parents=True)
    catalog=[]
    for d,m in modules:
        if m["quality"]["status"]!="approved":continue
        payload=d/"payload"
        files=sorted((p,p.relative_to(payload).as_posix()) for p in payload.rglob("*") if p.is_file())
        for src,rel in files:
            dest=sword/rel
            if dest.exists():raise ValueError("collision: "+rel)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(src,dest)
        pkg=sword/"packages"/(m["sword_id"]+".zip")
        with zipfile.ZipFile(pkg,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for src,rel in sorted(files,key=lambda item:item[1]):
                info=zipfile.ZipInfo(rel,(1980,1,1,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=0o100644<<16
                z.writestr(info,src.read_bytes())
        catalog.append({"id":m["id"],"sword_id":m["sword_id"],"title":m["title"],
                        "category":m["category"],"language":m["language"],"version":m["version"],
                        "versification":m.get("versification"),"edition":m["quality"]["edition"],
                        "download":{"url":base_url+"sword/packages/"+pkg.name,
                                    "sha256":sha256(pkg),"size_bytes":pkg.stat().st_size}})
    catalog.sort(key=lambda x:x["id"])
    with (sword/"mods.d.tar.gz").open("wb") as out:
        with gzip.GzipFile(filename="",fileobj=out,mode="wb",mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode="w") as tar:
                for p in sorted((sword/"mods.d").rglob("*")):
                    if p.is_file():
                        data=p.read_bytes();info=tarfile.TarInfo(p.relative_to(sword).as_posix())
                        info.size=len(data);info.mode=0o644;info.mtime=0
                        tar.addfile(info,io.BytesIO(data))
    manifest={"schema_version":1,"repository":"Bible Resources","repository_url":base_url,
              "modules":catalog}
    (output/"catalog/v1/catalog.json").write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (output/".nojekyll").write_text("")
    (output/"index.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Bible Resources</title><h1>Bible Resources</h1><p>Curated SWORD modules; unapproved resources are never published.</p><a href="catalog/v1/catalog.json">JSON catalogue</a></html>\n',encoding="utf-8")
    if sum(p.stat().st_size for p in output.rglob("*") if p.is_file())>400*1024*1024:
        raise ValueError("GitHub Pages size limit exceeded")
    return catalog

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=ROOT/"dist")
    p.add_argument("--base-url",default="https://icfmp.github.io/Bible-Resources/")
    a=p.parse_args()
    print(f"Published {len(build(output=a.output,base_url=a.base_url))} modules")
if __name__=="__main__":main()
