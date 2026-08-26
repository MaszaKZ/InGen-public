"""Run the smallest supported GPU path through generation, judging, and aggregation."""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


PACKAGE = Path(__file__).resolve().parent
DEFAULT_CACHE = PACKAGE / "models" / "huggingface" / "hub"
GENERATORS = ("mistral", "qwen")
JUDGES = ("granite8b", "phi4_14b", "falcon3_10b")
CONDITION = "common_baseline"
GENERATION_MAX_NEW_TOKENS = 64
ACTIVE_MODEL_IDS = (
    "mistralai/Mistral-7B-Instruct-v0.3",
    "Qwen/Qwen2.5-7B-Instruct",
    "ibm-granite/granite-3.3-8b-instruct",
    "microsoft/phi-4",
    "tiiuae/Falcon3-10B-Instruct",
)


def timestamped_output_directory() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return PACKAGE / "generated-receipts" / f"minimal-full-pipeline-smoke-{stamp}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one scenario through both active generators, all three active "
            "judges, and panel aggregation without changing registered results."
        )
    )
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--checksum-manifest",
        type=Path,
        help=(
            "Optional model-checksums.json produced by verify_models.py; the "
            "active pinned snapshots are always checked structurally."
        ),
    )
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Print the fixed execution scope without loading models or writing output.",
    )
    return parser.parse_args(argv)


def build_plan(cache_dir: Path, output_dir: Path) -> dict[str, object]:
    return {
        "verification_level": "minimal_full_pipeline_smoke",
        "condition": CONDITION,
        "scenario_count": 1,
        "generators": list(GENERATORS),
        "judges": list(JUDGES),
        "expected_rows": {
            "generations": 2,
            "judgments": 6,
            "panels": 2,
        },
        "generation_max_new_tokens": GENERATION_MAX_NEW_TOKENS,
        "cache_dir": str(cache_dir.resolve()),
        "output_dir": str(output_dir.resolve()),
    }


def configure_offline_cache(cache_dir: Path) -> None:
    cache_dir = cache_dir.resolve()
    os.environ["HF_HOME"] = str(cache_dir.parent if cache_dir.name == "hub" else cache_dir)
    os.environ["HF_HUB_CACHE"] = str(cache_dir)
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(cache_dir)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"


def validate_pipeline_rows(
    generations: list[dict[str, Any]],
    judgments: list[dict[str, Any]],
    panels: list[dict[str, Any]],
    *,
    expected_generators: set[tuple[str, str]],
    expected_judges: dict[str, tuple[str, str]],
) -> dict[str, int]:
    counts = {
        "generations": len(generations),
        "judgments": len(judgments),
        "panels": len(panels),
    }
    if counts != {"generations": 2, "judgments": 6, "panels": 2}:
        raise AssertionError(f"expected the 2/6/2 row product, found {counts}")

    observed_generators = {
        (str(row.get("generator_model")), str(row.get("generator_revision")))
        for row in generations
    }
    if observed_generators != expected_generators:
        raise AssertionError("generation rows do not match the pinned active generators")
    if any(row.get("condition") != CONDITION for row in generations):
        raise AssertionError(f"all generation rows must use {CONDITION}")
    scenario_seed = {
        (str(row.get("scenario_id")), int(row.get("seed", -1)))
        for row in generations
    }
    if len(scenario_seed) != 1:
        raise AssertionError("generation rows must share one scenario and one seed")
    if any(not str(row.get("response", "")).strip() for row in generations):
        raise AssertionError("generation responses must be nonblank")

    response_ids = [str(row.get("response_id", "")) for row in generations]
    if not all(response_ids) or len(set(response_ids)) != 2:
        raise AssertionError("generation response IDs must be nonblank and unique")
    expected_pairs = {
        (response_id, judge_name)
        for response_id in response_ids
        for judge_name in expected_judges
    }
    observed_pairs = {
        (str(row.get("response_id", "")), str(row.get("judge_name", "")))
        for row in judgments
    }
    if observed_pairs != expected_pairs or len(observed_pairs) != len(judgments):
        raise AssertionError("judgments do not form the complete response-by-judge product")
    for row in judgments:
        name = str(row.get("judge_name", ""))
        identity = (str(row.get("judge_model", "")), str(row.get("judge_revision", "")))
        if name not in expected_judges or identity != expected_judges[name]:
            raise AssertionError("judgment rows do not match the pinned active judges")
    if sum(int(row.get("parse_success", 0)) for row in judgments) != 6:
        raise AssertionError("expected six parsed judgments")

    panel_ids = [str(row.get("response_id", "")) for row in panels]
    if set(panel_ids) != set(response_ids) or len(set(panel_ids)) != len(panel_ids):
        raise AssertionError("panel rows must contain one result per response")
    if sum(int(row.get("parse_success", 0)) for row in panels) != 2:
        raise AssertionError("expected two parsed panel rows")
    return counts


def prepare_output_directory(output_dir: Path) -> Path:
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"output directory already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    return output_dir


