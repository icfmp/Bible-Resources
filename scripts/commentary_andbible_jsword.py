#!/usr/bin/env python3
"""Independent pinned Android AndBible-stable JSword ENGINE test of stock zCom.

This script never builds, republishes, relabels or alters a commentary module.
It downloads the exact original SWORD ZIP, verifies its conf and native raw
SHA-256, installs it in a disposable SWORD_PATH, checks real diatheke entries,
and loads those entries through AndBible's pinned JSword Java implementation.

A Java engine test is not an Android application/GUI compatibility claim.
No original prose, Java test log or module bytes leave the temporary context.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from commentary_intake import load_manifest
from commentary_native_raw_inventory import _safe_stock_install
from commentary_stock_candidate import _native_content
from pilot_fetch import fetch
from pilot_preflight import PilotError, inspect_archive
from pilot_subprocess import present_key, query
from probe_andbible_jsword import AND_BIBLE_JSWORD_SHA, AND_BIBLE_RELEASE

SHA = re.compile(r"[a-f0-9]{64}\Z")
JUNIT = "org.icfmp.research.CommentaryAndBibleJSwordProbeTest"
TEST_NAME = JUNIT.rsplit(".", 1)[-1]
ROOT = Path(__file__).resolve().parents[1]
MAX_PRIVATE_LOG_BYTES = 4_000_000


def _junit_result(path: Path, *, exit_code: int) -> dict:
    """Bounded JUnit inspection; never surface a source text or failure trace."""
    if (path.is_symlink() or not path.is_file()
            or not 0 < path.stat().st_size <= 500_000):
        raise PilotError("Pinned AndBible JSword did not produce bounded JUnit evidence")
    try:
        result = ET.parse(path).getroot()
        if result.tag != "testsuite":
            raise ValueError("Unknown JUnit structure")
        counts = {name: int(result.attrib[name]) for name in ("tests", "errors", "failures")}
        counts["skipped"] = int(result.attrib.get("skipped", "0"))
    except (ET.ParseError, ValueError, KeyError, OverflowError):
        raise PilotError("Unreviewed JSword JUnit result metadata") from None
    if (exit_code != 0 or counts != {"tests": 3, "errors": 0, "failures": 0, "skipped": 0}):
        raise PilotError("AndBible JSword original-commentary engine checks failed")
    return counts


def _live_samples(manifest: dict, installed: Path, *, reader: str) -> tuple[list[str], list[str]]:
    """Select only verified substantive original entries, not empty key labels."""
    refs = manifest["sample_references"]
    selected = []
    digests = []
    for ref in refs:
        code, data = query(
            manifest["module_id"], ref, fmt="plain", root=installed, exe=reader,
            limit=256 * 1024, timeout=30,
        )
        if code != 0 or not present_key(ref, data, code):
            raise PilotError("Independent original commentary diatheke key is unreadable")
        if len(data) > 64:
            selected.append(ref)
            digests.append(sha256(data).hexdigest())
    if not 2 <= len(selected) <= 20 or not all(SHA.fullmatch(d) for d in digests):
        raise PilotError("Insufficient substantial independent stock commentary sample entries")
    return selected, digests


def _run_pinned_jsword(
    jsword: Path, installed: Path, scratch: Path, module_id: str, probes: list[str],
) -> dict:
    """Use exactly the earlier approved AndBible 5.1.1117 JSword source commit."""
    if (jsword.is_symlink() or not jsword.is_dir()
            or scratch.is_symlink() or not scratch.is_dir()
            or installed.is_symlink() or not installed.is_dir()
            or not (jsword / "gradlew").is_file()
            or not (jsword / "build.gradle.kts").is_file()
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}", module_id)
            or any(";" in p or "\n" in p for p in probes)
            or not 2 <= len(probes) <= 20):
        raise PilotError("Unsafe original module / independent JSword test context")
    checked = subprocess.run(
        ["git", "-C", str(jsword), "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=12, check=False,
    )
    if checked.returncode or checked.stdout.strip() != AND_BIBLE_JSWORD_SHA:
        raise PilotError("AndBible stable JSword revision differs from the pinned engine")
    original_test = ROOT / "tests/java/org/icfmp/research" / (TEST_NAME + ".java")
    destination = jsword / "src/test/java/org/icfmp/research" / (TEST_NAME + ".java")
    if (original_test.is_symlink() or not original_test.is_file()
            or destination.is_symlink() or destination.exists()):
        raise PilotError("Unreviewed or colliding independent Java commentary test")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(original_test, destination)
    home = scratch / "private-java-home"
    gradle = scratch / "private-gradle-cache"
    home.mkdir(mode=0o700)
    gradle.mkdir(mode=0o700)
    logfile = scratch / "private-jsword-build.log"
    env = dict(
        os.environ,
        COMMENTARY_JSWORD_MODULE_ROOT=str(installed),
        COMMENTARY_JSWORD_MODULE_ID=module_id,
        COMMENTARY_JSWORD_SAMPLES=";".join(probes),
        SWORD_PATH=str(installed),
        HOME=str(home),
        GRADLE_USER_HOME=str(gradle),
        JAVA_TOOL_OPTIONS="-Duser.home=" + str(home),
        LC_ALL="C.UTF-8",
        LANG="C.UTF-8",
    )
    with logfile.open("xb") as output:
        try:
            process = subprocess.run(
                ["bash", str(jsword / "gradlew"), "--no-daemon", "--console=plain",
                 "test", "--tests", JUNIT],
                cwd=jsword, env=env, stdout=output, stderr=subprocess.STDOUT,
                timeout=900, check=False,
            )
        except subprocess.TimeoutExpired:
            raise PilotError("Independent pinned JSword commentary test timed out") from None
    if logfile.stat().st_size > MAX_PRIVATE_LOG_BYTES:
        raise PilotError("Unbounded private JSword build output")
    receipt = _junit_result(
        jsword / "build/test-results/test" / ("TEST-" + JUNIT + ".xml"),
        exit_code=process.returncode,
    )
    return {
        "jsword_test_count": receipt["tests"],
        "jsword_errors": receipt["errors"],
        "jsword_failures": receipt["failures"],
        "jsword_skipped": receipt["skipped"],
        "pinned_AndBible_JSword_commit": AND_BIBLE_JSWORD_SHA,
        "pinned_AndBible_release": AND_BIBLE_RELEASE,
        "test_log_or_original_prose_uploaded": False,
    }


def audit_pinned_commentary(resource_id: str, *, jsword: Path,
                           native_raw_binary: Path, reader: str = "diatheke") -> dict:
    manifest = load_manifest(resource_id)
    if (manifest["rights"]["status"] != "research_only"
            or manifest["rights"]["owner_approved"] is not False
            or manifest.get("native_raw_corpus_sha256") is None):
        raise PilotError("Original exact commentary requires unapproved SHA-pinned research manifest")
    for name in ("archive_sha256", "stock_conf_sha256", "native_raw_corpus_sha256"):
        if not isinstance(manifest.get(name), str) or not SHA.fullmatch(manifest[name]):
            raise PilotError("Missing reviewed original stock archive, conf or corpus identity")
    if native_raw_binary.is_symlink() or not native_raw_binary.is_file():
        raise PilotError("Independent native SWORD raw checker is required")
    with tempfile.TemporaryDirectory(prefix="commentary-andbible-jsword-private-") as temporary:
        work = Path(temporary)
        archive = work / "original-stock.zip"
        downloaded = fetch(manifest["sword_zip_url"], archive, manifest["provider"])
        if downloaded["sha256"] != manifest["archive_sha256"]:
            raise PilotError("Official SWORD original ZIP differs from pinned original")
        inventory = inspect_archive(
            archive, source_kind="sword", expected_module_id=manifest["module_id"],
            expected_category="commentary",
        )
        conf = inventory["sword_conf"]
        if (conf["driver"] != "zCom" or conf["version"] != manifest["version"]
                or conf["language"] != manifest["language"]
                or (conf["versification"] or "KJV") != "KJV"):
            raise PilotError("Original stock driver, language, version or mapping differs")
        with ZipFile(archive) as original:
            confsha = sha256(original.read(
                "mods.d/" + manifest["module_id"].lower() + ".conf"
            )).hexdigest()
        if confsha != manifest["stock_conf_sha256"]:
            raise PilotError("Original commentary conf no longer matches reviewed digest")
        installed = work / "installed"
        _safe_stock_install(archive, inventory["members"], installed)
        native = _native_content(installed, manifest["module_id"], native_raw_binary)
        if (native["raw_sha256"] != manifest["native_raw_corpus_sha256"]
                or native["count"] != native["K"] + native["I"] + native["U"]
                or native["count"] < 2):
            raise PilotError("Full original native raw commentary corpus is not identical")
        refs, digests = _live_samples(manifest, installed, reader=reader)
        java = _run_pinned_jsword(jsword, installed, work,
                                  manifest["module_id"], refs)
        return {
            "schema_version": 1,
            "status": "pinned_original_zCom_andbible_stable_jsword_engine_samples_pass",
            "resource_id": resource_id,
            "module_id": manifest["module_id"],
            "original_archive_sha256": downloaded["sha256"],
            "original_conf_sha256": confsha,
            "all_original_native_raw_sha256": native["raw_sha256"],
            "all_native_keys_independently_read": native["count"],
            "native_numbered_keys": native["K"],
            "native_intro_keys": native["I"],
            "native_opaque_top_keys": native["U"],
            "real_diatheke_substantial_samples": len(refs),
            "real_diatheke_original_output_sha256": digests,
            **java,
            "original_sword_module_mutated": False,
            "andbible_android_app_installed_or_gui_tested": False,
            "xiphos_commentary_content_gui_verified": False,
            "rights_and_editorial_owner_approved": False,
            "published": False,
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--jsword", type=Path, required=True)
    parser.add_argument("--native-raw-binary", type=Path, required=True)
    parser.add_argument("--reader", default="diatheke")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.report.is_symlink() or args.report.exists() or not args.report.parent.is_dir():
        raise PilotError("Refusing unsafe or existing JSword result path")
    receipt = audit_pinned_commentary(
        args.resource_id, jsword=args.jsword,
        native_raw_binary=args.native_raw_binary, reader=args.reader,
    )
    args.report.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("Exact original SWORD zCom independently decoded with stable AndBible JSword (metadata only; not Android GUI)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
