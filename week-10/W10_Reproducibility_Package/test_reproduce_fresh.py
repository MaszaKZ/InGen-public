import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import Mock, patch


MODULE_PATH = Path(__file__).with_name("reproduce_fresh.py")
SPEC = importlib.util.spec_from_file_location("reproduce_fresh", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules["reproduce_fresh"] = MODULE
SPEC.loader.exec_module(MODULE)


EXPECTED_FULL_STAGES = (
    "restore_protocol_inputs", "clear_generated_evidence", "week03_generate",
    "week04_generate", "week05_generate", "week05_audit", "week05_notebook",
    "week06_build_bank", "week06_generate", "week06_judge", "week06_test",
    "week06_verify", "week07_generate", "week07_judge", "week07_analyze",
    "week07_notebook_build", "week07_notebook_execute", "week07_report",
    "week08_analyze", "week08_verify", "week09_tables", "week09_figures",
    "week09_verify", "week10_sensitivity", "fresh_run_verify",
)


class FreshGraphTests(unittest.TestCase):
    def test_stage_is_immutable(self):
        stage = MODULE.Stage("x", ("x.py",), "internal")
        with self.assertRaises(FrozenInstanceError):
            stage.name = "changed"

    def test_full_graph_has_exact_order_and_unique_names(self):
        graph = MODULE.full_command_graph()
        self.assertEqual(tuple(stage.name for stage in graph), EXPECTED_FULL_STAGES)
        self.assertEqual(len(graph), len(set(stage.name for stage in graph)))
        self.assertTrue(all(isinstance(stage.argv, tuple) for stage in graph))

    def test_full_graph_uses_fresh_safe_commands(self):
        graph = MODULE.full_command_graph()
        commands = [" ".join(stage.argv) for stage in graph]
        self.assertIn("--model mistral-7b-instruct-v0.3", commands[3])
        for name in ("week07_generate", "week07_judge"):
            stage = next(s for s in graph if s.name == name)
            self.assertIn("--phase", stage.argv)
            self.assertIn("confirmation", stage.argv)
        self.assertFalse(any("regenerate_all.py" in command for command in commands))
        self.assertFalse(any("verify_w10.py" in command for command in commands))
        notebook = next(s for s in graph if s.name == "week07_notebook_execute")
        self.assertEqual(notebook.argv, (
            "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
            "--inplace", "--ExecutePreprocessor.timeout=900",
            "week-07/W07_Analysis_Notebook.ipynb",
        ))
        self.assertTrue(all(not (stage.argv and stage.argv[0].endswith("python")) for stage in graph))

    def test_mock_graph_is_smoke_only_and_has_mock_receipt(self):
        graph = MODULE.mock_command_graph()
        names = tuple(stage.name for stage in graph)
        self.assertEqual(names, (
            "clear_generated_evidence",
            "week03_generate",
            "week04_generate",
            "week05_generate",
            "week05_audit",
            "week06_build_bank",
            "week06_generate",
            "week06_judge",
            "week06_test",
            "week07_generate",
            "mock_receipt_check",
        ))
        self.assertEqual(len(names), len(set(names)))
        commands = [" ".join(stage.argv) for stage in graph]
        self.assertNotIn("restore_protocol_inputs", names)
        self.assertFalse(any("fetch_data.py" in command for command in commands))
        self.assertTrue(any("--mock" in stage.argv for stage in graph if stage.name == "week03_generate"))
        self.assertTrue(any("--mock" in stage.argv for stage in graph if stage.name == "week04_generate"))
        self.assertTrue(any("--mock" in stage.argv for stage in graph if stage.name == "week05_generate"))
        self.assertTrue(any("--smoke" in stage.argv for stage in graph if stage.name in {"week06_generate", "week06_judge", "week06_test"}))
        self.assertFalse(any(stage.name == "week06_verify" for stage in graph))
        self.assertFalse(any("verify_w06_independent.py" in stage.argv for stage in graph))
        w07 = next(stage for stage in graph if stage.name == "week07_generate")
        self.assertEqual(w07.argv, ("week-07/run_w07_replication.py", "--phase", "smoke", "--limit", "1"))
        self.assertFalse(any(name in names for name in ("week07_judge", "week07_analyze")))
        receipt = graph[-1]
        self.assertEqual(receipt.name, "mock_receipt_check")
        self.assertEqual(receipt.category, "internal")
        self.assertIn("mock_only", receipt.argv)


class FreshDestinationSafetyTests(unittest.TestCase):
    def _git_result(self, stdout: str):
        class Result:
            returncode = 0

            def __init__(self, result_stdout: str):
                self.stdout = result_stdout
                self.stderr = ""

        return Result(stdout)

    def _source_root(self, parent: Path) -> Path:
        source_root = parent / "source"
        source_root.mkdir()
        return source_root

    def _write_receipt(
        self,
        run_dir: Path,
        *,
        commit: str,
        mode: str | None = "full",
        status: str = "failed",
    ) -> None:
        (run_dir / ".git").write_text("gitdir: /tmp/worktrees/run\n", encoding="utf-8")
        (run_dir / "run-receipt.json").write_text(
            json.dumps({"source_commit": commit, "mode": mode, "status": status}),
            encoding="utf-8",
        )

    def _worktree_results(self, head: str = "abc123"):
        return (self._git_result("true\n"), self._git_result(f"{head}\n"))

    def test_rejects_repository_root_and_any_source_ancestor(self):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            parent = Path(temporary)
            source_root = self._source_root(parent)

            with self.assertRaises(ValueError):
                MODULE.validate_destination(source_root, source_root, resume=False)
            with self.assertRaises(ValueError):
                MODULE.validate_destination(source_root, parent, resume=False)

    def test_rejects_non_empty_destination_without_resume(self):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            parent = Path(temporary)
            source_root = self._source_root(parent)
            run_dir = parent / "external-run"
            run_dir.mkdir()
            (run_dir / "existing.txt").write_text("preserve me", encoding="utf-8")

            with self.assertRaises(ValueError):
                MODULE.validate_destination(source_root, run_dir, resume=False)

    def test_rejects_empty_destination_when_resuming(self):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            parent = Path(temporary)
            source_root = self._source_root(parent)
            run_dir = parent / "external-run"
            run_dir.mkdir()

            with self.assertRaises(ValueError):
                MODULE.validate_destination(source_root, run_dir, resume=True)

    @patch("subprocess.run")
    @patch.object(MODULE, "source_state", return_value={"source_commit": "abc123", "tracked_changes": False})
    def test_rejects_resume_when_receipt_commit_differs(self, _source_state, run):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            parent = Path(temporary)
            source_root = self._source_root(parent)
            run_dir = parent / "external-run"
            run_dir.mkdir()
            self._write_receipt(run_dir, commit="different")
            run.side_effect = self._worktree_results()

            with self.assertRaises(ValueError):
                MODULE.validate_destination(source_root, run_dir, resume=True, mode="full")

    def test_accepts_new_empty_external_destination(self):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            parent = Path(temporary)
            source_root = self._source_root(parent)
            run_dir = parent / "external-run"

            MODULE.validate_destination(source_root, run_dir, resume=False)

    @patch("subprocess.run")
    @patch.object(MODULE, "source_state", return_value={"source_commit": "abc123", "tracked_changes": False})
    def test_accepts_failed_resume_with_matching_commit(self, _source_state, run):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            parent = Path(temporary)
            source_root = self._source_root(parent)
            run_dir = parent / "external-run"
            run_dir.mkdir()
            self._write_receipt(run_dir, commit="abc123")
            run.side_effect = self._worktree_results()

            MODULE.validate_destination(source_root, run_dir, resume=True, mode="full")

    @patch("subprocess.run")
    @patch.object(MODULE, "source_state", return_value={"source_commit": "abc123", "tracked_changes": False})
    def test_rejects_resume_without_matching_resumable_mode_and_status(self, _source_state, run):
        cases = (
            (None, "failed"),
            ("plan", "failed"),
            ("mock", "failed"),
            ("full", "complete"),
            ("full", "mock_only"),
            ("full", "arbitrary"),
        )
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            parent = Path(temporary)
            source_root = self._source_root(parent)
            for receipt_mode, status in cases:
                with self.subTest(mode=receipt_mode, status=status):
                    run_dir = parent / f"run-{receipt_mode}-{status}"
                    run_dir.mkdir()
                    self._write_receipt(run_dir, commit="abc123", mode=receipt_mode, status=status)
                    with self.assertRaises(ValueError):
                        MODULE.validate_destination(source_root, run_dir, resume=True, mode="full")

    @patch("subprocess.run")
    @patch.object(MODULE, "source_state", return_value={"source_commit": "abc123", "tracked_changes": False})
    def test_rejects_resume_when_git_marker_is_not_matching_worktree(self, _source_state, run):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            parent = Path(temporary)
            source_root = self._source_root(parent)
            run_dir = parent / "external-run"
            run_dir.mkdir()
            self._write_receipt(run_dir, commit="abc123")

            run.side_effect = (self._git_result("false\n"),)
            with self.assertRaises(ValueError):
                MODULE.validate_destination(source_root, run_dir, resume=True, mode="full")

            run.side_effect = self._worktree_results(head="different")
            with self.assertRaises(ValueError):
                MODULE.validate_destination(source_root, run_dir, resume=True, mode="full")

    @patch("subprocess.run")
    def test_source_state_reports_commit_and_tracked_changes(self, run):
        run.side_effect = (self._git_result("abc123\n"), self._git_result("M tracked.py\n"))

        state = MODULE.source_state(Path("source"))

        self.assertEqual(state, {"source_commit": "abc123", "tracked_changes": True})
        self.assertEqual(
            [call.args[0] for call in run.call_args_list],
            [
                ["git", "-C", "source", "rev-parse", "HEAD"],
                ["git", "-C", "source", "status", "--porcelain", "--untracked-files=no"],
            ],
        )
        for invocation in run.call_args_list:
            self.assertEqual(
                {key: invocation.kwargs["env"][key] for key in MODULE.OFFLINE_ENVIRONMENT_KEYS},
                {
                    "HF_HOME": str(Path("source") / ".hf-cache"),
                    "HF_HUB_CACHE": str(Path("source") / ".hf-cache" / "hub"),
                    "HF_HUB_OFFLINE": "1",
                    "TRANSFORMERS_OFFLINE": "1",
                    "PYTHONHASHSEED": "0",
                },
            )

    @patch("subprocess.run")
    def test_source_state_rejects_tracked_changes_for_full_and_mock_but_reports_plan(self, run):
        dirty_state = (self._git_result("abc123\n"), self._git_result("M tracked.py\n"))
        run.side_effect = dirty_state * 3

        with self.assertRaises(ValueError):
            MODULE.source_state(Path("source"), mode="full")
        with self.assertRaises(ValueError):
            MODULE.source_state(Path("source"), mode="mock")
        self.assertEqual(
            MODULE.source_state(Path("source"), mode="plan"),
            {"source_commit": "abc123", "tracked_changes": True},
        )

    @patch("subprocess.run")
    def test_create_worktree_detaches_at_commit_then_records_incomplete_identity(self, run):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            parent = Path(temporary)
            source_root = self._source_root(parent)
            run_dir = parent / "external-run"

            def add_detached_worktree(*_args, **_kwargs):
                run_dir.mkdir()
                (run_dir / ".git").write_text("gitdir: /tmp/worktrees/run\n", encoding="utf-8")
                return self._git_result("")

            run.side_effect = add_detached_worktree

            MODULE.create_worktree(source_root, run_dir, "abc123", mode="mock")

            self.assertEqual(
                run.call_args.args[0],
                ["git", "-C", str(source_root), "worktree", "add", "--detach", str(run_dir), "abc123"],
            )
            receipt = json.loads((run_dir / "run-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["source_commit"], "abc123")
            self.assertEqual(receipt["mode"], "mock")
            self.assertEqual(receipt["status"], "incomplete")
            self.assertEqual(
                {key: run.call_args.kwargs["env"][key] for key in MODULE.OFFLINE_ENVIRONMENT_KEYS},
                {
                    "HF_HOME": str(run_dir / ".hf-cache"),
                    "HF_HUB_CACHE": str(run_dir / ".hf-cache" / "hub"),
                    "HF_HUB_OFFLINE": "1",
                    "TRANSFORMERS_OFFLINE": "1",
                    "PYTHONHASHSEED": "0",
                },
            )

    @patch("subprocess.run")
    @patch.object(MODULE, "source_state", return_value={"source_commit": "abc123", "tracked_changes": False})
    def test_resume_git_identity_checks_use_the_run_scoped_offline_environment(self, _source_state, run):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            parent = Path(temporary)
            source_root = self._source_root(parent)
            run_dir = parent / "external-run"
            run_dir.mkdir()
            self._write_receipt(run_dir, commit="abc123")
            run.side_effect = self._worktree_results()

            MODULE.validate_destination(source_root, run_dir, resume=True, mode="full")

            for invocation in run.call_args_list:
                self.assertEqual(
                    {key: invocation.kwargs["env"][key] for key in MODULE.OFFLINE_ENVIRONMENT_KEYS},
                    {
                        "HF_HOME": str(run_dir / ".hf-cache"),
                        "HF_HUB_CACHE": str(run_dir / ".hf-cache" / "hub"),
                        "HF_HUB_OFFLINE": "1",
                        "TRANSFORMERS_OFFLINE": "1",
                        "PYTHONHASHSEED": "0",
                    },
                )


class FreshEnvironmentTests(unittest.TestCase):
    def _completed_process(self, stdout: str = ""):
        class Result:
            returncode = 0

            def __init__(self, result_stdout: str):
                self.stdout = result_stdout
                self.stderr = ""

        return Result(stdout)

    @patch("subprocess.run")
    def test_create_environment_installs_locked_layers_in_required_order(self, run):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            worktree = Path(temporary)

            python = MODULE.create_environment(worktree)

            venv_dir = worktree / ".fresh-venv"
            expected_python = (
                venv_dir / "Scripts" / "python.exe"
                if os.name == "nt"
                else venv_dir / "bin" / "python"
            )
            package_dir = MODULE_PATH.parent
            self.assertEqual(python, expected_python)
            self.assertEqual(
                [item.args[0] for item in run.call_args_list],
                [
                    [sys.executable, "-m", "venv", str(venv_dir)],
                    [str(expected_python), "-m", "pip", "install", "--upgrade", "pip"],
                    [str(expected_python), "-m", "pip", "install", "-r", str(package_dir / "requirements-analysis.txt")],
                    [
                        str(expected_python), "-m", "pip", "install", "torch==2.11.0",
                        "--index-url", "https://download.pytorch.org/whl/cu128",
                    ],
                    [
                        str(expected_python), "-m", "pip", "install", "-r", str(package_dir / "requirements-inference.txt"),
                        "--extra-index-url", "https://download.pytorch.org/whl/cu128",
                    ],
                ],
            )
            for item in run.call_args_list:
                self.assertTrue(item.kwargs["check"])
                self.assertEqual(item.kwargs["cwd"], str(worktree))
                self.assertEqual(
                    {key: item.kwargs["env"][key] for key in MODULE.OFFLINE_ENVIRONMENT_KEYS},
                    {
                        "HF_HOME": str(worktree / ".hf-cache"),
                        "HF_HUB_CACHE": str(worktree / ".hf-cache" / "hub"),
                        "HF_HUB_OFFLINE": "1",
                        "TRANSFORMERS_OFFLINE": "1",
                        "PYTHONHASHSEED": "0",
                    },
                )

    @patch.object(MODULE.shutil, "disk_usage")
    @patch("subprocess.run")
    def test_preflight_records_python_packages_and_cuda_facts_for_receipt(self, run, disk_usage):
        class DiskUsage:
            free = 80 * 1024**3

        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            worktree = Path(temporary)
            python = worktree / ".fresh-venv/python"
            cache_dir = worktree / ".hf-cache"
            original_receipt = {
                "source_commit": "abc123",
                "mode": "full",
                "status": "incomplete",
                "stages": [{"name": "setup", "status": "passed"}],
                "future_field": {"retain": True},
            }
            (worktree / "run-receipt.json").write_text(json.dumps(original_receipt), encoding="utf-8")
            disk_usage.return_value = DiskUsage()
            run.return_value = self._completed_process(json.dumps({
                "python_version": "3.11.15",
                "packages": {"torch": "2.11.0", "transformers": "5.12.0", "huggingface_hub": "1.19.0"},
                "cuda_available": True,
                "cuda_device_name": "Test CUDA GPU",
            }))

            receipt = MODULE.preflight_full(worktree, python, cache_dir)

            self.assertEqual(receipt["python_version"], "3.11.15")
            self.assertEqual(receipt["free_bytes"], 80 * 1024**3)
            self.assertEqual(receipt["packages"]["torch"], "2.11.0")
            self.assertEqual(receipt["gpu"], {"cuda_available": True, "device_name": "Test CUDA GPU"})
            persisted = json.loads((worktree / "run-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(persisted["preflight"], receipt)
            self.assertEqual(persisted["source_commit"], original_receipt["source_commit"])
            self.assertEqual(persisted["mode"], original_receipt["mode"])
            self.assertEqual(persisted["status"], original_receipt["status"])
            self.assertEqual(persisted["stages"], original_receipt["stages"])
            self.assertEqual(persisted["future_field"], original_receipt["future_field"])
            self.assertEqual(run.call_args.args[0][:2], [str(python), "-c"])
            self.assertEqual(
                {key: run.call_args.kwargs["env"][key] for key in MODULE.OFFLINE_ENVIRONMENT_KEYS},
                {
                    "HF_HOME": str(worktree / ".hf-cache"),
                    "HF_HUB_CACHE": str(worktree / ".hf-cache" / "hub"),
                    "HF_HUB_OFFLINE": "1",
                    "TRANSFORMERS_OFFLINE": "1",
                    "PYTHONHASHSEED": "0",
                },
            )

    @patch.object(MODULE.shutil, "disk_usage")
    @patch("subprocess.run")
    def test_preflight_rejects_missing_or_invalid_receipt(self, run, disk_usage):
        class DiskUsage:
            free = 80 * 1024**3

        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            worktree = Path(temporary)
            python = worktree / ".fresh-venv/python"
            cache_dir = worktree / ".hf-cache"
            disk_usage.return_value = DiskUsage()
            run.return_value = self._completed_process(json.dumps({
                "python_version": "3.11.15",
                "packages": {"torch": "2.11.0"},
                "cuda_available": True,
                "cuda_device_name": "Test CUDA GPU",
            }))

            with self.assertRaisesRegex(RuntimeError, "valid run receipt"):
                MODULE.preflight_full(worktree, python, cache_dir)
            (worktree / "run-receipt.json").write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "valid run receipt"):
                MODULE.preflight_full(worktree, python, cache_dir)

    @patch.object(MODULE.shutil, "disk_usage")
    @patch("subprocess.run")
    def test_preflight_rejects_wrong_python_low_space_and_missing_cuda(self, run, disk_usage):
        class DiskUsage:
            free = 80 * 1024**3

        worktree = Path("fresh-run")
        python = Path("fresh-run/.fresh-venv/python")
        cache_dir = worktree / ".hf-cache"
        disk_usage.return_value = DiskUsage()

        cases = (
            ("3.12.0", 80 * 1024**3, True, "Test CUDA GPU"),
            ("3.11.15", (80 * 1024**3) - 1, True, "Test CUDA GPU"),
            ("3.11.15", 80 * 1024**3, False, "Test CUDA GPU"),
            ("3.11.15", 80 * 1024**3, True, ""),
        )
        for version, free, available, name in cases:
            with self.subTest(version=version, free=free, available=available, name=name):
                disk_usage.return_value.free = free
                run.return_value = self._completed_process(json.dumps({
                    "python_version": version,
                    "packages": {"torch": "2.11.0"},
                    "cuda_available": available,
                    "cuda_device_name": name,
                }))
                with self.assertRaises(RuntimeError):
                    MODULE.preflight_full(worktree, python, cache_dir)


class FreshExecutionTests(unittest.TestCase):
    """Behavioral tests for receipt-backed stage execution.

    These tests intentionally mock only subprocesses: receipt, log, and resume
    state transitions remain real filesystem behavior.
    """

    def _context(self, root: Path, mode: str = "mock"):
        receipt_path = root / "run-receipt.json"
        MODULE.write_receipt(receipt_path, {
            "source_commit": "abc123",
            "mode": mode,
            "status": "incomplete",
            "stages": [],
        })
        return MODULE.RunContext(
            source_root=Path("source"),
            worktree=root,
            python=Path("run-python"),
            receipt_path=receipt_path,
            bundle=None,
            mode=mode,
            env=MODULE.offline_environment(root),
        )

    def _popen_result(self, returncode: int, stdout: str = "", stderr: str = ""):
        class Result:
            def __init__(self):
                self.args = []
                self.stdout = io.StringIO(stdout)
                self.stderr = io.StringIO(stderr)

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def communicate(self, *_args, **_kwargs):
                return self.stdout.read(), self.stderr.read()

            def poll(self):
                return returncode

            def kill(self):
                return None

            def wait(self, *_args, **_kwargs):
                return returncode

        return Result()

    @patch("subprocess.Popen")
    @patch("subprocess.run")
    def test_prefetch_uses_the_offline_children_hub_cache(self, run, popen):
        # Mutation caught: prefetching into HF_HOME instead of HF_HUB_CACHE leaves offline children cache-cold.
        run.return_value = subprocess.CompletedProcess([], 0, "", "")
        popen.return_value = self._popen_result(0)
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            context = self._context(Path(temporary), mode="full")

            MODULE._prefetch_models(context)
            MODULE.run_stage(
                MODULE.Stage("week03_generate", ("week-03/run_w03_baseline.py",), "command"),
                context,
            )

        offline_hub_cache = context.env["HF_HUB_CACHE"]
        self.assertEqual(run.call_args.args[0][-1], offline_hub_cache)
        self.assertEqual(run.call_args.kwargs["env"]["HF_HUB_CACHE"], offline_hub_cache)
        self.assertNotIn("HF_HUB_OFFLINE", run.call_args.kwargs["env"])
        self.assertNotIn("TRANSFORMERS_OFFLINE", run.call_args.kwargs["env"])
        self.assertEqual(popen.call_args.kwargs["env"]["HF_HUB_CACHE"], offline_hub_cache)
        self.assertEqual(popen.call_args.kwargs["env"]["HF_HUB_OFFLINE"], "1")
        self.assertEqual(popen.call_args.kwargs["env"]["TRANSFORMERS_OFFLINE"], "1")

    @patch("subprocess.Popen")
    def test_failed_stage_stops_graph_and_records_complete_stage_fields(self, popen):
        # Mutation caught: continuing after a failed stage would contaminate evidence.
        popen.side_effect = (
            self._popen_result(0, "one output"),
            self._popen_result(0, "two output"),
            self._popen_result(9, stderr="failure output"),
        )
        graph = (
            MODULE.Stage("one", ("one.py",), "command"),
            MODULE.Stage("two", ("two.py",), "command"),
            MODULE.Stage("three", ("three.py",), "command"),
            MODULE.Stage("must_not_run", ("later.py",), "command"),
        )
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            result = MODULE.execute_stages(graph, self._context(root))
            receipt = json.loads((root / "run-receipt.json").read_text(encoding="utf-8"))

            self.assertEqual(result, 9)
            self.assertEqual(receipt["status"], "failed")
            self.assertEqual(receipt["failed_stage"], "three")
            self.assertEqual([entry["name"] for entry in receipt["stages"]], ["one", "two", "three"])
            self.assertEqual(len(popen.call_args_list), 3)
            for entry, expected_argv, expected_returncode, expected_status in zip(
                receipt["stages"],
                (("run-python", "one.py"), ("run-python", "two.py"), ("run-python", "three.py")),
                (0, 0, 9),
                ("passed", "passed", "failed"),
            ):
                self.assertEqual(entry["argv"], list(expected_argv))
                self.assertEqual(entry["returncode"], expected_returncode)
                self.assertEqual(entry["status"], expected_status)
                self.assertIn("started_utc", entry)
                self.assertIn("completed_utc", entry)
                self.assertIsInstance(entry["duration_seconds"], float)

    @patch("subprocess.Popen")
    def test_complete_mock_graph_is_offline_and_reaches_mock_only(self, popen):
        # Mutations caught: adding protocol restoration or the full W6 verifier
        # makes a detached smoke run depend on external or unsuffixed evidence.
        def controlled_process(argv, *_args, **_kwargs):
            forbidden = {
                "week-10/W10_Reproducibility_Package/fetch_data.py",
                "week-06/verify_w06_independent.py",
            }
            return self._popen_result(7 if forbidden.intersection(argv) else 0)

        popen.side_effect = controlled_process
        graph = MODULE.mock_command_graph()
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            context = self._context(root)

            result = MODULE.execute_stages(graph, context)
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))

            self.assertEqual(result, 0)
            self.assertEqual(receipt["status"], "mock_only")
            self.assertEqual(
                [entry["name"] for entry in receipt["stages"]],
                [stage.name for stage in graph],
            )
            executed = [call.args[0] for call in popen.call_args_list]
            self.assertNotIn("protocol_restore", receipt)
            self.assertNotIn("protocol_inputs", receipt)
            self.assertFalse(any("fetch_data.py" in argv for argv in executed))
            self.assertFalse(any("week-06/verify_w06_independent.py" in argv for argv in executed))

    @patch("subprocess.Popen")
    def test_resume_skips_passed_stages_and_retries_failed_stage(self, popen):
        # Mutation caught: re-running a passed generation would overwrite fresh evidence.
        popen.side_effect = (
            self._popen_result(0),
            self._popen_result(0),
        )
        graph = (
            MODULE.Stage("one", ("one.py",), "command"),
            MODULE.Stage("two", ("two.py",), "command"),
            MODULE.Stage("three", ("three.py",), "command"),
        )
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            context = self._context(root)
            prior_log = root / "logs/01-one.log"
            prior_log.parent.mkdir(parents=True, exist_ok=True)
            prior_log.write_text("one output\n", encoding="utf-8")
            MODULE.write_receipt(context.receipt_path, {
                "source_commit": "abc123",
                "mode": "mock",
                "status": "failed",
                "failed_stage": "two",
                "stages": [
                    {
                        "name": "one", "argv": ["run-python", "one.py"],
                        "started_utc": "2026-08-14T12:00:00Z",
                        "completed_utc": "2026-08-14T12:00:01Z",
                        "duration_seconds": 1.0, "returncode": 0,
                        "status": "passed", "log_path": "logs/01-one.log",
                    },
                    {"name": "two", "status": "failed"},
                ],
            })

            result = MODULE.execute_stages(graph, context, resume=True)
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))

            self.assertEqual(result, 0)
            self.assertEqual(receipt["status"], "mock_only")
            self.assertEqual([call.args[0] for call in popen.call_args_list], [
                ["run-python", "two.py"], ["run-python", "three.py"],
            ])
            self.assertEqual([entry["name"] for entry in receipt["stages"]], ["one", "two", "two", "three"])

    def test_protocol_clear_only_removes_four_regenerable_outputs(self):
        # Mutation caught: deleting either locked calibration input breaks the protocol.
        generated = (
            "week-06/W06_Raw_Model_Outputs.jsonl",
            "week-06/W06_Judge_Ratings.csv",
            "week-07/W07_Raw_Model_Outputs.jsonl",
            "week-07/W07_Judge_Ratings.csv",
        )
        retained = (
            "week-07/W07_Preflight_Raw_Model_Outputs.jsonl",
            "week-07/W07_Judge_Gold_Ratings.csv",
        )
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            context = self._context(root)
            for relative in generated + retained:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(relative, encoding="utf-8")

            result = MODULE.run_stage(
                MODULE.Stage("clear_generated_evidence", ("clear_generated_evidence",), "internal"),
                context,
            )

            self.assertEqual(result.status, "passed")
            self.assertTrue(all(not (root / relative).exists() for relative in generated))
            self.assertTrue(all((root / relative).exists() for relative in retained))
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["deleted_generated_evidence"], list(generated))


