from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest import mock


PACKAGE = Path(__file__).resolve().parent.parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY_MODELS = load_module("verify_models", PACKAGE / "verify_models.py")
VERIFY_PACKAGE = load_module("verify_package", PACKAGE / "verify_package.py")
RUN_ACCEPTANCE = load_module("run_acceptance", PACKAGE / "run_acceptance.py")
SCRATCH = PACKAGE / ".test-tmp"
SCRATCH.mkdir(exist_ok=True)


@contextmanager
def scratch_directory():
    root = SCRATCH / f"case-{uuid.uuid4().hex}"
    root.mkdir()
    try:
        yield root
    finally:
        shutil.rmtree(root)


class ModelCacheTests(unittest.TestCase):
    def build_complete_cache(self, root: Path) -> None:
        lock = VERIFY_MODELS.load_lock()
        for repo_id, record in lock["models"].items():
            snapshot = (
                root
                / VERIFY_MODELS.cache_directory(repo_id)
                / "snapshots"
                / record["revision"]
            )
            snapshot.mkdir(parents=True)
            (snapshot / "config.json").write_text(
                '{"model_type": "fixture"}\n', encoding="utf-8"
            )
            (snapshot / "tokenizer_config.json").write_text(
                "{}\n", encoding="utf-8"
            )
            (snapshot / "tokenizer.json").write_text(
                '{"version": "1.0"}\n', encoding="utf-8"
            )
            shards = (
                "model-00001-of-00002.safetensors",
                "model-00002-of-00002.safetensors",
            )
            (snapshot / "model.safetensors.index.json").write_text(
                json.dumps(
                    {
                        "weight_map": {
                            "fixture.layer_1": shards[0],
                            "fixture.layer_2": shards[1],
                        }
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            for shard in shards:
                (snapshot / shard).write_bytes(b"fixture-weights\n")

    def test_allow_missing_is_explicit_and_structurally_strict(self) -> None:
        with scratch_directory() as root:
            result = VERIFY_MODELS.inspect_cache(root)
            self.assertFalse(VERIFY_MODELS.result_ok(result, allow_missing=False))
            self.assertTrue(VERIFY_MODELS.result_ok(result, allow_missing=True))
            self.assertEqual(len(result["missing"]), 10)

    def test_complete_cache_requires_a_checksum_manifest(self) -> None:
        with scratch_directory() as root:
            self.build_complete_cache(root)
            result = VERIFY_MODELS.inspect_cache(root)
            self.assertFalse(VERIFY_MODELS.result_ok(result, allow_missing=False))
            self.assertEqual(result["checksum_verification"]["status"], "missing")

    def test_checksum_manifest_detects_modified_model_bytes(self) -> None:
        with scratch_directory() as root:
            self.build_complete_cache(root)
            checksum_manifest = root / "model-checksums.json"
            VERIFY_MODELS.write_checksum_manifest(root, checksum_manifest)
            result = VERIFY_MODELS.inspect_cache(
                root, checksum_manifest=checksum_manifest
            )
            self.assertTrue(VERIFY_MODELS.result_ok(result, allow_missing=False))

            lock = VERIFY_MODELS.load_lock()
            repo_id, record = next(iter(lock["models"].items()))
            changed = (
                root
                / VERIFY_MODELS.cache_directory(repo_id)
                / "snapshots"
                / record["revision"]
                / "model-00001-of-00002.safetensors"
            )
            changed.write_bytes(b"modified-fixture-weights\n")
            result = VERIFY_MODELS.inspect_cache(
                root, checksum_manifest=checksum_manifest
            )
            self.assertFalse(VERIFY_MODELS.result_ok(result, allow_missing=False))
            self.assertEqual(result["checksum_verification"]["status"], "mismatch")
            self.assertIn(
                changed.relative_to(root).as_posix(),
                result["checksum_verification"]["mismatches"],
            )

    def test_complete_cache_with_checksums_rejects_unexpected_revision(self) -> None:
        with scratch_directory() as root:
            self.build_complete_cache(root)
            checksum_manifest = root / "model-checksums.json"
            VERIFY_MODELS.write_checksum_manifest(root, checksum_manifest)

            lock = VERIFY_MODELS.load_lock()
            repo_id = next(iter(lock["models"]))
            extra = root / VERIFY_MODELS.cache_directory(repo_id) / "snapshots" / ("f" * 40)
            extra.mkdir()
            (extra / "config.json").write_text("{}\n", encoding="utf-8")
            result = VERIFY_MODELS.inspect_cache(
                root, checksum_manifest=checksum_manifest
            )
            self.assertFalse(VERIFY_MODELS.result_ok(result, allow_missing=True))
            self.assertEqual(result["unexpected_revisions"][0]["revision"], "f" * 40)

    def test_config_only_snapshots_fail_load_completeness(self) -> None:
        with scratch_directory() as root:
            lock = VERIFY_MODELS.load_lock()
            for repo_id, record in lock["models"].items():
                snapshot = (
                    root
                    / VERIFY_MODELS.cache_directory(repo_id)
                    / "snapshots"
                    / record["revision"]
                )
                snapshot.mkdir(parents=True)
                (snapshot / "config.json").write_text("{}\n", encoding="utf-8")

            result = VERIFY_MODELS.inspect_cache(root)
            self.assertFalse(VERIFY_MODELS.result_ok(result, allow_missing=False))
            self.assertEqual(len(result["incomplete_snapshots"]), 10)

    def test_missing_indexed_weight_shard_fails_load_completeness(self) -> None:
        with scratch_directory() as root:
            self.build_complete_cache(root)
            lock = VERIFY_MODELS.load_lock()
            repo_id, record = next(iter(lock["models"].items()))
            snapshot = (
                root
                / VERIFY_MODELS.cache_directory(repo_id)
                / "snapshots"
                / record["revision"]
            )
            (snapshot / "model-00002-of-00002.safetensors").unlink()

            result = VERIFY_MODELS.inspect_cache(root)
            self.assertFalse(VERIFY_MODELS.result_ok(result, allow_missing=False))
            self.assertEqual(result["incomplete_snapshots"][0]["repo_id"], repo_id)
            self.assertIn(
                "model-00002-of-00002.safetensors",
                result["incomplete_snapshots"][0]["problems"],
            )


class PackageTests(unittest.TestCase):
    def test_generated_json_uses_canonical_lf_line_endings(self) -> None:
        for relative in (
            "package_manifest.json",
            "receipts/isolated-cpu-mock.json",
        ):
            payload = (PACKAGE / relative).read_bytes()
            self.assertNotIn(b"\r\n", payload, relative)
            self.assertTrue(payload.endswith(b"\n"), relative)

    def test_manifest_evidence_and_artifacts_verify(self) -> None:
        result = VERIFY_PACKAGE.verify_all()
        self.assertGreater(result["manifest"]["files"], 100)
        self.assertEqual(result["evidence"]["stress"]["plain"], -25.6)
        self.assertEqual(result["artifacts"]["slides"], 10)

    def test_distributed_receipts_are_manifest_pinned(self) -> None:
        paths = {
            entry["path"] for entry in VERIFY_PACKAGE.load_manifest()["files"]
        }
        self.assertIn("receipts/isolated-cpu-mock.json", paths)
        self.assertIn("receipts/isolated-short-inference.json", paths)
        cpu_receipt = json.loads(
            (PACKAGE / "receipts/isolated-cpu-mock.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn("package_manifest_sha256", cpu_receipt)
        self.assertFalse(
            VERIFY_PACKAGE._permitted_untracked("receipts/altered-receipt.json")
        )
        self.assertTrue(
            VERIFY_PACKAGE._permitted_untracked(
                "generated-receipts/cpu-mock-receipt.json"
            )
        )

    def test_acceptance_default_writes_a_generated_receipt(self) -> None:
        with scratch_directory() as root:
            (root / "package_manifest.json").write_text("{}\n", encoding="utf-8")
            package_result = {
                "manifest": {"files": 1, "bytes": 3},
                "artifacts": {"slides": 10},
            }
            model_result = {
                "expected": 10,
                "present": [],
                "missing": [{"repo_id": "fixture", "revision": "0" * 40}],
                "misplaced": [],
                "unexpected_models": [],
                "unexpected_revisions": [],
                "empty_snapshots": [],
                "incomplete_snapshots": [],
                "checksum_verification": {"status": "not_required"},
            }
            with (
                mock.patch.object(RUN_ACCEPTANCE, "PACKAGE", root),
                mock.patch.object(
                    RUN_ACCEPTANCE.verify_package,
                    "verify_all",
                    return_value=package_result,
                ),
                mock.patch.object(
                    RUN_ACCEPTANCE.verify_models,
                    "inspect_cache",
                    return_value=model_result,
                ),
                mock.patch.object(
                    RUN_ACCEPTANCE,
                    "recompute_smoke_counts",
                    return_value={},
                ),
            ):
                self.assertEqual(
                    RUN_ACCEPTANCE.main(["--model-policy", "allow-missing"]), 0
                )
            self.assertTrue(
                (root / "generated-receipts/cpu-mock-receipt.json").is_file()
            )
            self.assertFalse((root / "receipts/cpu-mock-receipt.json").exists())

    def test_top_level_runner_contains_no_download_automation(self) -> None:
        checked = [
            PACKAGE / "verify_models.py",
            PACKAGE / "verify_package.py",
            PACKAGE / "run_acceptance.py",
            PACKAGE / "run_minimal_pipeline_smoke.py",
            PACKAGE / "analysis/regenerate_figures.py",
        ]
        banned = ("snapshot_download", "requests.get", "urlopen(", "prefetch_models")
        for path in checked:
            source = path.read_text(encoding="utf-8")
            for token in banned:
                self.assertNotIn(token, source, f"{token} in {path.name}")

    def test_model_lock_has_exact_immutable_revisions(self) -> None:
        lock = json.loads((PACKAGE / "model_lock.json").read_text(encoding="utf-8"))
        self.assertEqual(len(lock["models"]), 10)
        self.assertTrue(
            all(len(record["revision"]) == 40 for record in lock["models"].values())
        )

    def test_report_source_and_presentation_provenance_are_local(self) -> None:
        report_dir = PACKAGE / "artifacts/report"
        source = (report_dir / "Capstone_Report.tex").read_text(encoding="utf-8")
        for stem in (
            "W11_Figure1_Operating_Point.pdf",
            "W11_Figure2_Prompt_Tradeoffs.pdf",
            "W11_Figure3_Measurement_Stress.pdf",
            "W11_Figure4_Expected_Loss.pdf",
        ):
            self.assertIn(f"figures/{stem}", source)
            self.assertTrue((report_dir / "figures" / stem).is_file())
        self.assertTrue(
            (PACKAGE / "source/presentation/Mid_Review_Template.pptx").is_file()
        )

    def test_packaged_week7_entry_point_resolves_package_model_lock(self) -> None:
        source = PACKAGE / "source"
        completed = subprocess.run(
            [sys.executable, "week-07/run_w07_replication.py", "--help"],
            cwd=source,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_packaged_preflight_lock_accepts_admitted_snapshot(self) -> None:
        source = PACKAGE / "source"
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; "
                    "sys.path.insert(0, 'week-07'); "
                    "import w07_common; "
                    "w07_common.assert_preflight_ready_for_confirmation()"
                ),
            ],
            cwd=source,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_runtime_metadata_records_the_actual_invocation(self) -> None:
        with scratch_directory() as root:
            source = root / "source"
            shutil.copytree(PACKAGE / "source", source)
            shutil.copy2(PACKAGE / "model_lock.json", root / "model_lock.json")
            week7 = source / "week-07"
            completed = subprocess.run(
                [
                    sys.executable,
                    "run_w07_replication.py",
                    "--phase",
                    "smoke",
                    "--models",
                    "qwen",
                    "--batch-size",
                    "1",
                    "--limit",
                    "1",
                ],
                cwd=week7,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            metadata = json.loads(
                (week7 / "W07_Smoke_Run_Metadata.json").read_text(encoding="utf-8")
            )
            command = metadata["commands"][0]
            self.assertNotIn(".conda-w01", command)
            for token in ("--phase smoke", "--models qwen", "--limit 1"):
                self.assertIn(token, command)

    def test_runtime_provenance_rejects_superseded_interpreters(self) -> None:
        verifier = getattr(VERIFY_PACKAGE, "verify_runtime_provenance", None)
        self.assertIsNotNone(verifier)
        result = verifier()
        self.assertEqual(result["active_scripts"], 4)

    def test_runtime_command_preserves_actual_arguments(self) -> None:
        source = PACKAGE / "source"
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; sys.path.insert(0, 'week-07'); "
                    "import w07_common; "
                    "print(w07_common.runtime_command("
                    "['judge_w07_replication.py', '--phase', 'gold', "
                    "'--judges', 'granite8b', '--limit', '1'], "
                    "executable=r'C:\\\\review env\\\\python.exe'))"
                ),
            ],
            cwd=source,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(r'C:\\review env\\python.exe', completed.stdout)
        self.assertIn("--judges granite8b", completed.stdout)
        self.assertIn("--limit 1", completed.stdout)

    def test_short_inference_receipt_is_explicitly_bounded(self) -> None:
        receipt = json.loads(
            (PACKAGE / "receipts/isolated-short-inference.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(receipt["status"], "partial_inference_verified")
        self.assertEqual(receipt["execution"]["generated_rows"], 5)
        self.assertEqual(receipt["execution"]["nonblank_rows"], 5)
        self.assertEqual(receipt["execution"]["hit_token_cap"], 0)
        self.assertEqual(receipt["model"]["remote_checksum_files_verified"], 14)
        self.assertFalse(receipt["model"]["cache_included"])
        for boundary in ("Mistral", "judges", "full confirmation"):
            self.assertIn(boundary, receipt["claim_boundary"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
