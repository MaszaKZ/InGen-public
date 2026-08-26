from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parent
MANIFEST = PACKAGE / "package_manifest.json"
ANALYSIS = PACKAGE / "analysis"
sys.path.insert(0, str(ANALYSIS))

from evidence import common_baseline_rows, load_evidence, mitigation_rows, stress_rows  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path = MANIFEST) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "ingen-final-package-manifest-v1":
        raise ValueError("unsupported package manifest schema")
    entries = payload.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("package manifest has no file entries")
    return payload


def _permitted_untracked(relative: str) -> bool:
    return (
        relative == "package_manifest.json"
        or relative.startswith("generated-receipts/")
        or relative.startswith("regenerated-figures/")
        or (
            relative.startswith("models/huggingface/hub/")
            and relative != "models/huggingface/hub/PUT_MODELS_HERE.txt"
        )
        or "/__pycache__/" in f"/{relative}"
        or relative.endswith(".pyc")
    )


def verify_manifest() -> dict[str, Any]:
    manifest = load_manifest()
    expected: dict[str, dict[str, Any]] = {}
    for entry in manifest["files"]:
        relative = str(entry["path"])
        if relative in expected or relative.startswith("/") or ".." in Path(relative).parts:
            raise ValueError(f"unsafe or duplicate manifest path: {relative}")
        expected[relative] = entry

    actual = {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file()
    }
    missing = sorted(set(expected) - actual)
    unexpected = sorted(
        relative
        for relative in actual - set(expected)
        if not _permitted_untracked(relative)
    )
    mismatches: list[dict[str, Any]] = []
    for relative, entry in expected.items():
        path = PACKAGE / relative
        if not path.is_file():
            continue
        size = path.stat().st_size
        digest = sha256(path)
        if size != int(entry["size_bytes"]) or digest != str(entry["sha256"]):
            mismatches.append(
                {
                    "path": relative,
                    "expected_size": int(entry["size_bytes"]),
                    "actual_size": size,
                    "expected_sha256": str(entry["sha256"]),
                    "actual_sha256": digest,
                }
            )
    if missing or unexpected or mismatches:
        raise ValueError(
            json.dumps(
                {"missing": missing, "unexpected": unexpected, "mismatches": mismatches},
                sort_keys=True,
            )
        )
    return {"files": len(expected), "bytes": sum(int(row["size_bytes"]) for row in expected.values())}


def _csv_rows(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _text_lines(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def verify_evidence() -> dict[str, Any]:
    evidence = load_evidence(PACKAGE / "source")
    contrasts = common_baseline_rows(evidence)
    observed = [(row["subtype"], row["estimate_pp"], row["ci_pp"]) for row in contrasts]
    expected = [
        ("plain", -55.0, [-77.5, -32.5]),
        ("pressured", -40.1, [-55.3, -26.0]),
        ("control", 18.8, [6.2, 34.4]),
    ]
    if observed != expected:
        raise ValueError(f"headline contrasts changed: {observed!r}")

    stress = {row["endpoint"]: row["stressed_pp"] for row in stress_rows(evidence)}
    if stress != {"plain": -25.6, "pressured": -35.0, "control": 18.1}:
        raise ValueError(f"stress estimates changed: {stress!r}")

    passes = [
        row
        for row in mitigation_rows(evidence)
        if row["observed_pass"]
    ]
    if len(passes) != 1 or passes[0]["model"] != "Qwen2.5-7B-Instruct" or passes[0]["condition"] != "Deliberation" or passes[0]["combined_stress_pass"]:
        raise ValueError(f"mitigation disposition changed: {passes!r}")

    raw_counts = {
        "diagnostic_raw_outputs": _text_lines(PACKAGE / "source/week-06/W06_Raw_Model_Outputs.snapshot.jsonl"),
        "diagnostic_judge_rows": _csv_rows(PACKAGE / "source/week-06/W06_Judge_Ratings.csv"),
        "confirmation_raw_outputs": _text_lines(PACKAGE / "source/week-07/W07_Raw_Model_Outputs.snapshot.jsonl"),
        "confirmation_judge_rows": _csv_rows(PACKAGE / "source/week-07/W07_Judge_Ratings.csv"),
    }
    if raw_counts != {
        "diagnostic_raw_outputs": 384,
        "diagnostic_judge_rows": 384,
        "confirmation_raw_outputs": 4800,
        "confirmation_judge_rows": 14400,
    }:
        raise ValueError(f"raw evidence counts changed: {raw_counts!r}")
    return {"contrasts": observed, "stress": stress, "raw_counts": raw_counts}


def verify_artifacts() -> dict[str, Any]:
    report_pdf = PACKAGE / "artifacts/report/Capstone_Report.pdf"
    report_tex = PACKAGE / "artifacts/report/Capstone_Report.tex"
    deck = PACKAGE / "artifacts/slides/Research_Review_Deck.pptx"
    if not report_pdf.read_bytes().startswith(b"%PDF-"):
        raise ValueError("capstone PDF signature is invalid")
    source = report_tex.read_text(encoding="utf-8")
    for banned in ("feedback", "superseded", "TODO", "Week 11", "behaviour", "authorisation"):
        if banned in source:
            raise ValueError(f"report contains banned text: {banned}")
    for relative in re.findall(r"figures/(W11_[A-Za-z0-9_]+\.pdf)", source):
        if not (report_tex.parent / "figures" / relative).is_file():
            raise ValueError(f"report-local figure is missing: {relative}")
    with zipfile.ZipFile(deck) as archive:
        slides = [
            name
            for name in archive.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        ]
        notes = [
            name
            for name in archive.namelist()
            if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
        ]
        if len(slides) != 14 or len(notes) != 14:
            raise ValueError(f"deck structure changed: {len(slides)} slides, {len(notes)} notes")
        if not all(b"[Sources]" in archive.read(name) for name in notes):
            raise ValueError("one or more deck slides lacks a [Sources] note block")
    return {
        "report_sha256": sha256(report_pdf),
        "deck_sha256": sha256(deck),
        "slides": 10,
    }


def verify_runtime_provenance() -> dict[str, Any]:
    active = (
        PACKAGE / "run_minimal_pipeline_smoke.py",
        PACKAGE / "source/week-07/run_w07_replication.py",
        PACKAGE / "source/week-07/judge_w07_replication.py",
        PACKAGE / "source/week-07/analyze_w07.py",
    )
    problems: list[str] = []
    for path in active:
        source = path.read_text(encoding="utf-8")
        if ".conda-w01" in source:
            problems.append(f"{path.name}: superseded interpreter path")
        if "runtime_command(" not in source and "record_runtime_command(" not in source:
            problems.append(f"{path.name}: actual runtime command is not recorded")
    if problems:
        raise ValueError("; ".join(problems))
    return {"active_scripts": len(active)}


def verify_all() -> dict[str, Any]:
    return {
        "manifest": verify_manifest(),
        "evidence": verify_evidence(),
        "artifacts": verify_artifacts(),
        "runtime_provenance": verify_runtime_provenance(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the standalone research package.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = verify_all()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"status": "pass", **result}, indent=2, sort_keys=True))
    else:
        print("PASS: package manifest, evidence, and artifacts verified")
        print(f"files: {result['manifest']['files']}")
        print(f"bytes: {result['manifest']['bytes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
