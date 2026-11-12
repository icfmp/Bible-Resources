#!/usr/bin/env python3
"""Run an exact AndBible-stable JSword fork against the PRIVATE audited SWORD.

Not an Android UI test. Neither source XML, the resulting binary, individual
Bible verses nor note bodies are copied to published GitHub artifacts.
"""
from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

AND_BIBLE_RELEASE = "production-1117"
AND_BIBLE_JSWORD_SHA = "6ebd10a005fa7761e611c048ececea1430e22546"
JUNIT = "org.icfmp.research.DarbyAndBibleJSwordProbeTest"
MODULE = "JND2024RepairResearch"


class AndBibleJSwordProbeError(ValueError):
    """Untrusted engine revision, missing native data or failing Java test."""


def run_pinned_jsword(jsword: Path, payload: Path, scratch: Path) -> dict:
    repo = jsword.resolve(strict=True)
    module_root = payload.resolve(strict=True)
    if (not repo.is_dir() or jsword.is_symlink() or
            not (repo / "build.gradle.kts").is_file() or
            not (repo / "gradlew").is_file() or
            not (module_root / "mods.d" /
                 "jnd2024repairresearch.conf").is_file() or
            not scratch.is_dir() or scratch.is_symlink() or
            not "private-darby-repaired-sword-" in str(module_root)):
        raise AndBibleJSwordProbeError("Not the fully audited private module or JSword checkout")
    git = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                         capture_output=True, text=True, timeout=12, check=False)
    if git.returncode or git.stdout.strip() != AND_BIBLE_JSWORD_SHA:
        raise AndBibleJSwordProbeError("JSword engine drift from AndBible 5.1.1117")
    upstream_test = (
        Path(__file__).resolve().parents[1]
        / "tests/java/org/icfmp/research/DarbyAndBibleJSwordProbeTest.java"
    )
    if not upstream_test.is_file() or upstream_test.is_symlink():
        raise AndBibleJSwordProbeError("Missing reviewed independent Java integration test")
    target = repo / "src/test/java/org/icfmp/research/DarbyAndBibleJSwordProbeTest.java"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.exists():
        raise AndBibleJSwordProbeError("Refusing to overwrite upstream JSword test")
    shutil.copyfile(upstream_test, target)

    private_home = scratch / "jsword-private-home"
    private_home.mkdir()
    gradle_home = scratch / "jsword-gradle-cache"
    gradle_home.mkdir()
    log = scratch / "jsword-gradle-private.log"
    env = dict(os.environ,
               DARBY_JSWORD_MODULE_ROOT=str(module_root),
               DARBY_JSWORD_PRIVATE_HOME=str(private_home),
               GRADLE_USER_HOME=str(gradle_home),
               JAVA_TOOL_OPTIONS="-Duser.home=" + str(private_home),
               LC_ALL="C.UTF-8",
               LANG="C.UTF-8")
    cmd = [
        "bash", str(repo / "gradlew"), "--no-daemon", "--console=plain",
        "--stacktrace", "test", "--tests", JUNIT
    ]
    with log.open("xb") as output:
        try:
            process = subprocess.run(cmd, cwd=repo, env=env, stdout=output,
                                     stderr=subprocess.STDOUT, timeout=720,
                                     check=False)
        except subprocess.TimeoutExpired as exc:
            raise AndBibleJSwordProbeError("Pinned JSword test exceeded bounded duration") from exc
    if log.stat().st_size > 4 * 1024 * 1024:
        raise AndBibleJSwordProbeError("Unbounded private Java test output")
    results = (repo / "build/test-results/test"
               / ("TEST-" + JUNIT + ".xml"))
    if not results.is_file() or results.is_symlink():
        raise AndBibleJSwordProbeError(
            "AndBible-stable JSword did not produce expected JUnit evidence"
            " (private log retained only inside short-lived runner)")
    try:
        report = ET.parse(results).getroot()
        total = int(report.attrib["tests"])
        failures = int(report.attrib["failures"])
        errors = int(report.attrib["errors"])
        skipped = int(report.attrib.get("skipped", "0"))
    except (ET.ParseError, ValueError, KeyError) as exc:
        raise AndBibleJSwordProbeError("Malformed AndBible JSword JUnit metadata") from exc
    failed_names = [
        x.get("name", "unknown") for x in report.findall("testcase")
        if x.find("failure") is not None or x.find("error") is not None
    ]
    # Test names are our safe authored identifiers; do not print exception
    # details, JUnit stdout, private book data, or source/HTML snippets.
    if process.returncode or total != 5 or failures or errors or skipped:
        print("AndBible JSword safe JUnit categories only:",
              json.dumps({"exit_success": process.returncode == 0,
                          "count": total, "failures": failures, "errors": errors,
                          "skipped": skipped, "failed_test_names": failed_names[:5]},
                         sort_keys=True))
        raise AndBibleJSwordProbeError("Independent stable AndBible JSword gate did not pass")
    return {
        "status": "exact_andbible_5_1_jsword_engine_samples_pass",
        "andbible_release_tag": AND_BIBLE_RELEASE,
        "andbible_jsword_submodule_commit": AND_BIBLE_JSWORD_SHA,
        "java_test_count": total,
        "java_test_failures": failures,
        "java_test_skipped": skipped,
        "actual_private_module_identity": MODULE,
        "actual_module_used_was_native_fidelity_audited": True,
        "android_gui_installed_or_tested": False,
        "full_jsword_note_inventory_checked": False,
        "compiled_module_or_source_uploaded": False,
        "editorial_approval": False,
        "released": False,
    }
