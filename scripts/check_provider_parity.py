#!/usr/bin/env python3
"""Verify that Bible Resources tracks every declared Bible content source.

Reads only source declarations, not Bible texts or executable source imports.
Exit 1 means a reproducible inventory mismatch; exit 2 means the source
repository could not be checked. Never treat a failed fetch as "in sync".
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BIBLE_RAW = "https://raw.githubusercontent.com/icfmp/Bible"
SOURCE_FILES = ("bible/providers.py", "bible/reference_data.py", "bible/topic_data.py")
MAX_SOURCE = 256 * 1024


def download(url: str) -> str:
    if urlsplit(url).scheme != "https":
        raise ValueError("Only HTTPS sources are supported")
    request = urllib.request.Request(url, headers={"User-Agent": "BibleResources-SourceParity/1.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        final = urlsplit(response.url)
        if final.scheme != "https" or final.hostname != "raw.githubusercontent.com":
            raise ValueError("Unexpected source redirect")
        data = response.read(MAX_SOURCE + 1)
    if len(data) > MAX_SOURCE:
        raise ValueError("Source file is too large")
    return data.decode("utf-8")


def bible_sources(root: Path | None = None, ref: str = "main") -> dict[str, str]:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,100}", ref) or ".." in ref:
        raise ValueError("Invalid Bible ref")
    return {
        path: (root / path).read_text(encoding="utf-8") if root is not None
        else download(f"{BIBLE_RAW}/{ref}/{path}")
        for path in SOURCE_FILES
    }


def named_assignments(source: str) -> dict[str, ast.expr]:
    tree = ast.parse(source)
    result = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result[target.id] = node.value
    return result


def declared_providers(source: str) -> list[dict]:
    nodes = named_assignments(source)
    active = nodes.get("PROVIDERS")
    if not isinstance(active, (ast.Tuple, ast.List)):
        raise ValueError("Bible PROVIDERS declaration cannot be inspected safely")
    providers = []
    for element in active.elts:
        if not isinstance(element, ast.Name):
            raise ValueError("Unexpected provider expression")
        call = nodes.get(element.id)
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != "Provider":
            raise ValueError("Unexpected provider definition: " + element.id)
        if len(call.args) != 5 or call.keywords:
            raise ValueError("Unexpected Provider signature")
        values = [ast.literal_eval(argument) for argument in call.args]
        if not all(isinstance(value, str) for value in values):
            raise ValueError("Nonliteral provider field")
        identifier, name, source_url, catalogue_url, packages_url = values
        providers.append(dict(id=identifier, name=name, source_url=source_url,
                              catalogue_url=catalogue_url, packages_url=packages_url))
    return providers


def literal_constant(source: str, key: str) -> str:
    expr = named_assignments(source).get(key)
    if expr is None:
        raise ValueError("Missing Bible constant: " + key)
    value = ast.literal_eval(expr)
    if not isinstance(value, str) or not value.startswith("https://"):
        raise ValueError("Invalid Bible source URL: " + key)
    return value


def expected_inventory(sources: dict[str, str]) -> tuple[dict, dict]:
    modules, external = {}, {}
    for item in declared_providers(sources["bible/providers.py"]):
        identifier = item["id"]
        if item["catalogue_url"].endswith("/mods.d.tar.gz") and item["packages_url"]:
            modules[identifier] = item
        else:
            external[identifier] = item
    for path, identifier in (
        ("bible/reference_data.py", "openbible-cross-references"),
        ("bible/topic_data.py", "openbible-topics"),
    ):
        source = sources[path]
        external[identifier] = {
            "id": identifier,
            "source_url": literal_constant(source, "SOURCE_URL"),
            "download_url": literal_constant(source, "DOWNLOAD_URL"),
        }
    return modules, external


def compare(config: dict, sources: dict[str, str]) -> dict:
    expected_sword, expected_external = expected_inventory(sources)
    errors = []
    sword_rows = config.get("providers", [])
    external_rows = config.get("external_sources", [])
    if not isinstance(sword_rows, list) or not isinstance(external_rows, list):
        raise ValueError("Provider configuration must contain two lists")

    def index(rows, kind):
        result = {}
        for item in rows:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                errors.append(f"{kind}: invalid provider entry")
                continue
            identifier = item["id"]
            if identifier in result:
                errors.append(f"{kind}: duplicate {identifier}")
            result[identifier] = item
        return result

    actual_sword = index(sword_rows, "SWORD")
    actual_external = index(external_rows, "external")
    for expected, actual, kind in (
        (expected_sword, actual_sword, "SWORD"),
        (expected_external, actual_external, "external"),
    ):
        for identifier in sorted(expected.keys() - actual.keys()):
            errors.append(f"{kind}: Bible declares missing source {identifier}")
        for identifier in sorted(actual.keys() - expected.keys()):
            errors.append(f"{kind}: Bible no longer declares {identifier}")
        for identifier in sorted(expected.keys() & actual.keys()):
            original, recorded = expected[identifier], actual[identifier]
            if kind == "SWORD":
                catalogue = original["catalogue_url"]
                directory = catalogue.rsplit("/", 1)[0] + "/"
                checks = {
                    "kind": "sword", "source_url": original["source_url"],
                    "catalogue_url": catalogue, "packages_url": original["packages_url"],
                    "base_url": directory,
                }
            elif identifier == "youversion":
                checks = {"kind": "api", "source_url": original["source_url"],
                          "catalogue_url": original["catalogue_url"]}
            else:
                checks = {"kind": "dataset", "source_url": original["source_url"],
                          "download_url": original["download_url"]}
            for field, expected_value in checks.items():
                if recorded.get(field) != expected_value:
                    errors.append(f"{kind}: {identifier}.{field} differs from Bible")
            if kind == "external" and recorded.get("monitoring") != "inventory_only":
                errors.append(f"external: {identifier} must explicitly use inventory_only until an adapter is implemented")
    for entry in sword_rows + external_rows:
        for key in ("source_url", "base_url", "catalogue_url", "packages_url", "download_url"):
            value = entry.get(key) if isinstance(entry, dict) else None
            if value is not None and value != "" and (
                not isinstance(value, str) or urlsplit(value).scheme != "https"
            ):
                errors.append(f"{entry.get('id')}: invalid {key}")
    return {
        "schema_version": 1,
        "status": "in_sync" if not errors else "drift",
        "bible_sword_providers": sorted(expected_sword),
        "bible_external_sources": sorted(expected_external),
        "errors": errors,
        "source_sha256": {path: hashlib.sha256(content.encode("utf-8")).hexdigest()
                          for path, content in sources.items()},
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--bible-root", type=Path, help="Offline Bible checkout for tests")
    parser.add_argument("--bible-ref", default="main")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        config = json.loads((args.root / "config/upstreams.json").read_text(encoding="utf-8"))
        if config.get("schema_version") != 2:
            raise ValueError("Unsupported upstream registry schema")
        sources = bible_sources(args.bible_root, args.bible_ref)
        result = compare(config, sources)
        exit_code = 0 if result["status"] == "in_sync" else 1
    except (OSError, UnicodeError, ValueError, SyntaxError) as exc:
        result = {"schema_version": 1, "status": "unavailable",
                  "error": str(exc), "errors": ["Bible inventory could not be checked"]}
        exit_code = 2
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