def summarize_generation_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "nonblank_rows": sum(bool(str(row.get("response", "")).strip()) for row in rows),
        "rows_at_token_cap": sum(bool(row.get("hit_max_new_tokens")) for row in rows),
        "generated_token_counts": [
            int(row.get("generated_token_count", 0)) for row in rows
        ],
    }


def orchestrate_minimal_pipeline(
    generate_stage: Callable[[], tuple[list[dict[str, Any]], dict[str, Any]]],
    judge_stage: Callable[
        [str, list[dict[str, Any]]],
        tuple[list[dict[str, Any]], dict[str, Any]],
    ],
    aggregate_stage: Callable[
        [list[dict[str, Any]], list[dict[str, Any]]], list[dict[str, Any]]
    ],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    generations, generation_metadata = generate_stage()
    ratings: list[dict[str, Any]] = []
    judge_metadata: dict[str, Any] = {}
    for name in JUDGES:
        rows, metadata = judge_stage(name, generations)
        ratings.extend(rows)
        judge_metadata[name] = metadata
    panels = aggregate_stage(generations, ratings)
    return generations, ratings, panels, {
        "generation": generation_metadata,
        "judges": judge_metadata,
    }


def runtime_command(argv: list[str] | None = None) -> str:
    return subprocess.list2cmdline([sys.executable, *(sys.argv if argv is None else argv)])


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write an empty CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def verify_active_model_cache(
    cache_dir: Path, checksum_manifest: Path | None = None
) -> dict[str, Any]:
    import verify_models

    cache_dir = cache_dir.resolve()
    lock = verify_models.load_lock()
    problems: list[str] = []
    snapshots: list[dict[str, str]] = []
    for repo_id in ACTIVE_MODEL_IDS:
        revision = str(lock["models"][repo_id]["revision"])
        snapshot = (
            cache_dir
            / verify_models.cache_directory(repo_id)
            / "snapshots"
            / revision
        )
        if not snapshot.is_dir():
            problems.append(f"missing {repo_id}@{revision}")
            continue
        snapshot_problems = verify_models.snapshot_problems(snapshot)
        if snapshot_problems:
            problems.append(f"{repo_id}@{revision}: {', '.join(snapshot_problems)}")
            continue
        snapshots.append({"repo_id": repo_id, "revision": revision})
    if problems:
        raise RuntimeError("active model cache is incomplete: " + "; ".join(problems))

    checksum_status: dict[str, Any] = {"status": "not_supplied"}
    if checksum_manifest is not None:
        checksum_status = verify_models.verify_checksum_manifest(
            cache_dir, checksum_manifest, lock
        )
        if checksum_status.get("status") != "pass":
            raise RuntimeError(
                "model checksum verification failed: " + json.dumps(checksum_status)
            )
    return {
        "cache_dir": str(cache_dir),
        "active_snapshots": snapshots,
        "checksum_manifest": checksum_status,
    }


def load_week7_modules():
    week7 = PACKAGE / "source" / "week-07"
    sys.path.insert(0, str(week7))
    common = importlib.import_module("w07_common")
    generator = importlib.import_module("run_w07_replication")
    judge = importlib.import_module("judge_w07_replication")
    return common, generator, judge


def cuda_peak_bytes(torch_module) -> int:
    return int(torch_module.cuda.max_memory_allocated())


def run_gpu_pipeline(output_dir: Path) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    common, generator, judge = load_week7_modules()
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the minimal full-pipeline smoke test")

    generation_path = output_dir / "W07_Preflight_Raw_Model_Outputs.jsonl"
    generation_metadata_path = output_dir / "W07_Preflight_Run_Metadata.json"
    preflight_log_path = output_dir / ".preflight-corrections.json"
    ratings_path = output_dir / "W07_Minimal_Judge_Ratings.csv"
    results_path = output_dir / "W07_Minimal_Results.csv"

    def generate_stage():
        generator.CONDITIONS = (CONDITION,)
        generator.MAX_NEW_TOKENS = GENERATION_MAX_NEW_TOKENS
        generator.RAW = output_dir / "W07_Raw_Model_Outputs.jsonl"
        generator.PREFLIGHT_LOG = preflight_log_path
        prior_argv = sys.argv
        started = time.perf_counter()
        try:
            sys.argv = [
                "run_w07_replication.py",
                "--phase",
                "preflight",
                "--models",
                *GENERATORS,
                "--batch-size",
                "1",
                "--limit",
                "1",
            ]
            generator.main()
        finally:
            sys.argv = prior_argv
        rows = common.read_jsonl(generation_path)
        recorded = common.read_json(generation_metadata_path)
        preflight_log_path.unlink(missing_ok=True)
        generation_metadata_path.unlink(missing_ok=True)
        return rows, {
            "seconds": time.perf_counter() - started,
            "peak_cuda_memory_bytes": int(
                recorded["runtime"]["peak_cuda_memory_bytes"]
            ),
            "max_new_tokens": GENERATION_MAX_NEW_TOKENS,
            "models": [
                {"name": name, **common.MODELS[name]} for name in GENERATORS
            ],
        }

    def judge_stage(name: str, source: list[dict[str, Any]]):
        spec = common.JUDGES[name]
        checkpoint = output_dir / f".{name}.partial.csv"
        gc.collect()
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        rows = judge.run_judge(
            name,
            spec,
            source,
            "confirmation",
            int(spec["batch_size"]),
            checkpoint,
        )
        seconds = time.perf_counter() - started
        peak = cuda_peak_bytes(torch)
        checkpoint.unlink(missing_ok=True)
        return rows, {
            "seconds": seconds,
            "peak_cuda_memory_bytes": peak,
            "model_id": spec["id"],
            "revision": spec["revision"],
            "batch_size": int(spec["batch_size"]),
            "max_new_tokens": int(judge.JUDGE_MAX_NEW_TOKENS),
        }

    def aggregate_stage(
        source: list[dict[str, Any]], ratings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        return judge.aggregate_confirmation(source, ratings, list(JUDGES))

    generations, ratings, panels, metadata = orchestrate_minimal_pipeline(
        generate_stage, judge_stage, aggregate_stage
    )
    expected_generators = {
        (common.MODELS[name]["id"], common.MODELS[name]["revision"])
        for name in GENERATORS
    }
    expected_judges = {
        name: (common.JUDGES[name]["id"], common.JUDGES[name]["revision"])
        for name in JUDGES
    }
    validate_pipeline_rows(
        generations,
        ratings,
        panels,
        expected_generators=expected_generators,
        expected_judges=expected_judges,
    )
    write_csv(ratings_path, ratings)
    write_csv(results_path, panels)
    return generations, ratings, panels, metadata


def runtime_metadata() -> dict[str, Any]:
    import torch

    packages = {}
    for name in ("torch", "transformers", "bitsandbytes", "accelerate"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "not-installed"
    properties = torch.cuda.get_device_properties(0)
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "packages": packages,
        "gpu": {
            "name": torch.cuda.get_device_name(0),
            "total_memory_bytes": int(properties.total_memory),
        },
        "offline_only": True,
    }


def execute(args: argparse.Namespace, output_dir: Path) -> dict[str, Any]:
    cache_dir = args.cache_dir.resolve()
    configure_offline_cache(cache_dir)
    cache_validation = verify_active_model_cache(cache_dir, args.checksum_manifest)
    output_dir = prepare_output_directory(output_dir)
    started_utc = datetime.now(timezone.utc)
    started = time.perf_counter()
    generations, ratings, panels, stage_metadata = run_gpu_pipeline(output_dir)
    elapsed = time.perf_counter() - started

    artifacts = {
        "generations": output_dir / "W07_Preflight_Raw_Model_Outputs.jsonl",
        "judgments": output_dir / "W07_Minimal_Judge_Ratings.csv",
        "panels": output_dir / "W07_Minimal_Results.csv",
    }
    receipt = {
        "schema_version": "w11-minimal-full-pipeline-smoke-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "started_utc": started_utc.isoformat(),
        "status": "passed",
        "verification_level": "minimal_full_pipeline_smoke",
        "scope": {
            "scenario_count": 1,
            "condition": CONDITION,
            "generators": list(GENERATORS),
            "judges": list(JUDGES),
            "generation_max_new_tokens": GENERATION_MAX_NEW_TOKENS,
            "expected_rows": {
                "generations": 2,
                "judgments": 6,
                "panels": 2,
            },
        },
        "counts": {
            "generations": len(generations),
            "judgments": len(ratings),
            "panels": len(panels),
        },
        "generation_summary": summarize_generation_rows(generations),
        "all_judgments_parsed": all(
            int(row["parse_success"]) == 1 for row in ratings
        ),
        "all_panels_parsed": all(
            int(row["parse_success"]) == 1 for row in panels
        ),
        "overall_seconds": elapsed,
        "stage_metadata": stage_metadata,
        "runtime": runtime_metadata(),
        "cache_validation": cache_validation,
        "command": runtime_command(),
        "artifacts": {
            name: {
                "path": path.name,
                "sha256": sha256_file(path),
            }
            for name, path in artifacts.items()
        },
        "claim_boundary": (
            "This bounded smoke test checks execution and interface compatibility "
            "for one scenario in one condition. It does not reproduce the registered "
            "confirmation dataset, estimates, or figures."
        ),
    }
    write_json(output_dir / "smoke_receipt.json", receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = args.output_dir or timestamped_output_directory()
    plan = build_plan(args.cache_dir, output_dir)
    if args.plan_only:
        print(json.dumps(plan, indent=2))
        return 0
    receipt = execute(args, output_dir)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "verification_level": receipt["verification_level"],
                "counts": receipt["counts"],
                "overall_seconds": receipt["overall_seconds"],
                "receipt": str((output_dir / "smoke_receipt.json").resolve()),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
