#!/usr/bin/env python3
"""Prepare a text-free upstream correction request from a verified OSIS diff.

The actual diff is private by default; no upstream issue/PR is posted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from normalize_osis import EditorialError, checksum


def proposal(plan_file: Path, report_file: Path, *, provider: str,
             module_id: str, source_revision: str) -> str:
    plan_bytes=Path(plan_file).read_bytes()
    plan=json.loads(plan_bytes)
    report=json.loads(Path(report_file).read_text(encoding="utf-8"))
    if (report.get("status")!="structural_edit_verified_not_published"
            or report.get("plan_sha256")!=checksum(plan_bytes)
            or report.get("source_sha256")!=plan.get("source_sha256")
            or report.get("edition")!=plan.get("edition")
            or report.get("kind")!=plan.get("kind")
            or not report.get("full_text_exactly_preserved")
            or not report.get("inline_semantic_tags_preserved")
            or not report.get("original_source_unchanged")
            or not report.get("operations")):
        raise EditorialError("Only a matching approved and fully verified normalizer report may generate a proposal")
    if not provider.strip() or not module_id.strip() or not source_revision.strip():
        raise EditorialError("Source provider/module/version identification is required")
    edits=plan.get("edits")
    if len(edits)!=len(report["operations"]):
        raise EditorialError("Plan operations disagree with verified report")
    lines=[
        "# Editorial source markup correction proposal",
        "",
        f"- Source provider: {provider}",
        f"- SWORD module: {module_id}",
        f"- Source version: {source_revision}",
        f"- Edition type: {plan['edition']}",
        f"- Original source SHA-256: {report['source_sha256']}",
        f"- Revised OSIS source SHA-256: {report['output_sha256']}",
        f"- Reviewed plan SHA-256: {report['plan_sha256']}",
        f"- Private before/after diff SHA-256: {report['diff_sha256']}",
        f"- Review evidence: {plan['review']['evidence_url']}",
        "",
        "## Proposed changes",
        "",
    ]
    for i,(edit,verified) in enumerate(zip(edits,report["operations"]),1):
        if edit["operation"]!=verified["operation"] or edit["source_reference"]!=verified["source_reference"]:
            raise EditorialError("Verified operation mismatch in source-key proposal")
        lines.extend([
            f"{i}. {edit['source_reference']}: {edit['operation']}",
            f"   - Reason: {edit['reason']}",
            "",
        ])
    lines += [
        "## Verification and submission limits",
        "",
        "- The original source was not modified.",
        "- Source and revised edition passed the same reviewed, pinned CrossWire OSIS XSD.",
        "- The serialized output preserved the exact character stream, notes, keys and inline semantic markup.",
        "- Editorial changes are confined to the explicitly reviewed layout operations above.",
        "- This proposal does **not** claim the rebuilt SWORD module passed a full round trip or GTK visual review.",
        "- The actual source patch/diff remains private; attach it only after checking upstream contribution permissions.",
        "- No issue, pull request or release has been submitted by this generator.",
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan",type=Path,required=True)
    p.add_argument("--normalization-report",type=Path,required=True)
    p.add_argument("--provider",required=True)
    p.add_argument("--module",required=True)
    p.add_argument("--source-revision",required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        print("Refusing existing upstream proposal output",file=sys.stderr)
        return 1
    try:
        value=proposal(args.plan,args.normalization_report,provider=args.provider,
                       module_id=args.module,source_revision=args.source_revision)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(value,encoding="utf-8")
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("Upstream proposal blocked: "+str(exc),file=sys.stderr)
        return 1
    print("Prepared private, text-free upstream review draft: "+str(args.output))
    return 0


if __name__=="__main__":
    sys.exit(main())
