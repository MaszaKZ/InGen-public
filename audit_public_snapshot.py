"""Standalone, fail-closed audit for an exported InGen public snapshot."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote


SOURCE_COMMIT = "1989f335c7562b8f74444286ebc26c317bfe5024"
PROVENANCE_SCHEMA = "ingen-public-snapshot-v1"
EXPORT_SCHEMA = "ingen-public-export-v1"
DATA_SCHEMA = "w10-data-manifest-public-v1"
PACKAGE = Path("week-10/W10_Reproducibility_Package")
DATA_MANIFEST = PACKAGE / "data_manifest.json"
FETCH = PACKAGE / "fetch_data.py"
TRANSFORMED_PATHS = (
    ".gitattributes",
    ".gitignore",
    "README.md",
    "week-06/W06_Mid_Review_Work_Process.md",
    "week-07/README.md",
    "week-07/W07_Precalibration_Audit.md",
    "week-07/W07_Prompt_Correction_Review.md",
    "week-07/Wk-07-ResearchLog.md",
    "week-09/W09_Paper_Draft_v1.md",
    "week-09/W09_Self_Critique.md",
    "week-10/README.md",
    "week-10/W10_Feedback.md",
    "week-10/W10_Reproducibility_Package/README.md",
    "week-10/W10_Reproducibility_Package/W10_CleanEnv_Test_Transcript.md",
    "week-10/W10_Reproducibility_Package/data_manifest.json",
    "week-10/W10_Reproducibility_Package/fetch_data.py",
    "week-10/W10_Reproducibility_Package/regenerate_all.py",
    "week-10/W10_Reproducibility_Package/reproduce_fresh.py",
    "week-10/W10_Reproducibility_Package/test_reproduce_fresh.py",
    "week-10/Wk-10-ResearchLog.md",
    "week-10/verify_w10.py",
    "week-11/build_w11_deck.mjs",
)

MIT_LICENSE = """MIT License

Copyright (c) 2026 InGen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

RIGHTS_NOTICE = """# Rights Notice

The MIT License in `LICENSE` applies to the software code in this repository.

Unless an individual file states otherwise, papers, prose, figures, datasets,
model outputs, experiment results, and other research artifacts are not
licensed under the MIT License and remain copyright-controlled by InGen.

Third-party names, model identifiers, citations, software, and dependencies
remain subject to their respective owners' terms.
"""

EXPECTED_BUNDLE = {
    "name": "ingen-raw-evidence-v1.zip",
    "sha256": "950dfb8d0b6958fcbbad7c607940c6f5337eec9864fac07732948b0d81c7bba4",
    "size_bytes": 1653594,
    "availability_note": "Separately supplied; this public repository provides no download location.",
}

EXPECTED_DATA_FILES = {
    "week-06/W06_Raw_Model_Outputs.jsonl": (655555, "267f89874a9b10030916d6cc341a31c67ab99ed0cc4f37c57377b6bca085f12f"),
    "week-06/W06_Judge_Ratings.csv": (394510, "c8e913ef09d8c291370fd6152b358f948bd911937590bdf0ec00ed195cffc113"),
    "week-07/W07_Preflight_Raw_Model_Outputs.jsonl": (389789, "16443b67f28e7c6e631fe95318962192e7e7b260e495a284a80064858e131a40"),
    "week-07/W07_Raw_Model_Outputs.jsonl": (7308850, "d998be244dcc1e91b78aeaea8c3aaa920ee0dff0186e006bd0955756b7594de5"),
    "week-07/W07_Judge_Ratings.csv": (16432178, "0d601af2ca82fe2d9ca6cdec108427bc0c4ffc3e5fede7adaf461fc3c41f79dc"),
    "week-07/W07_Judge_Gold_Ratings.csv": (427827, "a3f19e28adccf3206db279c80a54e67d7b1f1893d50690bb58ec7dc88cac05a3"),
}


class AuditError(RuntimeError):
    """Raised when a public-tree audit check fails."""


