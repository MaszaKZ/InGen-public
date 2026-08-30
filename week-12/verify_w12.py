from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zlib
from collections.abc import Sequence
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "week-11" / "W11_Reproducibility_Package"
TEMP_ROOT = ROOT / "tmp" / "w12-verifier"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def notebook_paths(package: Path) -> Sequence[Path]:
    relative = (
        "source/week-04/W04_Extended_Benchmark.ipynb",
        "source/week-05/W05_Experiment_Notebook.ipynb",
        "source/week-06/W06_Experiment2_Notebook.ipynb",
        "source/week-07/W07_Analysis_Notebook.ipynb",
    )
    paths = tuple(package / item for item in relative)
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing packaged notebooks: {missing}")
    return paths


def _pdf_object_corpus(data: bytes) -> bytes:
    segments = [data]
    for match in re.finditer(rb"stream\r?\n", data):
        start = match.end()
        end = data.find(b"endstream", start)
        if end == -1:
            continue
        try:
            segments.append(zlib.decompress(data[start:end].rstrip(b"\r\n")))
        except zlib.error:
            continue
    return b"".join(segments)


def verify_pdf(pdf: Path) -> dict[str, int]:
    if not pdf.is_file():
        raise FileNotFoundError(pdf)
    corpus = _pdf_object_corpus(pdf.read_bytes())
    pages = len(re.findall(rb"/Type\s*/Page\b", corpus))
    if not 10 <= pages <= 12:
        raise RuntimeError(f"paper page count outside 10-12: {pages}")

    titles = []
    for hex_string in re.findall(rb"/Title\s*<([0-9a-fA-F]+)>", corpus):
        try:
            titles.append(bytes.fromhex(hex_string.decode("ascii")).decode("utf-16-be"))
        except (ValueError, UnicodeDecodeError):
            continue
    titles.extend(
        literal.decode("latin-1")
        for literal in re.findall(rb"/Title\s*\(([^)]*)\)", corpus)
    )
    if not any(
        "Generator Choice Sets the Safety Operating Point" in title for title in titles
    ):
        raise RuntimeError("paper PDF metadata title is missing or incorrect")
    if pdf.stat().st_size < 100_000:
        raise RuntimeError("paper PDF is unexpectedly small")
    return {"pages": pages, "title_entries": len(titles)}


def _kernel_environment(output_dir: Path, python: Path, package: Path) -> dict[str, str]:
    runtime = output_dir / "runtime"
    config = output_dir / "config"
    ipython = output_dir / "ipython"
    matplotlib = output_dir / "matplotlib"
    kernel_dir = output_dir / "kernels" / "w12-verify"
    for path in (runtime, config, ipython, matplotlib, kernel_dir):
        path.mkdir(parents=True, exist_ok=True)
    kernel = {
        "argv": [str(python), "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "Week 12 verification",
        "language": "python",
    }
    (kernel_dir / "kernel.json").write_text(
        json.dumps(kernel, indent=2) + "\n", encoding="utf-8"
    )

    env = os.environ.copy()
    env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUTF8": "1",
            "JUPYTER_ALLOW_INSECURE_WRITES": "1",
            "JUPYTER_RUNTIME_DIR": str(runtime),
            "JUPYTER_CONFIG_DIR": str(config),
            "JUPYTER_PATH": str(output_dir),
            "IPYTHONDIR": str(ipython),
            "MPLCONFIGDIR": str(matplotlib),
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_HOME": str(package / "models" / "huggingface"),
            "HF_HUB_CACHE": str(package / "models" / "huggingface" / "hub"),
            "TEMP": str(output_dir),
            "TMP": str(output_dir),
            "TMPDIR": str(output_dir),
        }
    )
    return env


def run_notebook(notebook: Path, output_dir: Path, python: Path) -> Path:
    notebook = notebook.resolve()
    output_dir = output_dir.resolve()
    package = notebook.parents[2]
    before = sha256(notebook)
    destination = output_dir / f"{notebook.stem}.executed.ipynb"
    env = _kernel_environment(output_dir, python.resolve(), package)
    workspace = output_dir / "workspaces" / f"{notebook.stem}-{before[:12]}"
    isolated_source = workspace / "source"
    shutil.copytree(package / "source", isolated_source, dirs_exist_ok=True)
    figure_source = package.parents[1] / "week-07" / "figures"
    figure_target = isolated_source / "week-07" / "figures"
    figure_target.mkdir(parents=True, exist_ok=True)
    for name in (
        "W07_Figure1_Common_Baseline_Cross_Model.png",
        "W07_Figure2_Prompt_Safety_and_Control_Cost.png",
        "W07_Figure3_Seed_Variability_and_Judge_Agreement.png",
    ):
        shutil.copy2(figure_source / name, figure_target / name)
    isolated_notebook = isolated_source / notebook.relative_to(package / "source")
    command = [
        str(python.resolve()),
        "-m",
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        "--ExecutePreprocessor.timeout=300",
        "--ExecutePreprocessor.kernel_name=w12-verify",
        "--output",
        destination.name,
        "--output-dir",
        str(output_dir),
        str(isolated_notebook),
    ]
    completed = subprocess.run(
        command,
        cwd=isolated_source,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        raise RuntimeError(
            f"notebook execution failed ({completed.returncode}): {notebook.name}"
        )
    if sha256(notebook) != before:
        raise RuntimeError(f"source notebook changed during execution: {notebook}")
    if not destination.is_file():
        raise FileNotFoundError(destination)

    executed = json.loads(destination.read_text(encoding="utf-8"))
    errors = [
        output
        for cell in executed.get("cells", [])
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]
    if errors:
        raise RuntimeError(f"executed notebook contains errors: {notebook.name}")
    return destination


def run(label: str, command: list[str], env: dict[str, str]) -> None:
    print(f"\n== {label} ==", flush=True)
    print(" ".join(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"{label} failed with exit code {completed.returncode}")
    print(f"PASS: {label}", flush=True)


def main() -> int:
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUTF8": "1",
            "TEMP": str(TEMP_ROOT),
            "TMP": str(TEMP_ROOT),
            "TMPDIR": str(TEMP_ROOT),
        }
    )

    run(
        "Week 12 acceptance contract",
        [sys.executable, "-m", "unittest", "week-12/test_w12.py", "-v"],
        env,
    )
    run(
        "Week 11 admitted-evidence verifier",
        [sys.executable, "week-11/verify_w11.py"],
        env,
    )

    pdf_result = verify_pdf(ROOT / "week-12" / "W12_Final_Paper.pdf")
    print(
        f"PASS: paper PDF ({pdf_result['pages']} pages; "
        f"metadata title verified without external PDF tools)",
        flush=True,
    )

    notebook_output = TEMP_ROOT / "notebook-execution"
    source_hashes = {path: sha256(path) for path in notebook_paths(PACKAGE)}
    for notebook in notebook_paths(PACKAGE):
        executed = run_notebook(notebook, notebook_output, Path(sys.executable))
        print(f"PASS: {notebook.name} -> {executed.name}", flush=True)
    for path, expected_hash in source_hashes.items():
        if sha256(path) != expected_hash:
            raise RuntimeError(f"packaged notebook hash changed: {path}")

    print("\nW12 VERIFICATION PASSED", flush=True)
    print(
        "Week 12 artifacts, four isolated notebooks, and the retained Week 11 "
        "evidence base are consistent.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
