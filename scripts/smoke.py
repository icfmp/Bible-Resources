#!/usr/bin/env python3
"""Check actual SWORD interoperability using diatheke. Do not certify skipped tests."""
import os,sys,shutil,subprocess
from pathlib import Path
from validate import ROOT,validate
def main():
    modules,errors=validate()
    if errors: print(*errors,sep="\n",file=sys.stderr);return 1
    approved=[m for _,m in modules if m["quality"]["status"]=="approved"]
    if not approved: print("SWORD runtime test SKIPPED (zero approved modules)");return 0
    exe=shutil.which("diatheke")
    if not exe: print("diatheke is required",file=sys.stderr);return 1
    env=dict(os.environ,SWORD_PATH=str(ROOT/"dist/sword"))
    for m in approved:
        p=subprocess.run([exe,"-b",m["sword_id"],"-k",m["quality"]["smoke_key"],"-f","plain"],
                         env=env,text=True,capture_output=True,timeout=30)
        if p.returncode or not p.stdout.strip() or "not found" in p.stdout.lower():
            print(f"SWORD ERROR {m['sword_id']}: {p.stderr} {p.stdout[:120]}",file=sys.stderr);return 1
        print("SWORD OK",m["sword_id"])
    return 0
if __name__=="__main__":raise SystemExit(main())