class FreshCliContractTests(unittest.TestCase):
    def test_destination_allows_only_the_reserved_in_repository_run_subtree(self):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            source = Path(temporary) / "source"
            source.mkdir()
            MODULE.validate_destination(source, source / ".reproduction-runs" / "run-001", resume=False)
            with self.assertRaises(ValueError):
                MODULE.validate_destination(source, source / "week-07" / "run-001", resume=False)
            with self.assertRaises(ValueError):
                MODULE.validate_destination(source, source / ".reproduction-runs", resume=False)
            with self.assertRaises(ValueError):
                MODULE.validate_destination(source, source.parent, resume=False)

    @patch.object(MODULE, "create_worktree")
    def test_full_cost_guard_precedes_worktree_creation(self, create_worktree):
        exit_code = MODULE.main(["--mode", "full"])
        self.assertNotEqual(exit_code, 0)
        create_worktree.assert_not_called()

    @patch.object(MODULE, "create_worktree")
    def test_invalid_confirmation_batch_sizes_precede_worktree_creation(self, create_worktree):
        for batch_size in (0, -1, 7):
            with self.subTest(batch_size=batch_size):
                self.assertNotEqual(
                    MODULE.main(["--mode", "full", "--accept-compute-cost", "--bundle", "local.zip",
                                 "--batch-size", str(batch_size)]),
                    0,
                )
        create_worktree.assert_not_called()

    @patch.object(MODULE, "create_worktree")
    def test_full_local_bundle_guard_precedes_worktree_creation(self, create_worktree):
        exit_code = MODULE.main(["--mode", "full", "--accept-compute-cost"])
        self.assertNotEqual(exit_code, 0)
        create_worktree.assert_not_called()

    @patch.object(MODULE, "source_state", return_value={"source_commit": "abc123", "tracked_changes": False})
    def test_plan_mode_performs_no_filesystem_writes(self, _source_state):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            run_dir = Path(temporary) / "planned-run"
            self.assertEqual(MODULE.main(["--mode", "plan", "--run-dir", str(run_dir)]), 0)
            self.assertFalse(run_dir.exists())


