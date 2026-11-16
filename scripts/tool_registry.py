#!/usr/bin/env python3
"""Generate a source-bound, metadata-only inventory of all tracked tool scripts.

This is a maintenance inventory, NOT an import or rights approval. References
are static call-site candidates, not a claim that code is exercised. Unknown
tools stay UNDECIDED. No code/script is deleted or reformatted by the inventory.
"""
from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ROLES = frozenset({
    "KEEP_GENERIC", "GENERALIZE", "MERGE", "HISTORICAL/ARCHIVE", "UNDECIDED"
})
# Narrow, verified entry points. The rest are conservatively classified by
# explicit edition coupling or as pending review, never silently archived.
CORE = {
    "build.py", "validate.py", "release_preflight.py",
    "publish_reviewed_release.py", "catalogue_release_coverage.py",
    "verify_public_catalogue.py", "commentary_intake.py",
    "commentary_native_inventory.py", "commentary_native_raw_inventory.py",
    "reviewed_compiled_commentary_rebuild.py",
    "compiled_stock_commentary_proof.py", "guard_commentary.py",
    "sword_native_raw_corpus_inventory.py", "sword_native_inventory.py",
    "sword_native_commentary_index.cpp",
    "sword_native_commentary_raw_corpus.cpp",
}
EXPERIMENTS = (
    "commentary_chapter_", "commentary_nonlink_",
    "commentary_prose_cross_slot", "commentary_reference_cross_slot",
    "commentary_unresolved_lexical_triage",
)
EDITION_PREFIXES = (
    "stage_darby_", "prepare_darby_", "probe_darby_",
    "materialize_attested_lsg_", "lsg_", "darby_",
)
READER_NAMES = ("xiphos", "andbible", "android", "jsword", "webview")
PIN = re.compile(r"[a-f0-9]{64}")
FORMATS = ("RawText", "zText", "RawCom", "RawCom4", "zCom", "zCom4",
           "OSIS", "USFM", "USFX", "ThML")
FILE_BOUND = 500_000


def tracked(root: Path, *directories: str) -> list[Path]:
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--",
                             *directories], capture_output=True, check=True,
                            timeout=15)
    return sorted(root / part.decode("utf-8") for part in
                  result.stdout.split(b"\0") if part)


def _code(source: str) -> tuple[str, bool, tuple[str, ...]]:
    try:
        tree = ast.parse(source)
        doc = ast.get_docstring(tree) or ""
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(item.name.split(".", 1)[0] for item in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".", 1)[0])
    except (SyntaxError, ValueError):
        doc, imports = "", set()
    return doc.splitlines()[0][:220] if doc else "", (
        "__main__" in source or "if __name__" in source
    ), tuple(sorted(imports))


def classify(name: str, source: str, *, core=CORE) -> tuple[str, str]:
    if name in core:
        return "KEEP_GENERIC", "high"
    if name.startswith(EDITION_PREFIXES) or (
            any(token in name.lower() for token in ("darby", "mhcc", "lsg"))
            and name != "commentary_sword_identity_migration.py"):
        return "HISTORICAL/ARCHIVE", "medium"
    if any(name.startswith(prefix) for prefix in EXPERIMENTS):
        return "MERGE", "low"
    # Edition pinning inside an otherwise reusable-sounding script is exactly
    # the kind of code coupling that requires explicit extraction/review.
    if re.search(r"\b(?:BRMHCC|BRLSG1910|BRJND2024|mhcc-crosswire|"
                 r"darby-jnd-2024|lsg-1910)\b", source):
        return "GENERALIZE", "medium"
    if name.startswith(("commentary_", "source_", "sword_")):
        return "UNDECIDED", "low"
    return "UNDECIDED", "low"