@dataclass(frozen=True)
class CommandResult:
    name: str
    argv: tuple[str, ...]
    returncode: int


@dataclass(frozen=True)
class AuditReport:
    file_count: int
    inventory_sha256: str
    commands: tuple[CommandResult, ...]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_inventory_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and "\\" not in value


def parse_inventory(path: Path) -> dict[str, str]:
    inventory: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise AuditError(f"cannot read public inventory: {exc}") from exc
    if not lines:
        raise AuditError("public inventory is empty")
    for number, line in enumerate(lines, 1):
        digest, separator, relative = line.partition("  ")
        if not separator or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise AuditError(f"malformed inventory line {number}")
        if not _safe_inventory_path(relative):
            raise AuditError(f"unsafe inventory path on line {number}")
        if relative == "PUBLIC_INVENTORY.sha256":
            raise AuditError("public inventory must not list itself")
        if relative in inventory:
            raise AuditError(f"duplicate inventory path: {relative}")
        inventory[relative] = digest
    return inventory


def _regular_tree_paths(root: Path) -> set[str]:
    paths: set[str] = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise AuditError(f"symlink found in public tree: {relative}")
        try:
            mode = path.stat().st_mode
        except OSError as exc:
            raise AuditError(f"cannot inspect public path {relative}: {exc}") from exc
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise AuditError(f"non-regular public path: {relative}")
        paths.add(relative)
    return paths


def audit_integrity(root: Path) -> tuple[dict[str, str], str]:
    root = root.resolve(strict=True)
    inventory_path = root / "PUBLIC_INVENTORY.sha256"
    inventory = parse_inventory(inventory_path)
    actual = _regular_tree_paths(root) - {"PUBLIC_INVENTORY.sha256"}
    expected = set(inventory)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise AuditError(f"inventory path mismatch; missing={missing}; unexpected={extra}")
    for relative, expected_hash in inventory.items():
        try:
            actual_hash = sha256_bytes((root / relative).read_bytes())
        except OSError as exc:
            raise AuditError(f"cannot hash public path {relative}: {exc}") from exc
        if actual_hash != expected_hash:
            raise AuditError(f"inventory hash mismatch: {relative}")
    return inventory, sha256_bytes(inventory_path.read_bytes())


def _forbidden_literals() -> tuple[bytes, ...]:
    return (
        b"WEHAVEDNA" + b"/InGen",
        b"gh release" + b" download",
        b"gh auth" + b" login",
        b"private" + b" release",
        b"private" + b"-release",
        b"private" + b" GitHub release",
        b"private" + b"_release_network",
        b"C:" + b"\\Users\\IHAVE",
        b"C:" + b"/Users/IHAVE",
        b"file:" + b"//",
    )


TEXT_SUFFIXES = {"", ".bib", ".csv", ".gitignore", ".json", ".jsonl", ".md", ".mjs", ".ps1", ".py", ".tex", ".txt"}


def scan_public_bytes(root: Path, inventory: dict[str, str]) -> None:
    secret_patterns = (
        re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
        re.compile(rb"ghp_[A-Za-z0-9]{30,}"),
        re.compile(rb"hf_[A-Za-z0-9]{24,}"),
    )
    windows_absolute = re.compile(r"(?i)(?<![A-Za-z0-9])[A-Z]:[\\/](?:Users|Documents and Settings)[\\/]")
    unix_absolute = re.compile(r"(?<![A-Za-z0-9])/(?:home|Users)/[^/\s]+/")
    forbidden = tuple(item.lower() for item in _forbidden_literals())
    for relative in sorted(inventory):
        data = (root / relative).read_bytes()
        folded = data.lower()
        if any(literal in folded for literal in forbidden):
            raise AuditError(f"forbidden private identifier in {relative}")
        if any(pattern.search(data) for pattern in secret_patterns):
            raise AuditError(f"suspected secret in {relative}")
        path = Path(relative)
        suffix = path.suffix.lower() if path.name != ".gitignore" else ".gitignore"
        if suffix not in TEXT_SUFFIXES:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AuditError(f"invalid UTF-8 text file {relative}: {exc}") from exc
        if windows_absolute.search(text) or unix_absolute.search(text):
            raise AuditError(f"absolute workstation path in {relative}")