class FreshReviewRegressionTests(unittest.TestCase):
    def _context(self, root: Path, *, mode: str = "mock", bundle: Path | None = None):
        receipt_path = root / "run-receipt.json"
        MODULE.write_receipt(receipt_path, {
            "source_commit": "abc123",
            "mode": mode,
            "status": "incomplete",
            "stages": [],
        })
        return MODULE.RunContext(
            source_root=Path("source"), worktree=root, python=Path("run-python"),
            receipt_path=receipt_path, bundle=bundle, mode=mode,
            env=MODULE.offline_environment(root),
        )

    def _popen_result(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        class Result:
            def __init__(self):
                self.args = []
                self.stdout = io.StringIO(stdout)
                self.stderr = io.StringIO(stderr)

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def communicate(self, *_args, **_kwargs):
                return self.stdout.read(), self.stderr.read()

            def poll(self):
                return returncode

            def kill(self):
                return None

            def wait(self, *_args, **_kwargs):
                return returncode

        return Result()

    def _passed_entry(self, root: Path, stage: MODULE.Stage, index: int, argv: list[str] | None = None):
        relative_log = f"logs/{index:02d}-{stage.name}.log"
        log_path = root / relative_log
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("prior output\n", encoding="utf-8")
        return {
            "name": stage.name,
            "argv": argv if argv is not None else ["run-python", *stage.argv],
            "started_utc": "2026-08-14T12:00:00Z",
            "completed_utc": "2026-08-14T12:00:01Z",
            "duration_seconds": 1.0,
            "returncode": 0,
            "status": "passed",
            "log_path": relative_log,
        }

    def _result(self, stage: MODULE.Stage, root: Path, index: int):
        return MODULE.StageResult(
            stage.name, ("run-python", *stage.argv), "2026-08-14T12:00:00Z",
            "2026-08-14T12:00:01Z", 1.0, 0, "passed",
            f"logs/{index:02d}-{stage.name}.log",
        )

    @patch.object(MODULE, "_run_fresh_verifier")
    def test_full_execution_preserves_verifier_completion_and_records_verifier_stage(self, run_verifier):
        # Mutation caught: final receipt handling must not overwrite a verifier-complete full run.
        def complete(context):
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))
            receipt["status"] = "complete"
            receipt["verification_pending"] = False
            MODULE.write_receipt(context.receipt_path, receipt)

        run_verifier.side_effect = complete
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            context = self._context(root, mode="full")
            exit_code = MODULE.execute_stages((MODULE.Stage("fresh_run_verify", ("fresh_run_verify",), "internal"),), context)
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))

            self.assertEqual(exit_code, 0)
            run_verifier.assert_called_once_with(context)
            self.assertEqual(receipt["status"], "complete")
            self.assertFalse(receipt["verification_pending"])
            self.assertEqual(receipt["stages"][-1]["name"], "fresh_run_verify")
            self.assertEqual(receipt["stages"][-1]["status"], "passed")

    @patch.object(MODULE, "_run_fresh_verifier", side_effect=OSError("verification storage failed"))
    def test_verifier_exception_is_incomplete_pending_and_clears_completion_evidence(self, _run_verifier):
        # Mutation caught: a verifier exception must not leave a completed receipt or stale completion evidence.
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            context = self._context(root, mode="full")
            (root / "fresh-verification.json").write_text('{"status":"complete"}', encoding="utf-8")
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))
            receipt.update({"status": "complete", "verification_pending": False})
            MODULE.write_receipt(context.receipt_path, receipt)

            exit_code = MODULE.execute_stages(
                (MODULE.Stage("fresh_run_verify", ("fresh_run_verify",), "internal"),), context,
            )
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))

            self.assertEqual(exit_code, 1)
            self.assertEqual(receipt["status"], "incomplete")
            self.assertTrue(receipt["verification_pending"])
            self.assertFalse((root / "fresh-verification.json").exists())

    def test_batch_size_rewrites_both_week7_confirmation_commands(self):
        # Mutation caught: judging with a different batch size than generation changes the recorded protocol.
        graph = MODULE._graph_with_batch_size(MODULE.full_command_graph(), 12)
        generate = next(stage for stage in graph if stage.name == "week07_generate")
        judge = next(stage for stage in graph if stage.name == "week07_judge")
        self.assertEqual(generate.argv, (
            "week-07/run_w07_replication.py", "--phase", "confirmation", "--batch-size", "12",
        ))
        self.assertEqual(judge.argv, (
            "week-07/judge_w07_replication.py", "--phase", "confirmation", "--batch-size", "12",
        ))

    @patch.object(MODULE, "run_stage")
    def test_resume_reexecutes_tampered_or_noncontiguous_receipt_entries(self, run_stage):
        # Mutation caught: name-only resume could skip evidence whose command or ordering was forged.
        graph = (
            MODULE.Stage("alpha", ("alpha.py",), "command"),
            MODULE.Stage("beta", ("beta.py",), "command"),
            MODULE.Stage("gamma", ("gamma.py",), "command"),
        )
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            context = self._context(root)
            bad_beta = self._passed_entry(root, graph[1], 2, ["run-python", "forged.py"])
            noncontiguous_gamma = self._passed_entry(root, graph[2], 3)
            MODULE.write_receipt(context.receipt_path, {
                "source_commit": "abc123", "mode": "mock", "status": "failed",
                "stages": [self._passed_entry(root, graph[0], 1), bad_beta, noncontiguous_gamma],
            })
            run_stage.side_effect = lambda stage, _context: self._result(stage, root, graph.index(stage) + 1)

            self.assertEqual(MODULE.execute_stages(graph, context, resume=True), 0)

            self.assertEqual([call.args[0].name for call in run_stage.call_args_list], ["beta", "gamma"])

    @patch.object(MODULE, "run_stage")
    def test_resume_accepts_later_valid_pass_after_a_failed_attempt(self, run_stage):
        graph = (
            MODULE.Stage("alpha", ("alpha.py",), "command"),
            MODULE.Stage("beta", ("beta.py",), "command"),
            MODULE.Stage("gamma", ("gamma.py",), "command"),
        )
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            context = self._context(root)
            failed_beta = {"name": "beta", "status": "failed", "returncode": 9}
            MODULE.write_receipt(context.receipt_path, {
                "source_commit": "abc123", "mode": "mock", "status": "failed",
                "stages": [
                    self._passed_entry(root, graph[0], 1), failed_beta,
                    self._passed_entry(root, graph[1], 2),
                ],
            })
            run_stage.side_effect = lambda stage, _context: self._result(stage, root, graph.index(stage) + 1)

            self.assertEqual(MODULE.execute_stages(graph, context, resume=True), 0)

            self.assertEqual([call.args[0].name for call in run_stage.call_args_list], ["gamma"])

    def test_stage_streams_output_before_a_real_child_finishes_and_logs_it(self):
        # Mutation caught: buffering until child completion hides progress on long inference stages.
        class Sink(io.StringIO):
            def __init__(self):
                super().__init__()
                self.ready = threading.Event()

            def write(self, value):
                written = super().write(value)
                if value.strip() == "ready-now":
                    self.ready.set()
                return written

        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            context = self._context(root)
            context = MODULE.replace(context, python=Path(sys.executable))
            stage = MODULE.Stage(
                "stream", ("-c", "import time; print('ready-now', flush=True); time.sleep(0.5)"), "command",
            )
            sink = Sink()
            result_box = []
            with patch.object(MODULE.sys, "stdout", sink):
                started = time.monotonic()
                worker = threading.Thread(target=lambda: result_box.append(MODULE.run_stage(stage, context)))
                worker.start()
                self.assertTrue(sink.ready.wait(0.25))
                self.assertTrue(worker.is_alive())
                worker.join(3)

            self.assertEqual(result_box[0].returncode, 0)
            self.assertIn("ready-now", (root / result_box[0].log_path).read_text(encoding="utf-8"))

    @patch("subprocess.Popen")
    def test_streaming_runner_closes_child_pipe_handles(self, popen):
        # Mutation caught: leaked pipe handles accumulate during a long stage graph.
        process = self._popen_result(stdout="line\n")
        process.stdout.close = Mock(wraps=process.stdout.close)
        process.stderr.close = Mock(wraps=process.stderr.close)
        popen.return_value = process
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            context = self._context(Path(temporary))
            MODULE.run_stage(MODULE.Stage("pipes", ("pipes.py",), "command"), context)

        process.stdout.close.assert_called_once_with()
        process.stderr.close.assert_called_once_with()

    @patch("subprocess.Popen")
    @patch("subprocess.run")
    def test_protocol_restore_records_local_bundle_without_network_authorization(self, run, popen):
        # Mutation caught: public restoration must remain local-only and auditable.
        run.return_value = subprocess.CompletedProcess(["run-python"], 0, "", "")
        popen.side_effect = lambda *_args, **_kwargs: self._popen_result()
        bundle = Path("local-evidence.zip")
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            for relative in MODULE.PROTOCOL_INPUTS:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(relative, encoding="utf-8")
            context = self._context(root, bundle=bundle)
            result = MODULE.run_stage(
                MODULE.Stage("restore_protocol_inputs", ("ignored",), "internal"), context,
            )
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))

            self.assertEqual(result.returncode, 0)
            self.assertEqual(receipt["protocol_restore"]["mode"], "local_bundle")
            self.assertFalse(receipt["protocol_restore"]["network_authorized"])
            expected_argv = (
                "run-python", "week-10/W10_Reproducibility_Package/fetch_data.py",
                "--from-path", str(bundle.resolve()),
            )
            self.assertEqual(result.argv, expected_argv)
            self.assertEqual(
                {key: popen.call_args.kwargs["env"][key] for key in MODULE.OFFLINE_ENVIRONMENT_KEYS},
                {key: context.env[key] for key in MODULE.OFFLINE_ENVIRONMENT_KEYS},
            )

    @patch("subprocess.run")
    def test_plan_git_reads_disable_optional_locks(self, run):
        run.side_effect = (
            subprocess.CompletedProcess([], 0, "abc123\n", ""),
            subprocess.CompletedProcess([], 0, "", ""),
        )
        MODULE.source_state(Path("source"), mode="plan")
        self.assertTrue(all(call.kwargs["env"]["GIT_OPTIONAL_LOCKS"] == "0" for call in run.call_args_list))

    @patch.object(MODULE, "source_state", return_value={"source_commit": "abc123", "tracked_changes": False})
    def test_default_plan_prints_batched_full_graph_requirements_without_writes(self, _source_state):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            run_dir = Path(temporary) / "planned-run"
            output = io.StringIO()
            with patch.object(MODULE.sys, "stdout", output):
                self.assertEqual(MODULE.main(["--mode", "plan", "--run-dir", str(run_dir), "--batch-size", "12"]), 0)
            plan = json.loads(output.getvalue())

            self.assertEqual(len(plan["stages"]), 25)
            self.assertEqual(plan["source_state"]["source_commit"], "abc123")
            self.assertIn("CUDA", plan["full_run_requirements"])
            self.assertEqual(
                next(stage["argv"] for stage in plan["stages"] if stage["name"] == "week07_judge"),
                ["week-07/judge_w07_replication.py", "--phase", "confirmation", "--batch-size", "12"],
            )
            self.assertFalse(run_dir.exists())

    @patch.object(MODULE, "create_environment", side_effect=RuntimeError("bootstrap failed"))
    @patch.object(MODULE, "source_state", return_value={"source_commit": "abc123", "tracked_changes": False})
    def test_setup_exception_marks_existing_receipt_failed(self, _source_state, _create_environment):
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            run_dir = root / "run"

            def create(_source, destination, commit, *, mode):
                destination.mkdir()
                MODULE.write_receipt(destination / "run-receipt.json", {
                    "source_commit": commit, "mode": mode, "status": "incomplete", "stages": [],
                })

            with patch.object(MODULE, "SOURCE_ROOT", source), patch.object(MODULE, "create_worktree", side_effect=create):
                self.assertEqual(MODULE.main([
                    "--mode", "full", "--accept-compute-cost", "--bundle", "local.zip",
                    "--run-dir", str(run_dir),
                ]), 1)
            receipt = json.loads((run_dir / "run-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "failed")
            self.assertEqual(receipt["failed_stage"], "setup")

    @patch("subprocess.Popen")
    def test_interrupt_terminates_and_reaps_child_before_incomplete_receipt(self, popen):
        # Mutation caught: Ctrl+C must not block on readers while the child still owns pipes.
        class Process:
            def __init__(self):
                self.stdout = io.StringIO()
                self.stderr = io.StringIO()
                self.terminate = Mock()
                self.kill = Mock()
                self.wait_calls = []

            def wait(self, timeout=None):
                self.wait_calls.append(timeout)
                if len(self.wait_calls) == 1:
                    raise KeyboardInterrupt
                if len(self.wait_calls) == 2:
                    raise subprocess.TimeoutExpired("child", timeout)
                return 0

        process = Process()
        original_stdout_close = process.stdout.close
        stdout_close = Mock()

        def fail_stdout_close_once():
            process.stdout.close = original_stdout_close
            raise OSError("retained pipe close failed")

        stdout_close.side_effect = fail_stdout_close_once
        process.stdout.close = stdout_close
        process.stderr.close = Mock(wraps=process.stderr.close)
        popen.return_value = process
        graph = (MODULE.Stage("interruptible", ("work.py",), "command"),)
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            context = self._context(Path(temporary))
            self.assertEqual(MODULE.execute_stages(graph, context), 130)
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))

        self.assertEqual(receipt["status"], "incomplete")
        self.assertEqual(receipt["current_stage"], "interruptible")
        process.terminate.assert_called_once_with()
        process.kill.assert_called_once_with()
        self.assertEqual(len(process.wait_calls), 3)
        stdout_close.assert_called_once_with()
        process.stderr.close.assert_called_once_with()

    @patch("subprocess.Popen")
    def test_real_windows_style_receipt_log_path_resumes_without_reexecution(self, popen):
        # Mutation caught: native backslash serialization made a valid Windows receipt fail prefix validation.
        popen.return_value = self._popen_result(stdout="first run\n")
        graph = (MODULE.Stage("portable", ("portable.py",), "command"),)
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            context = self._context(root)
            self.assertEqual(MODULE.execute_stages(graph, context), 0)
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["stages"][0]["log_path"], "logs/01-portable.log")
            receipt["status"] = "incomplete"
            MODULE.write_receipt(context.receipt_path, receipt)

            with patch.object(MODULE, "run_stage") as run_stage:
                self.assertEqual(MODULE.execute_stages(graph, context, resume=True), 0)
                run_stage.assert_not_called()

    @patch.object(MODULE, "run_stage")
    def test_malformed_timestamp_duration_or_returncode_reexecutes_instead_of_crashing_or_skipping(self, run_stage):
        graph = (MODULE.Stage("alpha", ("alpha.py",), "command"),)
        cases = (
            ("mixed timezone", {"started_utc": "2026-08-14T12:00:00", "completed_utc": "2026-08-14T12:00:01Z"}),
            ("nan duration", {"duration_seconds": float("nan")}),
            ("infinite duration", {"duration_seconds": float("inf")}),
            ("boolean duration", {"duration_seconds": True}),
            ("boolean return code", {"returncode": False}),
        )
        for label, replacement in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
                root = Path(temporary)
                context = self._context(root)
                entry = self._passed_entry(root, graph[0], 1)
                entry.update(replacement)
                MODULE.write_receipt(context.receipt_path, {
                    "source_commit": "abc123", "mode": "mock", "status": "failed", "stages": [entry],
                })
                run_stage.reset_mock()
                run_stage.return_value = self._result(graph[0], root, 1)

                self.assertEqual(MODULE.execute_stages(graph, context, resume=True), 0)

                self.assertEqual([call.args[0].name for call in run_stage.call_args_list], ["alpha"])

    @patch("subprocess.Popen")
    @patch("subprocess.run")
    def test_post_kill_reap_timeout_preserves_interrupt_exit_and_receipt(self, _run, popen):
        # Mutation caught: cleanup failure must not replace the original Ctrl+C outcome.
        class Process:
            def __init__(self):
                self.pid = 4242
                self.stdout = io.StringIO()
                self.stderr = io.StringIO()
                self.terminate = Mock()
                self.kill = Mock()
                self.wait_calls = []

            def wait(self, timeout=None):
                self.wait_calls.append(timeout)
                if len(self.wait_calls) == 1:
                    raise KeyboardInterrupt
                raise subprocess.TimeoutExpired("child", timeout)

        process = Process()
        process.stdout.close = Mock(wraps=process.stdout.close)
        process.stderr.close = Mock(wraps=process.stderr.close)
        popen.return_value = process
        graph = (MODULE.Stage("timeout_interrupt", ("work.py",), "command"),)
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            context = self._context(Path(temporary))
            self.assertEqual(MODULE.execute_stages(graph, context), 130)
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))

        self.assertEqual(receipt["status"], "incomplete")
        self.assertEqual(receipt["current_stage"], "timeout_interrupt")
        self.assertTrue(receipt["interrupt_cleanup_errors"])
        process.kill.assert_called_once_with()
        process.stdout.close.assert_called_once_with()
        process.stderr.close.assert_called_once_with()

    @patch.object(MODULE, "PIPE_JOIN_TIMEOUT_SECONDS", 0.01)
    @patch("subprocess.Popen")
    @patch("subprocess.run")
    def test_retained_pipe_reader_cannot_block_interrupt_cleanup(self, _run, popen):
        # Mutation caught: a descendant retaining stdout must not hold the driver after Ctrl+C.
        class BlockingStream:
            def __init__(self):
                self.started = threading.Event()
                self.release = threading.Event()
                self.close = Mock()

            def readline(self):
                self.started.set()
                self.release.wait(5)
                return ""

        class Process:
            def __init__(self, stream):
                self.pid = 4243
                self.stdout = stream
                self.stderr = io.StringIO()
                self.terminate = Mock()
                self.kill = Mock()
                self.wait_calls = 0

            def wait(self, timeout=None):
                self.wait_calls += 1
                if self.wait_calls == 1:
                    raise KeyboardInterrupt
                return 0

        blocked = BlockingStream()
        process = Process(blocked)
        process.stderr.close = Mock(wraps=process.stderr.close)
        popen.return_value = process
        graph = (MODULE.Stage("retained_pipe", ("work.py",), "command"),)
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            context = self._context(Path(temporary))
            started = time.monotonic()
            self.assertEqual(MODULE.execute_stages(graph, context), 130)
            elapsed = time.monotonic() - started
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))
            blocked.release.set()

        self.assertLess(elapsed, 0.5)
        self.assertEqual(receipt["status"], "incomplete")
        self.assertTrue(any("reader join timed out" in error for error in receipt["interrupt_cleanup_errors"]))
        blocked.close.assert_called_once_with()
        process.stderr.close.assert_called_once_with()

    @patch.object(MODULE, "_stop_stage_process_tree")
    @patch("subprocess.Popen")
    def test_reader_interrupt_after_child_exit_stops_tree_and_preserves_receipt(self, popen, stop_tree):
        # Mutation caught: Ctrl+C while draining a normal pipe tail must use the same bounded cleanup.
        class Reader:
            def __init__(self, *, interrupt_on: set[int] | None = None):
                self.interrupt_on = interrupt_on or set()
                self.join_timeouts = []
                self.join_calls = 0
                self.start = Mock()

            def join(self, timeout=None):
                self.join_calls += 1
                self.join_timeouts.append(timeout)
                if self.join_calls in self.interrupt_on:
                    raise KeyboardInterrupt

            def is_alive(self):
                return False

        class Process:
            def __init__(self):
                self.stdout = io.StringIO()
                self.stderr = io.StringIO()
                self.pid = 4244
                self.wait_calls = []

            def wait(self, timeout=None):
                self.wait_calls.append(timeout)
                return 0

        stdout_reader = Reader(interrupt_on={1, 2})
        stderr_reader = Reader()
        process = Process()
        process.stdout.close = Mock(wraps=process.stdout.close)
        process.stderr.close = Mock(wraps=process.stderr.close)
        popen.return_value = process
        graph = (MODULE.Stage("tail_interrupt", ("work.py",), "command"),)
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            context = self._context(Path(temporary))
            with patch.object(MODULE.threading, "Thread", side_effect=(stdout_reader, stderr_reader)):
                self.assertEqual(MODULE.execute_stages(graph, context), 130)
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))

        self.assertEqual(receipt["status"], "incomplete")
        self.assertEqual(receipt["current_stage"], "tail_interrupt")
        self.assertEqual(process.wait_calls, [None, MODULE.INTERRUPT_REAP_TIMEOUT_SECONDS])
        self.assertEqual([call.kwargs["force"] for call in stop_tree.call_args_list], [False])
        self.assertEqual(
            stdout_reader.join_timeouts,
            [MODULE.PIPE_JOIN_POLL_SECONDS, MODULE.PIPE_JOIN_TIMEOUT_SECONDS],
        )
        self.assertEqual(stderr_reader.join_timeouts, [MODULE.PIPE_JOIN_TIMEOUT_SECONDS])
        process.stdout.close.assert_called_once_with()
        process.stderr.close.assert_called_once_with()
        self.assertTrue(any("stdout reader join" in error for error in receipt["interrupt_cleanup_errors"]))

    @patch.object(MODULE, "_stop_stage_process_tree")
    @patch("subprocess.Popen")
    def test_setup_interrupt_after_popen_stops_tree_and_preserves_receipt(self, popen, stop_tree):
        # Mutation caught: Ctrl+C in post-Popen setup must not leave a child holding its pipes.
        class Process:
            def __init__(self):
                self.stdout = io.StringIO()
                self.stderr = io.StringIO()
                self.pid = 4245
                self.wait_calls = []

            def wait(self, timeout=None):
                self.wait_calls.append(timeout)
                return 0

        process = Process()
        process.stdout.close = Mock(wraps=process.stdout.close)
        process.stderr.close = Mock(wraps=process.stderr.close)
        popen.return_value = process
        graph = (MODULE.Stage("setup_interrupt", ("work.py",), "command"),)
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            context = self._context(Path(temporary))
            started = time.monotonic()
            with patch.object(MODULE.threading, "Lock", side_effect=KeyboardInterrupt):
                self.assertEqual(MODULE.execute_stages(graph, context), 130)
            elapsed = time.monotonic() - started
            receipt = json.loads(context.receipt_path.read_text(encoding="utf-8"))

        self.assertLess(elapsed, 0.5)
        self.assertEqual(receipt["status"], "incomplete")
        self.assertEqual(receipt["current_stage"], "setup_interrupt")
        self.assertEqual(process.wait_calls, [MODULE.INTERRUPT_REAP_TIMEOUT_SECONDS])
        self.assertEqual([call.kwargs["force"] for call in stop_tree.call_args_list], [False])
        process.stdout.close.assert_called_once_with()
        process.stderr.close.assert_called_once_with()

    @patch("subprocess.Popen")
    def test_normal_completion_drains_buffered_pipe_tail_before_closing_it(self, popen):
        # Mutation caught: closing pipes immediately after wait() can discard a buffered final line.
        class BufferedTailStream:
            def __init__(self):
                self.waiting_for_release = threading.Event()
                self.release = threading.Event()
                self.close_called = threading.Event()
                self.closed = False
                self.emitted = False
                self.close = Mock(side_effect=self._close)

            def _close(self):
                self.closed = True
                self.close_called.set()

            def readline(self):
                if self.emitted:
                    return ""
                self.waiting_for_release.set()
                self.release.wait(1)
                if self.closed:
                    return ""
                self.emitted = True
                return "buffered tail\\n"

        class Process:
            def __init__(self, stream):
                self.stdout = stream
                self.stderr = io.StringIO()

            def wait(self, timeout=None):
                return 0

        stream = BufferedTailStream()
        process = Process(stream)
        process.stderr.close = Mock(wraps=process.stderr.close)
        popen.return_value = process
        sink = io.StringIO()
        result_box = []
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            context = self._context(root)
            stage = MODULE.Stage("buffered_tail", ("work.py",), "command")
            with patch.object(MODULE.sys, "stdout", sink):
                worker = threading.Thread(target=lambda: result_box.append(MODULE.run_stage(stage, context)))
                worker.start()
                self.assertTrue(stream.waiting_for_release.wait(1))
                try:
                    self.assertFalse(stream.close_called.wait(0.1))
                finally:
                    stream.release.set()
                    worker.join(2)

            self.assertFalse(worker.is_alive())
            self.assertEqual(result_box[0].returncode, 0)
            self.assertIn("buffered tail", sink.getvalue())
            self.assertIn("buffered tail", (root / result_box[0].log_path).read_text(encoding="utf-8"))

        stream.close.assert_called_once_with()
        process.stderr.close.assert_called_once_with()

    @patch.object(MODULE, "PIPE_JOIN_TIMEOUT_SECONDS", 0.05)
    @patch("subprocess.Popen")
    def test_normal_completion_keeps_draining_tail_that_makes_slow_progress(self, popen):
        # Mutation caught: a fixed total join cutoff truncates a busy tail after its first line.
        class SlowProgressStream:
            def __init__(self):
                self.lines = ["tail one\\n", "tail two\\n", "tail three\\n", "tail four\\n"]
                self.closed = False
                self.close = Mock(side_effect=self._close)

            def _close(self):
                self.closed = True

            def readline(self):
                if self.closed or not self.lines:
                    return ""
                time.sleep(0.03)
                if self.closed:
                    return ""
                return self.lines.pop(0)

        class Process:
            def __init__(self, stream):
                self.stdout = stream
                self.stderr = io.StringIO()

            def wait(self, timeout=None):
                return 0

        stream = SlowProgressStream()
        process = Process(stream)
        process.stderr.close = Mock(wraps=process.stderr.close)
        popen.return_value = process
        sink = io.StringIO()
        expected_tail = "tail one\\ntail two\\ntail three\\ntail four\\n"
        with tempfile.TemporaryDirectory(dir=MODULE_PATH.parent) as temporary:
            root = Path(temporary)
            context = self._context(root)
            stage = MODULE.Stage("slow_tail", ("work.py",), "command")
            with patch.object(MODULE.sys, "stdout", sink):
                result = MODULE.run_stage(stage, context)

            self.assertEqual(result.returncode, 0)
            self.assertIn(expected_tail, sink.getvalue())
            self.assertIn(expected_tail, (root / result.log_path).read_text(encoding="utf-8"))

        stream.close.assert_called_once_with()
        process.stderr.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
