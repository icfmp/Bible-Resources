#!/usr/bin/env python3
"""Bounded commentary translation packets, structural checks and issue sync.

No editorial decisions or publication; source OSIS remains authoritative.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import tempfile

from lxml import etree
from source_osis_inventory import _read_source, _source_tree, OSIS

KEY = re.compile(r"[1-4]?[A-Za-z][A-Za-z0-9]*\.[1-9][0-9]*")


def chapters(root):
    result = {}
    for node in root.iter():
        if node.tag != OSIS + "chapter" and not (
            node.tag == OSIS + "div" and node.get("type") == "chapter"
        ):
            continue
        if node.get("sID") or node.get("eID"):
            continue
        key = node.get("osisID", "")
        if not KEY.fullmatch(key) or key in result or any(
            parent in result.values() for parent in node.iterancestors()
        ):
            raise ValueError(f"Invalid, duplicate or nested chapter: {key}")
        result[key] = node
    if not result:
        raise ValueError("No container chapters found")
    return result


def xml(node):
    return etree.tostring(node, encoding="unicode", with_tail=False)


def signature(node):
    """Structure, attributes and order; no claim about semantic equivalence."""
    return (node.tag, tuple(sorted(node.attrib.items())),
            tuple(signature(child) for child in node))


def read(path, expected):
    raw = _read_source(Path(path))
    if sha256(raw).hexdigest() != expected:
        raise ValueError(f"Source hash mismatch: {path}")
    return _source_tree(raw)


def audit_text(node):
    """Readable audit projection, not an authoritative source or reverse map."""
    def visit(element):
        if element.get("annotateRef") and not (
            element.get("sID") or element.get("eID")
        ):
            yield "\n[" + element.get("annotateRef") + "]\n"
        if element.tag in {OSIS + "title", OSIS + "p", OSIS + "row"}:
            yield "\n"
        if element.tag == OSIS + "div" and element.get("type") == "x-p" and element.get("sID"):
            yield "\n"
        if element.text:
            yield element.text
        for child in element:
            yield from visit(child)
            if child.tail:
                yield child.tail
        if element.get("osisRef"):
            yield " [" + element.get("osisRef") + "]"
        if element.tag == OSIS + "cell":
            yield " | "
        if element.tag in {OSIS + "title", OSIS + "p", OSIS + "row"}:
            yield "\n"
    return "\n".join(" ".join(line.split()) for line in "".join(visit(node)).splitlines() if line.strip())


def extract(args):
    modern = read(args.modern, args.modern_sha)
    classic = read(args.classic, args.classic_sha)
    left, right = chapters(modern), chapters(classic)
    if list(left) != list(right):
        raise ValueError("Chapter order/coverage differs; editorial review required")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    for key in left:
        packet = {"chapter": key, "modern_osis": xml(left[key]),
                  "classic_reading": audit_text(right[key])}
        (output / (key + ".json")).write_text(
            json.dumps(packet, ensure_ascii=False) + "\n", encoding="utf-8")
    outside = []
    for label, root, mapping in (("modern", modern, left), ("classic", classic, right)):
        selected = set(mapping.values())
        for node in root.iter():
            if any(p in selected for p in node.iterancestors()):
                continue
            if node in selected:
                if (node.tail or "").strip():
                    outside.append({"source": label, "path": root.getroottree().getpath(node), "tail": node.tail})
                continue
            if (node.text or "").strip() or (node.tail or "").strip():
                outside.append({"source": label, "path": root.getroottree().getpath(node),
                                "text": node.text, "tail": node.tail})
    (output / "manifest.json").write_text(json.dumps({
        "modern_sha256": args.modern_sha, "classic_sha256": args.classic_sha,
        "chapters": list(left), "outside_chapter_text": outside,
        "note": "Outside-chapter material requires explicit editorial review; audit reading is a projection."
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": len(left), "outside_text_nodes": len(outside)}))


def check(args):
    root = read(args.modern, args.modern_sha)
    source = chapters(root)
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    files = sorted(Path(args.manuscripts).glob("*.xml"))
    if not files:
        raise ValueError("No manuscript fragments found")
    for file in files:
        if file.stem not in source:
            raise ValueError(f"Unexpected manuscript: {file.name}")
        target = etree.parse(str(file), parser)
        if target.docinfo.doctype or signature(target.getroot()) != signature(source[file.stem]):
            raise ValueError(f"Structure/attributes differ: {file.name}")
    print(json.dumps({"checked_fragments": len(files), "semantic_review": False}))


def assemble(args):
    """Assemble a complete editorial candidate, never an approved module."""
    source = chapters(read(args.modern, args.modern_sha))
    template = _source_tree(_read_source(Path(args.template)))
    target = chapters(template)
    if list(source) != list(target):
        raise ValueError("Target template chapter order/coverage differs")
    text = template.find(OSIS + "osisText")
    if text is None or text.get("{http://www.w3.org/XML/1998/namespace}lang") != args.language:
        raise ValueError("Template must carry the explicitly selected target language")
    # The separately reviewed target template owns header and non-chapter
    # content. This command cannot decide or certify those translations.
    files = {p.stem: p for p in Path(args.manuscripts).glob("*.xml")}
    if set(files) != set(source):
        raise ValueError("Incomplete or unexpected chapter manuscript inventory")
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    for key, old in target.items():
        fragment = etree.parse(str(files[key]), parser)
        replacement = fragment.getroot()
        if fragment.docinfo.doctype or signature(replacement) != signature(source[key]):
            raise ValueError(f"Source structure/attributes differ: {key}")
        if signature(old) != signature(source[key]):
            raise ValueError(f"Template structure/attributes differ: {key}")
        replacement.tail = old.tail
        old.getparent().replace(old, replacement)
    output = Path(args.output)
    data = etree.tostring(template, encoding="UTF-8", xml_declaration=True)
    # Exclusive output creation: no source or previously reviewed file overwritten.
    with output.open("xb") as handle:
        handle.write(data)
    print(json.dumps({"assembled_chapters": len(source), "editorial_candidate": True,
                      "semantic_review": False, "publication": False}))


TASK = re.compile(r"^- \[([ x])\] (\d+) — (Translation|Editorial audit)$")
HEADING = re.compile(r"^### (.+)$")


def sync_body(body, progress):
    """Preserve all non-checklist lines, release gates and owner prose."""
    completed = {tuple(x) for x in progress["completed"]}
    if len(completed) != len(progress["completed"]):
        raise ValueError("Duplicate progress record")
    if any(kind not in ("Translation", "Editorial audit") for _, _, kind in completed):
        raise ValueError("Unknown progress task")
    if any((book, ch, "Translation") not in completed for book, ch, kind in completed if kind == "Editorial audit"):
        raise ValueError("Audit without translation")
    seen = set()
    book = None
    lines = []
    for line in body.splitlines(keepends=True):
        raw = line.rstrip("\r\n")
        heading = HEADING.fullmatch(raw)
        if heading:
            book = heading[1]
        task = TASK.fullmatch(raw)
        if task:
            key = (book, int(task[2]), task[3])
            if key in seen:
                raise ValueError("Duplicate issue task")
            seen.add(key)
            if task[1] == "x" and key not in completed:
                raise ValueError(f"Refusing to undo existing checkmark: {key}")
            raw = raw[:3] + ("x" if key in completed else " ") + raw[4:]
            line = raw + line[len(line.rstrip("\r\n")):]
        lines.append(line)
    if len(seen) != 2 * progress["total_chapters"] or not completed <= seen:
        raise ValueError("Issue/progress inventory mismatch")
    return "".join(lines)


def sync(args):
    progress = json.loads(Path(args.progress).read_text(encoding="utf-8"))
    repo, issue = progress["repository"], str(progress["issue"])
    def fetch():
        return json.loads(subprocess.check_output(
            ["gh", "issue", "view", issue, "--repo", repo, "--json", "body"], text=True))["body"]
    original = fetch()
    new = sync_body(original, progress)
    print(json.dumps({"changed": new != original,
                      "translated": sum(x[2] == "Translation" for x in progress["completed"]),
                      "audited": sum(x[2] == "Editorial audit" for x in progress["completed"])}))
    if not args.apply or new == original:
        return
    if fetch() != original:
        raise ValueError("Issue changed during sync; retry after reconciliation")
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "body.md"
        path.write_text(new, encoding="utf-8")
        subprocess.run(["gh", "issue", "edit", issue, "--repo", repo,
                        "--body-file", str(path)], check=True)
    if fetch() != new:
        raise ValueError("Issue post-write verification failed")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    subs = cli.add_subparsers(required=True)
    e = subs.add_parser("extract")
    for name in ("modern", "modern-sha", "classic", "classic-sha", "output"):
        e.add_argument("--" + name, required=True)
    e.set_defaults(run=extract)
    c = subs.add_parser("check")
    for name in ("modern", "modern-sha", "manuscripts"):
        c.add_argument("--" + name, required=True)
    c.set_defaults(run=check)
    a = subs.add_parser("assemble")
    for name in ("modern", "modern-sha", "manuscripts", "template", "language", "output"):
        a.add_argument("--" + name, required=True)
    a.set_defaults(run=assemble)
    s = subs.add_parser("sync")
    s.add_argument("--progress", required=True)
    s.add_argument("--apply", action="store_true")
    s.set_defaults(run=sync)
    args = cli.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