def verify_markdown_links(root: Path, inventory: dict[str, str]) -> None:
    link_pattern = re.compile(r"\[[^\]]*\]\(([^)\n]+)\)")
    # The Week 11 package's source/ subtree holds verbatim, hash-pinned copies
    # of admitted evidence documents; their relative links target the original
    # repository layout, and rewriting them would break the package manifest.
    verbatim_snapshot_prefix = "week-11/W11_Reproducibility_Package/source/"
    root = root.resolve(strict=True)
    for relative in sorted(
        path
        for path in inventory
        if path.endswith(".md") and not path.startswith(verbatim_snapshot_prefix)
    ):
        text = (root / relative).read_text(encoding="utf-8")
        for match in link_pattern.finditer(text):
            raw_target = match.group(1).strip()
            if raw_target.startswith("<") and ">" in raw_target:
                raw_target = raw_target[1 : raw_target.index(">")]
            else:
                raw_target = raw_target.split(maxsplit=1)[0]
            if not raw_target or raw_target.startswith("#") or re.match(
                r"^(?:https?://|mailto:)", raw_target, re.IGNORECASE
            ):
                continue
            path_text = unquote(raw_target.split("#", 1)[0].split("?", 1)[0])
            if not path_text:
                continue
            target = ((root / relative).parent / path_text).resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise AuditError(
                    f"Markdown link escapes public tree in {relative}: {raw_target}"
                ) from exc
            if not target.exists():
                raise AuditError(f"broken Markdown link in {relative}: {raw_target}")


