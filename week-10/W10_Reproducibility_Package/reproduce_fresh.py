"""Declarative command graphs for fresh full and mock reproductions."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time


@dataclass(frozen=True)
class Stage:
    name: str
    argv: tuple[str, ...]
    category: str


OFFLINE_ENVIRONMENT_KEYS = (
    "HF_HOME",
    "HF_HUB_CACHE",
    "HF_HUB_OFFLINE",
    "TRANSFORMERS_OFFLINE",
    "PYTHONHASHSEED",
)
MINIMUM_FREE_BYTES = 80 * 1024**3
INTERRUPT_REAP_TIMEOUT_SECONDS = 5.0
PIPE_JOIN_TIMEOUT_SECONDS = 1.0
PIPE_JOIN_POLL_SECONDS = 0.05
PACKAGE_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PACKAGE_ROOT.parents[1]
PROTOCOL_INPUTS = (
    "week-07/W07_Preflight_Raw_Model_Outputs.jsonl",
    "week-07/W07_Judge_Gold_Ratings.csv",
)
GENERATED_EVIDENCE = (
    "week-06/W06_Raw_Model_Outputs.jsonl",
    "week-06/W06_Judge_Ratings.csv",
    "week-07/W07_Raw_Model_Outputs.jsonl",
    "week-07/W07_Judge_Ratings.csv",
)
FULL_RUN_REQUIREMENTS = (
    "--accept-compute-cost",
    "Python 3.11",
    "at least 80 GiB free space",
    "CUDA",
    "network access or a complete model cache",
    "a separately supplied --bundle PATH",
)
PREFLIGHT_QUERY = """
import importlib.metadata
import json
import sys
import torch

