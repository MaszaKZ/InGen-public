from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("verify_w10", ROOT / "verify_w10.py")
assert SPEC and SPEC.loader
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class TrackedArtifactHygieneTests(unittest.TestCase):
    def test_rejects_raw_outputs_and_experiment_archives(self) -> None:
        paths = [
            "week-03/W03_Raw_Model_Outputs.jsonl",
            "week-06-explorations/rerun-v3/Raw_Model_Outputs.jsonl",
            "week-06.7z",
            "exports/experiment-results.tar.gz",
            "week-07/W07_Analysis.json",
            "week-09/figures/result.png",
        ]
        self.assertEqual(
            VERIFY.forbidden_tracked_artifacts(paths),
            [
                "exports/experiment-results.tar.gz",
                "week-03/W03_Raw_Model_Outputs.jsonl",
                "week-06-explorations/rerun-v3/Raw_Model_Outputs.jsonl",
                "week-06.7z",
            ],
        )

    def test_normalizes_windows_separators(self) -> None:
        self.assertEqual(
            VERIFY.forbidden_tracked_artifacts(
                [r"week-06-explorations\archive-v1\W06_Raw_Model_Outputs.jsonl"]
            ),
            ["week-06-explorations/archive-v1/W06_Raw_Model_Outputs.jsonl"],
        )

    def test_rejects_mixed_case_non_ascii_paths_and_all_archive_suffixes(self) -> None:
        self.assertEqual(
            VERIFY.forbidden_tracked_artifacts(
                [
                    "caf\u00e9/MODEL_Raw_Model_Outputs.JSONL",
                    "archives/first.7Z",
                    "archives/second.ZIP",
                    "archives/third.TAR",
                    "archives/fourth.TAR.GZ",
                    "archives/fifth.TGZ",
                ]
            ),
            [
                "archives/fifth.TGZ",
                "archives/first.7Z",
                "archives/fourth.TAR.GZ",
                "archives/second.ZIP",
                "archives/third.TAR",
                "caf\u00e9/MODEL_Raw_Model_Outputs.JSONL",
            ],
        )

    def test_deduplicates_normalized_paths(self) -> None:
        self.assertEqual(
            VERIFY.forbidden_tracked_artifacts(
                [
                    r"café\nested\Raw_Model_Outputs.jsonl",
                    "café/nested/Raw_Model_Outputs.jsonl",
                ]
            ),
            ["caf\u00e9/nested/Raw_Model_Outputs.jsonl"],
        )

    def test_parses_nul_delimited_git_inventory_without_quoting(self) -> None:
        self.assertEqual(
            VERIFY.parse_git_ls_files_output(
                "docs/readme.md\0caf\u00e9/Raw_Model_Outputs.jsonl\0archives/run.ZIP\0"
            ),
            [
                "docs/readme.md",
                "caf\u00e9/Raw_Model_Outputs.jsonl",
                "archives/run.ZIP",
            ],
        )

    def test_package_verifier_rejects_nul_delimited_non_ascii_raw_path(self) -> None:
        tracked = subprocess.run(
            ["git", "-C", str(VERIFY.ROOT), "ls-files", "-z"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        inventory = tracked + "caf\u00e9/Raw_Model_Outputs.jsonl\0"
        VERIFY.failures.clear()
        try:
            with patch.object(VERIFY.subprocess, "run", return_value=SimpleNamespace(stdout=inventory)):
                VERIFY.verify_package()
            self.assertIn(
                "raw model outputs or experiment archives remain tracked: caf\u00e9/Raw_Model_Outputs.jsonl",
                VERIFY.failures,
            )
        finally:
            VERIFY.failures.clear()


if __name__ == "__main__":
    unittest.main()
