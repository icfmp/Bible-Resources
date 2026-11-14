#!/usr/bin/env python3
"""Check genuine SWORD interoperability with diatheke for every approved module.

A natural-language commentary may legitimately contain "not found" within
the authorial prose. Never search the entire Bible/commentary output for
generic English fragments when classifying errors, and never print original
content in public CI logs.
"""
import os
import re
import sys
import shutil
import subprocess
from validate import ROOT, validate

# Only actual reader diagnostics at the BEGINNING of the response indicate
# errors. Once diatheke has emitted a passage header, subsequent words are
# authorial material, not diagnostic status.
_DIAGNOSTIC_PREFIX = re.compile(
    r"^(?:error:\s|usage:\s*diatheke|"
    r"module\s+.{1,120}?\s+not\s+found\b|"
    r"no\s+modules\s+(?:available|found)\b|"
    r"unable\s+to\s+find\s+module\b|"
    r"not\s+a\s+valid\s+(?:module|verse|reference)\b)",
    re.IGNORECASE,
)


def reader_failure_class(code: int, output: str) -> str | None:
    """Bounded, text-free classification; never leak original passage words."""
    if code != 0:
        return "nonzero_exit"
    if not isinstance(output, str) or not output.strip():
        return "empty_output"
    if _DIAGNOSTIC_PREFIX.match(output.lstrip()[:256]):
        return "reader_diagnostic"
    return None


def main():
    modules,errors=validate()
    if errors:
        print(*errors,sep="\n",file=sys.stderr)
        return 1
    approved=[m for _,m in modules if m["quality"]["status"]=="approved"]
    if not approved:
        print("SWORD runtime test SKIPPED (zero approved modules)")
        return 0
    exe=shutil.which("diatheke")
    if not exe:
        print("diatheke is required",file=sys.stderr)
        return 1
    env=dict(os.environ,SWORD_PATH=str(ROOT/"dist/sword"))
    for m in approved:
        p=subprocess.run(
            [exe,"-b",m["sword_id"],"-k",m["quality"]["smoke_key"],"-f","plain"],
            env=env,text=True,capture_output=True,timeout=30)
        failure=reader_failure_class(p.returncode,p.stdout)
        if failure is not None:
            print(f"SWORD ERROR {m['sword_id']}: {failure} "
                  f"(exit={p.returncode}; output_bytes={len(p.stdout.encode())})",
                  file=sys.stderr)
            return 1
        print("SWORD OK",m["sword_id"])
    return 0


if __name__=="__main__":
    raise SystemExit(main())