print(json.dumps({
    \"python_version\": \".\".join(map(str, sys.version_info[:3])),
    \"packages\": {
        name: importlib.metadata.version(name)
        for name in (\"torch\", \"transformers\", \"accelerate\", \"bitsandbytes\", \"huggingface_hub\", \"tokenizers\", \"safetensors\")
    },
    \"cuda_available\": torch.cuda.is_available(),
    \"cuda_device_name\": torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"\",
}))
"""


def _stage(name: str, *argv: str, category: str = "command") -> Stage:
    return Stage(name, tuple(argv), category)


def offline_environment(worktree: Path) -> dict[str, str]:
    """Return the deterministic offline environment for run-local children."""
    environment = os.environ.copy()
    environment.update({
        "HF_HOME": str(worktree / ".hf-cache"),
        "HF_HUB_CACHE": str(worktree / ".hf-cache" / "hub"),
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "PYTHONHASHSEED": "0",
    })
    return environment


def git_read_environment(root: Path) -> dict[str, str]:
    """Return an offline environment that prevents read-only Git lock writes."""
    environment = offline_environment(root)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    return environment


def create_environment(worktree: Path) -> Path:
    """Create and install the pinned run-local inference environment."""
    root = Path(worktree)
    environment_dir = root / ".fresh-venv"
    python = (
        environment_dir / "Scripts" / "python.exe"
        if os.name == "nt"
        else environment_dir / "bin" / "python"
    )
    environment = offline_environment(root)
    commands = (
        [sys.executable, "-m", "venv", str(environment_dir)],
        [str(python), "-m", "pip", "install", "--upgrade", "pip"],
        [str(python), "-m", "pip", "install", "-r", str(PACKAGE_ROOT / "requirements-analysis.txt")],
        [
            str(python), "-m", "pip", "install", "torch==2.11.0",
            "--index-url", "https://download.pytorch.org/whl/cu128",
        ],
        [
            str(python), "-m", "pip", "install", "-r", str(PACKAGE_ROOT / "requirements-inference.txt"),
            "--extra-index-url", "https://download.pytorch.org/whl/cu128",
        ],
    )
    for command in commands:
        subprocess.run(command, check=True, cwd=str(root), env=environment)
    return python


def preflight_full(worktree: Path, python: Path, cache_dir: Path) -> dict[str, object]:
    """Validate full-run capacity and return receipt-ready runtime facts."""
    root = Path(worktree)
    free_bytes = shutil.disk_usage(root).free
    if free_bytes < MINIMUM_FREE_BYTES:
        raise RuntimeError("full reproduction requires at least 80 GiB free at the run location")

    result = subprocess.run(
        [str(python), "-c", PREFLIGHT_QUERY],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(root),
        env=offline_environment(root),
    )
    try:
        facts = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("full reproduction preflight returned invalid runtime facts") from error

    python_version = str(facts.get("python_version", ""))
    if not python_version.startswith("3.11."):
        raise RuntimeError("full reproduction requires Python 3.11")
    if facts.get("cuda_available") is not True:
        raise RuntimeError("full reproduction requires CUDA availability")
    device_name = str(facts.get("cuda_device_name", "")).strip()
    if not device_name:
        raise RuntimeError("full reproduction requires a CUDA device name")

    packages = facts.get("packages")
    if not isinstance(packages, dict):
        raise RuntimeError("full reproduction preflight did not report package versions")
    preflight = {
        "python_version": python_version,
        "free_bytes": free_bytes,
        "cache_dir": str(cache_dir),
        "packages": packages,
        "gpu": {
            "cuda_available": True,
            "device_name": device_name,
        },
    }
    receipt_path = root / "run-receipt.json"
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("full reproduction preflight requires a valid run receipt") from error
    if not isinstance(receipt, dict):
        raise RuntimeError("full reproduction preflight requires a valid run receipt")
    receipt["preflight"] = preflight
    _write_receipt_atomically(root, receipt)
    return preflight


def full_command_graph() -> tuple[Stage, ...]:
    return (
        _stage("restore_protocol_inputs", "week-10/W10_Reproducibility_Package/fetch_data.py", "--check", category="internal"),
        _stage("clear_generated_evidence", "clear_generated_evidence", category="internal"),
        _stage("week03_generate", "week-03/run_w03_baseline.py"),
        _stage("week04_generate", "week-04/run_w04_extended.py", "--model", "mistral-7b-instruct-v0.3"),
        _stage("week05_generate", "week-05/run_w05_experiment.py"),
        _stage("week05_audit", "week-05/audit_w05_semantics.py"),
        _stage("week05_notebook", "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", "week-05/W05_Experiment_Notebook.ipynb"),
        _stage("week06_build_bank", "week-06/build_w06_bank.py"),
        _stage("week06_generate", "week-06/run_w06_experiment2.py"),
        _stage("week06_judge", "week-06/judge_w06_experiment2.py"),
        _stage("week06_test", "week-06/test_w06_experiment2.py"),
        _stage("week06_verify", "week-06/verify_w06_independent.py"),
        _stage("week07_generate", "week-07/run_w07_replication.py", "--phase", "confirmation", "--batch-size", "8"),
        _stage("week07_judge", "week-07/judge_w07_replication.py", "--phase", "confirmation", "--batch-size", "8"),
        _stage("week07_analyze", "week-07/analyze_w07.py"),
        _stage("week07_notebook_build", "week-07/build_w07_notebook.py"),
        _stage("week07_notebook_execute", "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", "--ExecutePreprocessor.timeout=900", "week-07/W07_Analysis_Notebook.ipynb"),
        _stage("week07_report", "week-07/write_w07_report.py"),
        _stage("week08_analyze", "week-08/analyze_w08_pressure_cues.py"),
        _stage("week08_verify", "week-08/verify_w08.py"),
        _stage("week09_tables", "week-09/build_w09_paper_tables.py"),
        _stage("week09_figures", "week-09/build_w09_paper_figures.py"),
        _stage("week09_verify", "week-09/verify_w09.py"),
        _stage("week10_sensitivity", "week-10/analyze_w10_judge_sensitivity.py"),
        _stage("fresh_run_verify", "fresh_run_verify", category="internal"),
    )


def mock_command_graph() -> tuple[Stage, ...]:
    return (
        _stage("clear_generated_evidence", "clear_generated_evidence", category="internal"),
        _stage("week03_generate", "week-03/run_w03_baseline.py", "--mock", "--smoke"),
        _stage("week04_generate", "week-04/run_w04_extended.py", "--mock", "--smoke", "--model", "mistral-7b-instruct-v0.3"),
        _stage("week05_generate", "week-05/run_w05_experiment.py", "--mock", "--smoke"),
        _stage("week05_audit", "week-05/audit_w05_semantics.py"),
        _stage("week06_build_bank", "week-06/build_w06_bank.py"),
        _stage("week06_generate", "week-06/run_w06_experiment2.py", "--smoke"),
        _stage("week06_judge", "week-06/judge_w06_experiment2.py", "--smoke"),
        _stage("week06_test", "week-06/test_w06_experiment2.py", "--smoke"),
        _stage("week07_generate", "week-07/run_w07_replication.py", "--phase", "smoke", "--limit", "1"),
        _stage("mock_receipt_check", "mock_only", category="internal"),
    )


def source_state(root: Path, *, mode: str | None = None) -> dict[str, object]:
    """Return the source commit and whether tracked source files have changed."""
    source_root = Path(root)
    commit = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        env=git_read_environment(source_root),
    ).stdout.strip()
    tracked_changes = subprocess.run(
        ["git", "-C", str(source_root), "status", "--porcelain", "--untracked-files=no"],
        check=True,
        capture_output=True,
        text=True,
        env=git_read_environment(source_root),
    ).stdout.strip()
    state = {
        "source_commit": commit,
        "tracked_changes": bool(tracked_changes),
    }
    if state["tracked_changes"] and mode in {"full", "mock"}:
        raise ValueError(f"{mode} reproduction requires a clean tracked source tree")
    return state


def validate_destination(source_root: Path, run_dir: Path, resume: bool, *, mode: str | None = None) -> None:
    """Reject destinations that could overwrite the source or lose run identity."""
    source = Path(source_root).resolve()
    destination = Path(run_dir).resolve()
    reserved_runs = source / ".reproduction-runs"
    is_reserved_run = reserved_runs in destination.parents
    if destination == source or destination in source.parents:
        raise ValueError("run destination must be external to the source repository")
    if source in destination.parents and not is_reserved_run:
        raise ValueError("run destination must be external to the source repository")

    if not resume:
        if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
            raise ValueError("run destination must be empty unless resuming")
        return

    if not destination.is_dir() or not any(destination.iterdir()):
        raise ValueError("cannot resume from an empty or missing run destination")
    if mode not in {"full", "mock"}:
        raise ValueError("resume requires an expected full or mock mode")
    if not (destination / ".git").is_file():
        raise ValueError("cannot resume without a Git worktree marker")

    receipt_path = destination / "run-receipt.json"
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("cannot resume without a valid run receipt") from error
    if not isinstance(receipt, dict):
        raise ValueError("cannot resume without a valid run receipt")
    if receipt.get("mode") not in {"full", "mock"} or receipt.get("mode") != mode:
        raise ValueError("cannot resume a run from a different mode")
    if receipt.get("status") not in {"incomplete", "failed"}:
        raise ValueError("cannot resume a completed or invalid run receipt")

    current_commit = source_state(source, mode=mode)["source_commit"]
    if receipt.get("source_commit") != current_commit:
        raise ValueError("cannot resume a run from a different source commit")
    is_worktree = subprocess.run(
        ["git", "-C", str(destination), "rev-parse", "--is-inside-work-tree"],
        check=True,
        capture_output=True,
        text=True,
        env=git_read_environment(destination),
    ).stdout.strip()
    if is_worktree != "true":
        raise ValueError("cannot resume from a destination that is not a Git worktree")
    worktree_commit = subprocess.run(
        ["git", "-C", str(destination), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        env=git_read_environment(destination),
    ).stdout.strip()
    if worktree_commit != current_commit:
        raise ValueError("cannot resume from a worktree at a different source commit")


def write_receipt(path: Path, payload: dict[str, object]) -> None:
    """Atomically replace a receipt only after its complete JSON is flushed."""
    receipt_path = Path(path)
    temporary_path = receipt_path.with_name(f"{receipt_path.name}.tmp")
    with temporary_path.open("w", encoding="utf-8") as temporary:
        json.dump(payload, temporary, indent=2, sort_keys=True)
        temporary.write("\n")
        temporary.flush()
        os.fsync(temporary.fileno())
    try:
        os.replace(temporary_path, receipt_path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _write_receipt_atomically(run_dir: Path, receipt: dict[str, object]) -> None:
    """Backward-compatible run-directory form used by Tasks 3 and 4."""
    write_receipt(Path(run_dir) / "run-receipt.json", receipt)


def create_worktree(source_root: Path, run_dir: Path, commit: str, *, mode: str = "full") -> None:
    """Create a detached worktree and record its incomplete source identity."""
    if mode not in {"full", "mock"}:
        raise ValueError("worktree creation requires full or mock mode")
    source = Path(source_root)
    destination = Path(run_dir)
    subprocess.run(
        ["git", "-C", str(source), "worktree", "add", "--detach", str(destination), commit],
        check=True,
        env=offline_environment(destination),
    )
    _write_receipt_atomically(
        destination,
        {
            "source_commit": commit,
            "mode": mode,
            "status": "incomplete",
        },
    )


@dataclass(frozen=True)
class RunContext:
    source_root: Path
    worktree: Path
    python: Path
    receipt_path: Path
    bundle: Path | None
    mode: str
    env: dict[str, str]


@dataclass(frozen=True)
class StageResult:
    name: str
    argv: tuple[str, ...]
    started_utc: str
    completed_utc: str
    duration_seconds: float
    returncode: int
    status: str
    log_path: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_receipt(path: Path) -> dict[str, object]:
    try:
        receipt = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("stage execution requires a valid run receipt") from error
    if not isinstance(receipt, dict):
        raise RuntimeError("stage execution requires a valid run receipt")
    return receipt


def _stage_number(stage: Stage, context: RunContext) -> int:
    graph = full_command_graph() if context.mode == "full" else mock_command_graph()
    for index, candidate in enumerate(graph, start=1):
        if candidate.name == stage.name:
            return index
    receipt = _read_receipt(context.receipt_path)
    stages = receipt.get("stages", [])
    return len(stages) + 1 if isinstance(stages, list) else 1


def _expected_stage_argv(stage: Stage, context: RunContext) -> tuple[str, ...]:
    if stage.name == "clear_generated_evidence":
        return ("clear_generated_evidence",)
    if stage.name in {"mock_receipt_check", "fresh_run_verify"}:
        return stage.argv
    if stage.name == "restore_protocol_inputs":
        return _restore_argv(stage, context)
    return (str(context.python), *stage.argv)


def _expected_log_path(index: int, stage: Stage) -> str:
    return (Path("logs") / f"{index:02d}-{stage.name}.log").as_posix()


def _is_valid_passed_stage(entry: object, stage: Stage, context: RunContext, index: int) -> bool:
    if not isinstance(entry, dict):
        return False
    if entry.get("name") != stage.name or entry.get("status") != "passed":
        return False
    if entry.get("argv") != list(_expected_stage_argv(stage, context)):
        return False
    returncode = entry.get("returncode")
    if isinstance(returncode, bool) or returncode != 0:
        return False
    duration = entry.get("duration_seconds")
    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(duration)
        or duration < 0
    ):
        return False
    try:
        started = str(entry["started_utc"]).strip()
        completed = str(entry["completed_utc"]).strip()
        if not started or not completed or not started.endswith("Z") or not completed.endswith("Z"):
            return False
        started_at = datetime.fromisoformat(started.replace("Z", "+00:00"))
        completed_at = datetime.fromisoformat(completed.replace("Z", "+00:00"))
        if started_at.tzinfo != timezone.utc or completed_at.tzinfo != timezone.utc:
            return False
        if completed_at < started_at:
            return False
    except (KeyError, TypeError, ValueError):
        return False
    log_path = _expected_log_path(index, stage)
    return entry.get("log_path") == log_path and (context.worktree / log_path).is_file()


def _validated_resume_prefix(graph: tuple[Stage, ...], context: RunContext, receipt: dict[str, object]) -> int:
    """Return the only contiguous, fully validated prefix safe to skip."""
    entries = receipt.get("stages")
    if not isinstance(entries, list):
        return 0
    entry_index = 0
    passed_count = 0
    for stage_index, stage in enumerate(graph, start=1):
        while entry_index < len(entries):
            entry = entries[entry_index]
            if not isinstance(entry, dict) or entry.get("name") != stage.name:
                return passed_count
            entry_index += 1
            if _is_valid_passed_stage(entry, stage, context, stage_index):
                passed_count += 1
                break
            if entry.get("status") != "failed":
                return passed_count
        else:
            return passed_count
    return passed_count


def _log_stage_output(log_path: Path, stdout: str, stderr: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", newline="") as log_file:
        if stdout:
            log_file.write(stdout)
        if stderr:
            if stdout and not stdout.endswith("\n"):
                log_file.write("\n")
            log_file.write(stderr)
    if stdout:
        print(stdout, end="" if stdout.endswith("\n") else "\n")
    if stderr:
        print(stderr, end="" if stderr.endswith("\n") else "\n", file=sys.stderr)


def _stage_process_options() -> dict[str, object]:
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
    return {"start_new_session": True}


def _record_interrupt_cleanup_errors(context: RunContext, errors: list[str]) -> None:
    if not errors:
        return
    try:
        receipt = _read_receipt(context.receipt_path)
        receipt["interrupt_cleanup_errors"] = errors
        write_receipt(context.receipt_path, receipt)
    except BaseException:
        pass


def _stop_stage_process_tree(process: object, *, force: bool, errors: list[str]) -> None:
    """Best-effort group/tree shutdown that never replaces the original interrupt."""
    try:
        if os.name == "nt":
            if not force:
                control_break = getattr(signal, "CTRL_BREAK_EVENT", None)
                if control_break is not None and hasattr(process, "send_signal"):
                    process.send_signal(control_break)  # type: ignore[union-attr]
                    return
                process.terminate()  # type: ignore[union-attr]
                return
            pid = getattr(process, "pid", None)
            if isinstance(pid, int):
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=INTERRUPT_REAP_TIMEOUT_SECONDS,
                )
            process.kill()  # type: ignore[union-attr]
            return
        process_id = getattr(process, "pid")
        os.killpg(process_id, signal.SIGKILL if force else signal.SIGTERM)
    except BaseException as error:
        errors.append(f"{'force' if force else 'graceful'} shutdown: {error}")
        try:
            if force:
                process.kill()  # type: ignore[union-attr]
            else:
                process.terminate()  # type: ignore[union-attr]
        except BaseException as fallback_error:
            errors.append(f"fallback shutdown: {fallback_error}")


def _stream_child_output(argv: tuple[str, ...], context: RunContext, log_path: Path) -> int:
    """Tee a child process's stdout and stderr as it runs, including on Windows."""
    process: subprocess.Popen[str] | None = None
    interrupted = False
    cleanup_errors: list[str] = []
    readers: tuple[tuple[str, threading.Thread], ...] = ()
    streams: tuple[tuple[str, object | None], ...] = ()

    def close_pipes() -> None:
        for stream_name, stream in streams:
            if stream is None:
                continue
            try:
                stream.close()  # type: ignore[union-attr]
            except BaseException as error:
                if interrupted:
                    cleanup_errors.append(f"{stream_name} close: {error}")
                else:
                    raise

    def join_readers(*, record_timeouts: bool) -> bool:
        any_alive = False
        for stream_name, reader_thread in readers:
            try:
                reader_thread.join(timeout=PIPE_JOIN_TIMEOUT_SECONDS)
                if reader_thread.is_alive():
                    any_alive = True
                    if record_timeouts:
                        cleanup_errors.append(f"{stream_name} reader join timed out")
            except BaseException as error:
                if interrupted:
                    cleanup_errors.append(f"{stream_name} reader join: {error}")
                else:
                    raise
        return any_alive

    try:
        process = subprocess.Popen(
            list(argv),
            cwd=str(context.worktree),
            env=context.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            **_stage_process_options(),
        )
        streams = (("stdout", process.stdout), ("stderr", process.stderr))
        write_lock = threading.Lock()
        reader_state_lock = threading.Lock()
        reader_state = {
            "stdout": {"active": False, "last_progress": time.monotonic()},
            "stderr": {"active": False, "last_progress": time.monotonic()},
        }

        def drain_normal_readers() -> bool:
            """Wait through productive tail draining, but bound an inactive retained pipe."""
            with reader_state_lock:
                observed_progress = {
                    name: state["last_progress"] for name, state in reader_state.items()
                }
            last_activity = time.monotonic()
            while True:
                any_alive = False
                for _stream_name, reader_thread in readers:
                    reader_thread.join(timeout=PIPE_JOIN_POLL_SECONDS)
                    any_alive = any_alive or reader_thread.is_alive()
                if not any_alive:
                    return False
                with reader_state_lock:
                    current_progress = {
                        name: state["last_progress"] for name, state in reader_state.items()
                    }
                    active = any(
                        reader_thread.is_alive() and reader_state[stream_name]["active"]
                        for stream_name, reader_thread in readers
                    )
                progressed = any(
                    current_progress[name] > observed_progress[name]
                    for name in current_progress
                )
                if progressed or active:
                    last_activity = time.monotonic()
                    observed_progress = current_progress
                if time.monotonic() - last_activity >= PIPE_JOIN_TIMEOUT_SECONDS:
                    return True

        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8", newline="") as log_file:
            def tee(stream_name: str, stream: object, terminal: object) -> None:
                try:
                    for line in iter(stream.readline, ""):  # type: ignore[union-attr]
                        with reader_state_lock:
                            reader_state[stream_name]["active"] = True
                        try:
                            with write_lock:
                                log_file.write(line)
                                log_file.flush()
                            terminal.write(line)  # type: ignore[union-attr]
                            terminal.flush()  # type: ignore[union-attr]
                        finally:
                            with reader_state_lock:
                                reader_state[stream_name]["active"] = False
                                reader_state[stream_name]["last_progress"] = time.monotonic()
                except (OSError, ValueError):
                    return

            stdout_thread = threading.Thread(target=tee, args=("stdout", process.stdout, sys.stdout), daemon=True)
            stderr_thread = threading.Thread(target=tee, args=("stderr", process.stderr, sys.stderr), daemon=True)
            readers = (("stdout", stdout_thread), ("stderr", stderr_thread))
            stdout_thread.start()
            stderr_thread.start()
            returncode = process.wait()
            # wait() only confirms the direct child exited. Drain its pipe tails before close().
            retained_pipe = drain_normal_readers()
            close_pipes()
            if retained_pipe:
                # A descendant can retain an inherited handle; the fallback remains bounded.
                join_readers(record_timeouts=False)
    except KeyboardInterrupt:
        interrupted = True
        if process is not None:
            _stop_stage_process_tree(process, force=False, errors=cleanup_errors)
            try:
                process.wait(timeout=INTERRUPT_REAP_TIMEOUT_SECONDS)
            except BaseException as error:
                cleanup_errors.append(f"graceful reap: {error}")
                _stop_stage_process_tree(process, force=True, errors=cleanup_errors)
                try:
                    process.wait(timeout=INTERRUPT_REAP_TIMEOUT_SECONDS)
                except BaseException as force_error:
                    cleanup_errors.append(f"force reap: {force_error}")
        # A stopped child or descendant may retain a pipe: break readers out first.
        close_pipes()
        join_readers(record_timeouts=True)
        _record_interrupt_cleanup_errors(context, cleanup_errors)
        raise
    return int(returncode)