def generate(root: Path = ROOT) -> dict:
    """Enumerate every tracked script and its checkable static callers.

    Dynamic subprocess arguments, GitHub API calls, workflow dispatch and
    historic Git revisions remain explicitly *outside* static reachability.
    """
    root = Path(root).resolve()
    sources = [p for p in tracked(root, "scripts")
               if p.is_file() and p.suffix in {".py", ".cpp", ".sh"}]
    others = [p for p in tracked(root, ".github/workflows", "tests", "docs")
              if p.is_file() and p.suffix in {".py", ".cpp", ".sh",
                                               ".yml", ".yaml", ".md"}]
    texts = {}
    for path in (*sources, *others):
        if path.is_symlink():
            raise ValueError("Symlink in tool reference inventory")
        if path.stat().st_size > FILE_BOUND:
            # Do not silently mistake oversized files for unused callers.
            raise ValueError(f"Tool reference exceeds bounded scan: {path}")
        texts[path.relative_to(root).as_posix()] = path.read_text(
            encoding="utf-8", errors="replace")
    records = []
    for path in sources:
        rel = path.relative_to(root).as_posix()
        source = texts[rel]
        purpose, cli, imports = _code(source) if path.suffix == ".py" else (
            next((ln.strip("/ *")[:220] for ln in source.splitlines()
                  if ln.strip("/ *")), ""), False, ())
        role, confidence = classify(path.name, source)
        stem = path.stem
        # Treat both qualified imports and literal filenames as static
        # evidence. Every reference is recorded with its exact caller path.
        literal = re.compile(r"(?<![A-Za-z0-9_])"
                             + re.escape(path.name) + r"(?![A-Za-z0-9_])")
        import_pat = re.compile(r"(?m)^\s*(?:from\s+" + re.escape(stem)
                                + r"(?:\s+import|\.)|import\s+"
                                + re.escape(stem) + r"(?:\s|$|,))")
        callers = [
            other for other, content in texts.items()
            if other != rel and (literal.search(content)
                                 or (path.suffix == ".py"
                                     and import_pat.search(content)))
        ]
        if path.name in CORE:
            next_step = "Retain stable verified interface; extend test fixtures."
        elif role == "HISTORICAL/ARCHIVE":
            next_step = ("Retain runnable historical evidence; extract shared "
                         "algorithms only after byte-equivalence tests.")
        elif role in {"MERGE", "GENERALIZE"}:
            next_step = ("Characterize output/provenance and historical callers; "
                         "extract into reusable code without changing receipts.")
        else:
            next_step = "Review source and callers before changing lifecycle."
        records.append({
            "path": rel,
            "purpose_first_line": purpose or "Not documented in source",
            "sha256_at_inventory": sha256(source.encode("utf-8")).hexdigest(),
            "classification": role,
            "confidence": confidence,
            "proposed_action": next_step,
            "entrypoint_hint": ("CLI or __main__ present" if cli else
                                "library, native helper or workflow-invoked"),
            "format_signals_not_certified_support":
                [fmt for fmt in FORMATS if re.search(r"\b" + re.escape(fmt)
                                                    + r"\b", source)],
            "reader_tool_signals":
                [name for name in READER_NAMES if name in source.lower()],
            "python_imports": imports,
            "static_references": callers,
            "static_reference_count": len(callers),
            "has_direct_tests_by_filename":
                f"tests/test_{stem}.py" in texts,
            "stage_hint": (
                "publication/release" if any(t in path.name for t in
                                             ("publish", "release", "build"))
                else "intake" if "intake" in path.name
                else "source/native audit" if any(t in path.name for t in
                                                  ("audit", "probe", "inventory",
                                                   "compare", "witness"))
                else "not determined"),
            "side_effects": ("unknown; inspect CLI and subprocesses before use"
                             if not path.name in CORE else
                             "consult the documented core tool contract"),
            "source_sha_requirement": (
                "must be separately checked; static scan is not proof"),
            "release_approval": "never inferred from inventory",
            "owner": "Bible Resources maintainers",
        })
    return {
        "schema_version": 1,
        "status": "SCRIPT_INVENTORY_STATIC_REVIEW_NOT_APPROVAL",
        "limitations": [
            "Static references are not proof of execution or non-use.",
            "Dynamic imports/subprocess calls and historical Git revisions "
            "require a separate manual review before removing a script.",
            "Format words are signals only, not supported-format certification.",
            "Classification is a review proposal, never an automatic deletion.",
            "No source text, full document content, archive or patient/user data "
            "is included in this report.",
        ],
        "files": records,
    }


def markdown(report: dict) -> str:
    records = report["files"]
    lines = [
        "# Tool registry — source-bound post-MHCC inventory",
        "",
        "This generated list covers every tracked \`scripts/*.py\`, \`*.cpp\` "
        "and \`*.sh\`. It lists static callers and review recommendations, "
        "**not** a licence to delete scripts or proof that they are exercised.",
        "Generate/check: \`python scripts/tool_registry.py --write\` / "
        "\`python scripts/tool_registry.py --check\`.",
        "The source-bound detailed registry is [TOOL_REGISTRY.json]"
        "(TOOL_REGISTRY.json). No publishing credentials or raw commentary "
        "content enter the inventory.",
        "",
        "## Lifecycle",
        "",
        "- **KEEP_GENERIC:** retain the stable interface and strengthen tests.",
        "- **GENERALIZE:** extract known edition-specific logic into a reviewed "
        "manifest, preserving existing proofs.",
        "- **MERGE:** candidate overlapping research functions; only merge after "
        "comparing outputs and historical dependencies.",
        "- **HISTORICAL/ARCHIVE:** retain for immutable proof/replay; archive "
        "only after evidence-based replacement, never by deleting blindly.",
        "- **UNDECIDED:** source/caller audit required; no inferred deletion.",
        "",
        "## Baseline counts",
        "",
    ]
    for status in sorted(ROLES):
        lines.append(f"- {status}: "
                     f"{sum(r['classification'] == status for r in records)}")
    lines += ["", "## All tracked tools", "",
              "| Script | Classification | Tests | Static callers | Stage hint |",
              "| --- | --- | --- | ---: | --- |"]
    for r in records:
        lines.append(
            f"| [\`{r['path']}\`](../{r['path']}) | "
            f"{r['classification']} | "
            f"{'named test' if r['has_direct_tests_by_filename'] else 'not established'} | "
            f"{r['static_reference_count']} | {r['stage_hint']} |")
    lines += ["", "## Safeguards and next steps", "",
              "Inventory every driver/rights/provenance contract before migrating "
              "an entry. Test actual compiled payload bytes and real native "
              "references in addition to any textual/static inventory.",
              "Only promote from proposed classification after issue review "
              "and a tested replacement; historical scripts may be needed "
              "to reproduce old signed or published releases.",
              "No registry entry authorizes editorial changes, user "
              "data changes or publication.",
              ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = generate(ROOT)
    expected = {
        ROOT / "docs/TOOL_REGISTRY.json":
            json.dumps(report, ensure_ascii=False, indent=2,
                       sort_keys=True) + "\n",
        ROOT / "docs/TOOL_REGISTRY.md": markdown(report),
    }
    if args.write:
        for path, body in expected.items():
            path.write_text(body, encoding="utf-8")
    else:
        drift = [str(path.relative_to(ROOT)) for path, body in expected.items()
                 if not path.is_file() or path.read_text(encoding="utf-8") != body]
        if drift:
            parser.error("Tool inventory changed: " + ", ".join(drift))
    print(f"Registered {len(report['files'])} tracked scripts; "
          "metadata-only, no source or release modified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
