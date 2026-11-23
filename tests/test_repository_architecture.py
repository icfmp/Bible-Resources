"""Fail-closed repository topology and live-reference maintenance guardrails.

These checks validate the current tracked tree and its active references, not
editorial acceptance or the correctness of original source content.
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = frozenset({
    ".gitignore", "CONTRIBUTING.md", "COPYING", "INSTALLATION_FR.md",
    "README.md", "SECURITY.md", "requirements.txt",
})
ROOT_DIRS = frozenset({
    ".github", "catalog", "config", "docs", "modules",
    "reports", "schemas", "scripts", "sources", "tests",
})
DISPOSABLE = frozenset({
    "work", "history", "examples", "dist", "pilot-inputs",
    "scratch", "tmp", "__pycache__", ".pytest_cache",
})
CATEGORIES = frozenset({
    "bibles", "commentaries", "dictionaries", "encyclopedias", "other",
})
PATH_FIELDS = frozenset({
    "source_decisions", "original_manifest", "notes_path",
    "evidence_path", "editorial_path",
})
SCRIPT_REF = re.compile(
    r"(?<![\w/])scripts/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*"
    r"\.(?:py|cpp|sh)\b"
)
TRIGGER_REF = re.compile(r"""^\s*-\s*['"]?((?:scripts|config)/[^'"\s]+)""")


def tracked_paths(root: Path) -> set[str]:
    output = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root,
        check=True, capture_output=True, timeout=20,
    ).stdout
    return {part.decode("utf-8") for part in output.split(b"\0") if part}


def topology_errors(paths: set[str]) -> list[str]:
    errors = []
    for name in sorted(paths):
        parts = PurePosixPath(name).parts
        if not parts or parts[0] in DISPOSABLE:
            errors.append(f"Retired temporary top-level directory: {name}")
            continue
        if len(parts) == 1:
            if name not in ROOT_FILES:
                errors.append(f"Unreviewed top-level file: {name}")
        elif parts[0] not in ROOT_DIRS:
            errors.append(f"Unreviewed top-level directory: {name}")
        if name.endswith("/.gitkeep") or name == ".gitkeep":
            errors.append(f"Tracked placeholder directory: {name}")
        if parts[0] == "sources" and len(parts) >= 3 and parts[1] in {
                "original", "cleaned"}:
            if parts[-1] == "README.md":
                continue
            if (len(parts) < 5 or parts[2] not in CATEGORIES
                    or not re.fullmatch(r"[a-z]{2,3}", parts[3])
                    or not re.fullmatch(r"[a-z][a-z0-9-]*", parts[4])):
                errors.append(f"Source outside type/language/edition: {name}")
    return errors


def configuration_errors(root: Path, paths: set[str]) -> list[str]:
    errors = []
    for name in sorted(p for p in paths
                       if p.startswith("config/") and p.endswith(".json")):
        path = root / name
        if path.is_symlink():
            errors.append(f"Configuration must not be a symlink: {name}")
            continue
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"Malformed configuration {name}: {exc}")
            continue
        if not isinstance(config, dict):
            errors.append(f"Configuration root must be a JSON object: {name}")
            continue
        for field in PATH_FIELDS & config.keys():
            target = config[field]
            if (not isinstance(target, str)
                    or PurePosixPath(target).is_absolute()
                    or ".." in PurePosixPath(target).parts
                    or target not in paths):
                errors.append(
                    f"Missing or unsafe active configuration reference "
                    f"{name}:{field} -> {target!r}"
                )
    return errors


def workflow_reference_errors(contents: dict[str, str],
                              paths: set[str]) -> list[str]:
    errors = []
    for name, source in sorted(contents.items()):
        for n, line in enumerate(source.splitlines(), 1):
            refs = set(SCRIPT_REF.findall(line))
            trigger = TRIGGER_REF.search(line)
            if trigger:
                refs.add(trigger.group(1))
            for target in sorted(refs):
                # Actions path filters may legitimately be globs.
                if any(character in target for character in "*?[]{}"):
                    continue
                if target not in paths:
                    errors.append(
                        f"Missing active workflow reference "
                        f"{name}:{n} -> {target}"
                    )
    return errors


class RepositoryArchitectureGuardrails(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = tracked_paths(ROOT)

    def test_current_tracked_layout_has_no_unreviewed_roots(self):
        self.assertFalse(topology_errors(self.paths))

    def test_sources_have_edition_owned_cleaned_manifests(self):
        for source in sorted(p for p in self.paths
                             if p.startswith("sources/cleaned/")
                             and p.endswith(".osis.xml")):
            manifest = str(PurePosixPath(source).parent / "CLEANUP_MANIFEST.json")
            with self.subTest(master=source):
                self.assertIn(manifest, self.paths)
        self.assertFalse((ROOT / "work").exists())

    def test_current_configs_have_valid_json_and_existing_active_references(self):
        self.assertFalse(configuration_errors(ROOT, self.paths))

    def test_workflow_paths_reference_tracked_live_inputs(self):
        contents = {
            path: (ROOT / path).read_text(encoding="utf-8")
            for path in self.paths
            if path.startswith(".github/workflows/")
            and path.endswith((".yml", ".yaml"))
        }
        self.assertGreaterEqual(len(contents), 1)
        self.assertFalse(workflow_reference_errors(contents, self.paths))

    def test_reject_regressions_to_retired_roots_and_placeholder_dirs(self):
        cases = (
            {"work/test.md"}, {"history/file.md"},
            {"new-scripts/helper.py"}, {"modules/new/.gitkeep"},
            {"sources/cleaned/commentaries/EN/edition/master.osis.xml"},
        )
        for paths in cases:
            with self.subTest(paths=paths):
                self.assertTrue(topology_errors(paths))

    def test_reject_missing_active_config_and_untracked_workflow_inputs(self):
        with self.subTest("missing config"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                file = root / "config/active.json"
                file.parent.mkdir()
                file.write_text(
                    json.dumps({"source_decisions": "config/missing.json"}),
                    encoding="utf-8",
                )
                errors = configuration_errors(root, {"config/active.json"})
                self.assertEqual(len(errors), 1)
                self.assertIn("Missing or unsafe", errors[0])
                file.write_text("{not json", encoding="utf-8")
                self.assertIn(
                    "Malformed", configuration_errors(
                        root, {"config/active.json"})[0]
                )
        refs = workflow_reference_errors(
            {".github/workflows/sample.yml": (
                "on:\n  pull_request:\n    paths:\n"
                "      - 'config/missing.json'\n"
                "jobs:\n  sample:\n    steps:\n"
                "      - run: python scripts/missing.py\n"
            )},
            {".github/workflows/sample.yml"},
        )
        self.assertEqual(len(refs), 2)
        self.assertFalse(workflow_reference_errors(
            {".github/workflows/sample.yml":
             "paths:\n  - 'config/release-plans/*.json'\n"},
            {".github/workflows/sample.yml"},
        ))

if __name__ == "__main__":
    unittest.main()