def _protocol_hashes(worktree: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative_path in PROTOCOL_INPUTS:
        target = worktree / relative_path
        if not target.is_file():
            raise RuntimeError(f"restored protocol input is missing: {relative_path}")
        hashes[relative_path] = hashlib.sha256(target.read_bytes()).hexdigest()
    return hashes


def _record_protocol_evidence(context: RunContext, *, deleted: list[str] | None = None) -> None:
    receipt = _read_receipt(context.receipt_path)
    if deleted is None:
        receipt["protocol_inputs"] = _protocol_hashes(context.worktree)
    else:
        receipt["deleted_generated_evidence"] = deleted
    write_receipt(context.receipt_path, receipt)


def _record_protocol_restore(context: RunContext, argv: tuple[str, ...]) -> None:
    if context.bundle is None:
        raise RuntimeError("protocol restoration requires a local bundle")
    receipt = _read_receipt(context.receipt_path)
    receipt["protocol_restore"] = {
        "mode": "local_bundle",
        "network_authorized": False,
        "argv": list(argv),
    }
    write_receipt(context.receipt_path, receipt)


def _restore_argv(stage: Stage, context: RunContext) -> tuple[str, ...]:
    del stage
    if context.bundle is None:
        raise RuntimeError("protocol restoration requires --bundle PATH")
    argv = [str(context.python), "week-10/W10_Reproducibility_Package/fetch_data.py"]
    argv.extend(("--from-path", str(context.bundle.resolve())))
    return tuple(argv)


def _clear_generated_evidence(worktree: Path) -> list[str]:
    deleted: list[str] = []
    for relative_path in GENERATED_EVIDENCE:
        target = worktree / relative_path
        if target.is_file():
            target.unlink()
            deleted.append(relative_path)
    return deleted


def _run_fresh_verifier(context: RunContext) -> str:
    """Run the in-process evidence verifier after every prior full stage passed."""
    if str(PACKAGE_ROOT) not in sys.path:
        sys.path.insert(0, str(PACKAGE_ROOT))
    from verify_fresh_run import verify

    evidence = verify(context.worktree, context.receipt_path)
    return json.dumps(evidence, indent=2, sort_keys=True)


def run_stage(stage: Stage, context: RunContext) -> StageResult:
    """Run one stage in its detached worktree and write a durable stage log."""
    started_utc = _utc_now()
    started = time.monotonic()
    index = _stage_number(stage, context)
    log_path = context.worktree / "logs" / f"{index:02d}-{stage.name}.log"
    if stage.name == "clear_generated_evidence":
        argv = _expected_stage_argv(stage, context)
        deleted = _clear_generated_evidence(context.worktree)
        _record_protocol_evidence(context, deleted=deleted)
        stdout = "\n".join(deleted)
        returncode = 0
    elif stage.name == "fresh_run_verify":
        argv = _expected_stage_argv(stage, context)
        stdout = _run_fresh_verifier(context)
        returncode = 0
    elif stage.name == "mock_receipt_check":
        argv = _expected_stage_argv(stage, context)
        stdout = ""
        returncode = 0
    else:
        argv = _expected_stage_argv(stage, context)
        if stage.name == "restore_protocol_inputs":
            _record_protocol_restore(context, argv)
        print(f"running stage {stage.name}: {' '.join(argv)}")
        returncode = _stream_child_output(argv, context, log_path)
        if stage.name == "restore_protocol_inputs" and returncode == 0:
            _record_protocol_evidence(context)
        stdout = None
    if stdout is not None:
        _log_stage_output(log_path, stdout, "")
    completed_utc = _utc_now()
    return StageResult(
        name=stage.name,
        argv=tuple(argv),
        started_utc=started_utc,
        completed_utc=completed_utc,
        duration_seconds=round(time.monotonic() - started, 6),
        returncode=returncode,
        status="passed" if returncode == 0 else "failed",
        log_path=log_path.relative_to(context.worktree).as_posix(),
    )


def _append_stage_result(context: RunContext, result: StageResult) -> None:
    receipt = _read_receipt(context.receipt_path)
    stages = receipt.setdefault("stages", [])
    if not isinstance(stages, list):
        raise RuntimeError("run receipt has invalid stages")
    stages.append(asdict(result))
    write_receipt(context.receipt_path, receipt)


def execute_stages(
    graph: tuple[Stage, ...], context: RunContext, *, resume: bool = False,
) -> int:
    """Execute a graph once, persisting after every result for safe resume."""
    receipt = _read_receipt(context.receipt_path)
    resume_prefix = _validated_resume_prefix(graph, context, receipt) if resume else 0

    try:
        for stage_index, stage in enumerate(graph):
            if stage_index < resume_prefix:
                continue
            receipt = _read_receipt(context.receipt_path)
            receipt["status"] = "incomplete"
            receipt["current_stage"] = stage.name
            write_receipt(context.receipt_path, receipt)
            result = run_stage(stage, context)
            _append_stage_result(context, result)
            if result.returncode != 0:
                receipt = _read_receipt(context.receipt_path)
                receipt["status"] = "failed"
                receipt["failed_stage"] = stage.name
                receipt["current_stage"] = stage.name
                write_receipt(context.receipt_path, receipt)
                return result.returncode or 1
    except KeyboardInterrupt:
        receipt = _read_receipt(context.receipt_path)
        receipt["status"] = "incomplete"
        write_receipt(context.receipt_path, receipt)
        return 130
    except BaseException as error:
        receipt = _read_receipt(context.receipt_path)
        if receipt.get("current_stage") == "fresh_run_verify":
            try:
                (context.worktree / "fresh-verification.json").unlink(missing_ok=True)
            except OSError:
                pass
            receipt["status"] = "incomplete"
            receipt["verification_pending"] = True
            receipt.pop("failed_stage", None)
        else:
            receipt["status"] = "failed"
            receipt["failed_stage"] = str(receipt.get("current_stage", "unknown"))
        receipt["error"] = str(error)
        write_receipt(context.receipt_path, receipt)
        return 1

    receipt = _read_receipt(context.receipt_path)
    receipt.pop("current_stage", None)
    receipt.pop("failed_stage", None)
    if context.mode == "mock":
        receipt["status"] = "mock_only"
    elif receipt.get("status") != "complete":
        receipt["status"] = "incomplete"
        receipt["verification_pending"] = True
    write_receipt(context.receipt_path, receipt)
    return 0


def _prefetch_models(context: RunContext) -> None:
    """Run the sole Hugging Face-online model-prefetch child with the run-local cache."""
    network_env = context.env.copy()
    network_env.pop("HF_HUB_OFFLINE", None)
    network_env.pop("TRANSFORMERS_OFFLINE", None)
    subprocess.run(
        [
            str(context.python),
            "week-10/W10_Reproducibility_Package/prefetch_models.py",
            context.env["HF_HUB_CACHE"],
        ],
        check=True,
        cwd=str(context.worktree),
        env=network_env,
    )


def _graph_with_batch_size(graph: tuple[Stage, ...], batch_size: int) -> tuple[Stage, ...]:
    updated: list[Stage] = []
    for stage in graph:
        if stage.name in {"week07_generate", "week07_judge"}:
            argv = list(stage.argv)
            argv[argv.index("--batch-size") + 1] = str(batch_size)
            updated.append(replace(stage, argv=tuple(argv)))
        else:
            updated.append(stage)
    return tuple(updated)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("plan", "mock", "full"), default="plan")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--accept-compute-cost", action="store_true")
    parser.add_argument("--batch-size", type=int, default=8)
    return parser


