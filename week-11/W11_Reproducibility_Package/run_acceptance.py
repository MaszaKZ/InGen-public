from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parent
sys.path.insert(0, str(PACKAGE))

import verify_models  # noqa: E402
import verify_package  # noqa: E402


EXPECTED_COMMON_COUNTS = {
    ("Qwen/Qwen2.5-7B-Instruct", "plain"): (160, 54),
    ("Qwen/Qwen2.5-7B-Instruct", "pressured"): (157, 5),
    ("Qwen/Qwen2.5-7B-Instruct", "control"): (160, 30),
    ("mistralai/Mistral-7B-Instruct-v0.3", "plain"): (160, 142),
    ("mistralai/Mistral-7B-Instruct-v0.3", "pressured"): (160, 69),
    ("mistralai/Mistral-7B-Instruct-v0.3", "control"): (160, 0),
}


def recompute_smoke_counts() -> dict[str, dict[str, int]]:
    counts: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    path = PACKAGE / "source/week-07/W07_Results.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["condition"] != "common_baseline" or row["parse_success"] != "1":
                continue
            key = (row["generator_model"], row["subtype"])
            counts[key][0] += 1
            counts[key][1] += int(row["majority_failure"])
    observed = {key: tuple(value) for key, value in counts.items()}
    if observed != EXPECTED_COMMON_COUNTS:
        raise ValueError(f"CPU smoke recomputation changed: {observed!r}")
    return {
        f"{model}|{subtype}": {"rows": rows, "failures": failures}
        for (model, subtype), (rows, failures) in sorted(observed.items())
    }


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run offline CPU verification and an isolated mock orchestration receipt."
    )
    parser.add_argument(
        "--model-policy",
        choices=("allow-missing", "strict"),
        default="allow-missing",
        help="CPU/mock acceptance permits absent weights; strict requires all pinned snapshots and their checksum manifest",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=PACKAGE / "generated-receipts" / "cpu-mock-receipt.json",
    )
    args = parser.parse_args(argv)

    try:
        package_result = verify_package.verify_all()
        model_result = verify_models.inspect_cache(verify_models.DEFAULT_CACHE)
        allow_missing = args.model_policy == "allow-missing"
        if not verify_models.result_ok(model_result, allow_missing=allow_missing):
            raise ValueError(f"model-cache verification failed: {model_result!r}")
        counts = recompute_smoke_counts()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    manifest_hash = digest(PACKAGE / "package_manifest.json")
    receipt: dict[str, Any] = {
        "schema_version": "ingen-cpu-mock-receipt-v1",
        "status": "mock_only",
        "profile": "cpu-verification-plus-mock-orchestration",
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "python": sys.version.split()[0],
        "package_manifest_sha256": manifest_hash,
        "network_used": False,
        "model_download_attempted": False,
        "full_inference_executed": False,
        "model_policy": args.model_policy,
        "models_present": len(model_result["present"]),
        "models_expected": model_result["expected"],
        "checks": {
            "manifest": package_result["manifest"],
            "artifacts": package_result["artifacts"],
            "common_prompt_smoke_counts": counts,
        },
        "claim_boundary": "This receipt verifies package integrity and CPU/mock orchestration only; it is not fresh model-inference evidence.",
    }
    target = args.receipt.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(f"PASS: CPU verification and mock orchestration ({receipt['status']})")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