def _read_json_object(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"invalid {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"invalid {label}: expected object")
    return value


def verify_provenance(root: Path) -> None:
    provenance = _read_json_object(root / "PUBLIC_SNAPSHOT.json", "provenance")
    expected = {
        "deterministic": True,
        "export_manifest_schema": EXPORT_SCHEMA,
        "schema_version": PROVENANCE_SCHEMA,
        "source_commit": SOURCE_COMMIT,
        "transformed_paths": list(TRANSFORMED_PATHS),
    }
    for field, value in expected.items():
        if provenance.get(field) != value:
            raise AuditError(f"provenance field mismatch: {field}")
    timestamp = provenance.get("source_commit_timestamp")
    if not isinstance(timestamp, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}", timestamp):
        raise AuditError("provenance field mismatch: source_commit_timestamp")
    if set(provenance) != set(expected) | {"source_commit_timestamp"}:
        raise AuditError("provenance contains unexpected fields")


def verify_legal_notices(root: Path) -> None:
    try:
        license_text = (root / "LICENSE").read_text(encoding="utf-8")
        rights_text = (root / "RIGHTS-NOTICE.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AuditError(f"cannot read license or rights notice: {exc}") from exc
    if license_text != MIT_LICENSE:
        raise AuditError("license does not match the approved MIT grant")
    if rights_text != RIGHTS_NOTICE:
        raise AuditError("rights notice does not match the approved research boundary")


def verify_local_bundle_contract(root: Path) -> None:
    manifest = _read_json_object(root / DATA_MANIFEST, "bundle manifest")
    if set(manifest) != {"schema_version", "bundle", "unbundled_note", "files"}:
        raise AuditError("bundle manifest has unexpected top-level fields")
    if manifest.get("schema_version") != DATA_SCHEMA or manifest.get("bundle") != EXPECTED_BUNDLE:
        raise AuditError("bundle manifest identity mismatch")
    records = manifest.get("files")
    if not isinstance(records, list) or len(records) != len(EXPECTED_DATA_FILES):
        raise AuditError("bundle manifest file list mismatch")
    found: dict[str, tuple[int, str]] = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {"name", "path", "sha256", "size_bytes"}:
            raise AuditError("bundle manifest file record is malformed")
        relative = record.get("path")
        if not isinstance(relative, str) or not _safe_inventory_path(relative):
            raise AuditError("bundle manifest path is unsafe")
        if record.get("name") != PurePosixPath(relative).name:
            raise AuditError(f"bundle manifest name mismatch: {relative}")
        size = record.get("size_bytes")
        digest = record.get("sha256")
        if not isinstance(size, int) or not isinstance(digest, str):
            raise AuditError(f"bundle manifest metadata is malformed: {relative}")
        if relative in found:
            raise AuditError(f"bundle manifest path is duplicated: {relative}")
        found[relative] = (size, digest)
    if found != EXPECTED_DATA_FILES:
        raise AuditError("bundle manifest file metadata mismatch")

    fetch_path = root / FETCH
    try:
        tree = ast.parse(fetch_path.read_text(encoding="utf-8"), filename=str(FETCH))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise AuditError(f"invalid local bundle restorer: {exc}") from exc
    forbidden_imports = {"http", "requests", "socket", "subprocess", "urllib"}
    for node in ast.walk(tree):
        names: tuple[str, ...] = ()
        if isinstance(node, ast.Import):
            names = tuple(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = (node.module.split(".", 1)[0],)
        if forbidden_imports.intersection(names):
            raise AuditError("bundle restorer imports a network-capable module")

    env = os.environ.copy()
    env.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PIP_NO_INDEX": "1",
        }
    )
    try:
        no_argument = subprocess.run(
            (sys.executable, str(fetch_path)),
            cwd=root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=60,
        )
        check = subprocess.run(
            (sys.executable, str(fetch_path), "--check"),
            cwd=root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AuditError(f"bundle restorer could not be exercised: {exc}") from exc
    if no_argument.returncode == 0 or "--from-path" not in no_argument.stdout:
        raise AuditError("bundle restorer does not require an explicit local bundle")
    if check.returncode != 0:
        missing = {
            match.group(1)
            for match in re.finditer(r"MISSING\s+(week-[^\s]+)", check.stdout)
        }
        if missing != set(EXPECTED_DATA_FILES):
            raise AuditError(f"bundle restorer --check failed: {check.stdout.strip()}")


def _verify_pdf(path: Path) -> None:
    data = path.read_bytes()
    if not data.startswith(b"%PDF-") or not data.rstrip().endswith(b"%%EOF"):
        raise AuditError(f"PDF structure is invalid: {path.name}")
    matches = list(re.finditer(rb"startxref\s+(\d+)\s+%%EOF", data[-2048:]))
    if not matches:
        raise AuditError(f"PDF startxref is missing: {path.name}")
    offset = int(matches[-1].group(1))
    if offset <= 0 or offset >= len(data):
        raise AuditError(f"PDF startxref is invalid: {path.name}")
    target = data[offset : offset + 512]
    compact = re.sub(rb"\s+", b"", target)
    if not (target.startswith(b"xref") or b"/Type/XRef" in compact):
        raise AuditError(f"PDF cross-reference is invalid: {path.name}")


def verify_document_structure(root: Path) -> None:
    pairs = (
        ("week-09/W09_Paper_Draft_v1_IEEE.tex", "output/pdf/W09_Paper_Draft_v1_IEEE.pdf"),
        ("week-10/W10_Paper_Draft_v2_IEEE.tex", "output/pdf/W10_Paper_Draft_v2_IEEE.pdf"),
        ("week-11/W11_Capstone_Report.tex", "week-11/W11_Capstone_Report.pdf"),
        (
            "week-11/W11_Reproducibility_Package/artifacts/report/Capstone_Report.tex",
            "week-11/W11_Reproducibility_Package/artifacts/report/Capstone_Report.pdf",
        ),
    )
    for tex_relative, pdf_relative in pairs:
        try:
            tex = (root / tex_relative).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise AuditError(f"cannot read TeX source {tex_relative}: {exc}") from exc
        if "\\documentclass" not in tex or "\\begin{document}" not in tex or "\\end{document}" not in tex:
            raise AuditError(f"TeX structure is invalid: {tex_relative}")
        _verify_pdf(root / pdf_relative)


def _run_checked(
    name: str,
    argv: tuple[str, ...],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: int = 600,
) -> tuple[CommandResult, str]:
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AuditError(f"public command {name} could not complete: {exc}") from exc
    if completed.returncode != 0:
        tail = "\n".join(completed.stdout.splitlines()[-40:])
        raise AuditError(
            f"public command {name} failed with exit {completed.returncode}:\n{tail}"
        )
    return CommandResult(name, argv, completed.returncode), completed.stdout


def _git_checked(argv: tuple[str, ...], *, cwd: Path, env: dict[str, str]) -> None:
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AuditError(f"temporary Git harness setup failed: {exc}") from exc
    if completed.returncode != 0:
        raise AuditError(
            f"temporary Git harness setup failed for {' '.join(argv)}: {completed.stdout.strip()}"
        )


def _prepare_git_harness(harness: Path, env: dict[str, str]) -> None:
    _git_checked(("git", "init", "-b", "main"), cwd=harness, env=env)
    _git_checked(("git", "config", "user.name", "Public Snapshot Audit"), cwd=harness, env=env)
    _git_checked(
        ("git", "config", "user.email", "audit@example.invalid"), cwd=harness, env=env
    )
    _git_checked(("git", "config", "core.autocrlf", "false"), cwd=harness, env=env)
    _git_checked(("git", "add", "--all"), cwd=harness, env=env)
    _git_checked(
        ("git", "commit", "-m", "Create disposable public audit harness"),
        cwd=harness,
        env=env,
    )


def _verify_plan_output(output: str) -> None:
    try:
        plan = json.loads(output)
    except json.JSONDecodeError as exc:
        raise AuditError(f"reproduction plan did not emit JSON: {exc}") from exc
    stages = plan.get("stages") if isinstance(plan, dict) else None
    if plan.get("mode") != "plan" or not isinstance(stages, list) or len(stages) != 25:
        raise AuditError("reproduction plan does not contain the expected 25 stages")
    names = [stage.get("name") for stage in stages if isinstance(stage, dict)]
    if len(names) != 25 or len(set(names)) != 25:
        raise AuditError("reproduction plan stage names are missing or duplicated")


def _verify_mock_receipt(run_dir: Path) -> None:
    receipt = _read_json_object(run_dir / "run-receipt.json", "offline mock receipt")
    stages = receipt.get("stages")
    if receipt.get("mode") != "mock" or receipt.get("status") != "mock_only":
        raise AuditError("offline mock receipt does not end in mock_only")
    if not isinstance(stages, list) or len(stages) != 11:
        raise AuditError("offline mock receipt does not contain the expected 11 stages")
    if any(not isinstance(stage, dict) or stage.get("returncode") != 0 for stage in stages):
        raise AuditError("offline mock receipt contains a failed stage")
    if "protocol_inputs" in receipt or "protocol_restore" in receipt:
        raise AuditError("offline mock receipt unexpectedly records protocol data")


def run_public_commands(root: Path) -> tuple[CommandResult, ...]:
    with tempfile.TemporaryDirectory(prefix="ingen-public-audit-") as temporary:
        temporary_root = Path(temporary)
        harness = temporary_root / "repo"
        runtime = temporary_root / "runtime"
        runtime.mkdir()
        shutil.copytree(root, harness)
        env = os.environ.copy()
        env.update(
            {
                "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1",
                "PIP_NO_INDEX": "1",
                "HF_HUB_DISABLE_TELEMETRY": "1",
                "TOKENIZERS_PARALLELISM": "false",
                "TMP": str(runtime),
                "TEMP": str(runtime),
                "PYTHONPYCACHEPREFIX": str(runtime / "pycache"),
                "MPLCONFIGDIR": str(runtime / "mplconfig"),
            }
        )
        _prepare_git_harness(harness, env)
        (harness / "tmp").mkdir(exist_ok=True)
        python = sys.executable
        reproduction = "week-10/W10_Reproducibility_Package/reproduce_fresh.py"
        commands: list[CommandResult] = []

        result, _ = _run_checked(
            "week10", (python, "week-10/verify_w10.py"), cwd=harness, env=env
        )
        commands.append(result)
        result, _ = _run_checked(
            "package_tests",
            (
                python,
                "-m",
                "unittest",
                "discover",
                "-s",
                "week-10/W10_Reproducibility_Package",
                "-p",
                "test_*.py",
            ),
            cwd=harness,
            env=env,
        )
        commands.append(result)
        result, _ = _run_checked(
            "w11_verify_package",
            (python, "week-11/W11_Reproducibility_Package/verify_package.py"),
            cwd=harness,
            env=env,
        )
        commands.append(result)
        result, _ = _run_checked(
            "w11_acceptance",
            (
                python,
                "week-11/W11_Reproducibility_Package/run_acceptance.py",
                "--model-policy",
                "allow-missing",
            ),
            cwd=harness,
            env=env,
        )
        commands.append(result)
        python_paths = tuple(
            sorted(
                path.relative_to(harness).as_posix()
                for path in harness.rglob("*.py")
                if ".git" not in path.parts
            )
        )
        result, _ = _run_checked(
            "py_compile", (python, "-m", "py_compile", *python_paths), cwd=harness, env=env
        )
        commands.append(result)
        plan_dir = temporary_root / "plan-output"
        result, output = _run_checked(
            "reproduction_plan",
            (python, reproduction, "--mode", "plan", "--run-dir", str(plan_dir)),
            cwd=harness,
            env=env,
        )
        _verify_plan_output(output)
        commands.append(result)

        mock_dir = harness / ".reproduction-runs" / "audit-mock"
        mock_error: BaseException | None = None
        try:
            result, _ = _run_checked(
                "offline_mock",
                (python, reproduction, "--mode", "mock", "--run-dir", str(mock_dir)),
                cwd=harness,
                env=env,
            )
            _verify_mock_receipt(mock_dir)
            commands.append(result)
        except BaseException as exc:
            mock_error = exc
        finally:
            if mock_dir.exists():
                cleanup = subprocess.run(
                    ("git", "worktree", "remove", "--force", str(mock_dir)),
                    cwd=harness,
                    env=env,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
                if cleanup.returncode != 0 and mock_error is None:
                    mock_error = AuditError(
                        f"offline mock worktree cleanup failed: {cleanup.stdout.strip()}"
                    )
            subprocess.run(
                ("git", "worktree", "prune"),
                cwd=harness,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        if mock_error is not None:
            raise mock_error
        return tuple(commands)


def audit_tree(root: Path, *, run_commands: bool = True) -> AuditReport:
    root = root.resolve(strict=True)
    inventory, inventory_digest = audit_integrity(root)
    scan_public_bytes(root, inventory)
    verify_markdown_links(root, inventory)
    verify_provenance(root)
    verify_legal_notices(root)
    verify_local_bundle_contract(root)
    verify_document_structure(root)
    commands = run_public_commands(root) if run_commands else ()
    return AuditReport(len(inventory), inventory_digest, commands)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--skip-commands", action="store_true")
    args = parser.parse_args()
    try:
        report = audit_tree(args.root, run_commands=not args.skip_commands)
    except (AuditError, OSError) as exc:
        raise SystemExit(f"FAIL: {exc}") from exc
    print(f"PASS: audited {report.file_count} public files; inventory sha256 {report.inventory_sha256}; commands {len(report.commands)}")


if __name__ == "__main__":
    main()