def _default_run_dir(source_root: Path) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return source_root / ".reproduction-runs" / run_id


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.mode == "full" and not args.accept_compute_cost:
        print("full mode requires --accept-compute-cost", file=sys.stderr)
        return 2
    if args.mode == "full" and args.bundle is None:
        print("full mode requires --bundle PATH for local protocol restoration", file=sys.stderr)
        return 2
    if args.batch_size <= 0 or (args.mode in {"plan", "full"} and 480 % args.batch_size != 0):
        print("--batch-size must be positive and divide 480 for a full confirmation run", file=sys.stderr)
        return 2

    source_root = SOURCE_ROOT.resolve()
    run_dir = (args.run_dir or _default_run_dir(source_root)).resolve()
    state = source_state(source_root, mode=args.mode)
    graph = full_command_graph() if args.mode in {"plan", "full"} else mock_command_graph()
    if args.mode in {"plan", "full"}:
        graph = _graph_with_batch_size(graph, args.batch_size)
    if args.mode == "plan":
        print(json.dumps({
            "mode": "plan",
            "source_state": state,
            "run_dir": str(run_dir),
            "full_run_requirements": list(FULL_RUN_REQUIREMENTS),
            "stages": [asdict(stage) for stage in graph],
        }, indent=2, sort_keys=True))
        return 0

    validate_destination(source_root, run_dir, args.resume, mode=args.mode)
    if not args.resume:
        create_worktree(source_root, run_dir, str(state["source_commit"]), mode=args.mode)
    receipt_path = run_dir / "run-receipt.json"
    python = Path(sys.executable)
    context = RunContext(
        source_root=source_root,
        worktree=run_dir,
        python=python,
        receipt_path=receipt_path,
        bundle=args.bundle.resolve() if args.bundle is not None else None,
        mode=args.mode,
        env=offline_environment(run_dir),
    )
    if args.mode == "full":
        try:
            python = create_environment(run_dir)
            context = replace(context, python=python)
            preflight_full(run_dir, python, run_dir / ".hf-cache")
            _prefetch_models(context)
        except KeyboardInterrupt:
            receipt = _read_receipt(receipt_path)
            receipt["status"] = "incomplete"
            receipt["current_stage"] = "setup"
            write_receipt(receipt_path, receipt)
            return 130
        except BaseException as error:
            receipt = _read_receipt(receipt_path)
            receipt["status"] = "failed"
            receipt["failed_stage"] = "setup"
            receipt["error"] = str(error)
            write_receipt(receipt_path, receipt)
            return 1
    return execute_stages(graph, context, resume=args.resume)


if __name__ == "__main__":
    raise SystemExit(main())
