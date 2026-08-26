from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parent
DEFAULT_CACHE = PACKAGE / "models" / "huggingface" / "hub"
DEFAULT_CHECKSUM_MANIFEST = PACKAGE / "models" / "model-checksums.json"
TOKENIZER_FILES = (
    "tokenizer.json",
    "tokenizer.model",
    "spiece.model",
    "vocab.json",
)
WEIGHT_INDEX_FILES = (
    "model.safetensors.index.json",
    "pytorch_model.bin.index.json",
)


def load_lock(path: Path = PACKAGE / "model_lock.json") -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    models = payload.get("models")
    if payload.get("schema_version") != "ingen-final-model-lock-v1" or not isinstance(models, dict):
        raise ValueError(f"invalid model lock: {path}")
    for repo_id, record in models.items():
        revision = record.get("revision") if isinstance(record, dict) else None
        if not isinstance(repo_id, str) or repo_id.count("/") != 1:
            raise ValueError(f"invalid repository ID: {repo_id!r}")
        if not isinstance(revision, str) or not revision.isalnum() or len(revision) != 40:
            raise ValueError(f"invalid immutable revision for {repo_id}: {revision!r}")
    return payload


def cache_directory(repo_id: str) -> str:
    return "models--" + repo_id.replace("/", "--")


def _snapshot_has_content(path: Path) -> bool:
    return any(item.is_file() or item.is_symlink() for item in path.rglob("*"))


def _resolved_nonempty_file(path: Path) -> bool:
    try:
        resolved = path.resolve(strict=True)
        return resolved.is_file() and resolved.stat().st_size > 0
    except OSError:
        return False


def _load_json_object(path: Path) -> dict[str, Any] | None:
    if not _resolved_nonempty_file(path):
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _snapshot_file_entries(
    cache_root: Path, lock: dict[str, Any]
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for repo_id, record in lock["models"].items():
        snapshot = (
            cache_root
            / cache_directory(repo_id)
            / "snapshots"
            / str(record["revision"])
        )
        for path in sorted(item for item in snapshot.rglob("*") if item.is_file()):
            entries.append(
                {
                    "path": path.relative_to(cache_root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            )
    return entries


def write_checksum_manifest(
    cache_root: Path,
    target: Path,
    lock: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lock = load_lock() if lock is None else lock
    cache_root = cache_root.resolve()
    structural = inspect_cache(
        cache_root,
        lock=lock,
        checksum_manifest=target,
        require_checksums=False,
    )
    if not result_ok(structural, allow_missing=False):
        raise ValueError("cannot checksum an incomplete or structurally invalid model cache")
    payload = {
        "schema_version": "ingen-model-checksum-manifest-v1",
        "models": {
            repo_id: {"revision": str(record["revision"])}
            for repo_id, record in lock["models"].items()
        },
        "files": _snapshot_file_entries(cache_root, lock),
    }
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def verify_checksum_manifest(
    cache_root: Path,
    manifest_path: Path,
    lock: dict[str, Any],
) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_file():
        return {"status": "missing", "manifest": str(manifest_path)}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = payload.get("files")
        models = payload.get("models")
        if (
            payload.get("schema_version") != "ingen-model-checksum-manifest-v1"
            or not isinstance(files, list)
            or not isinstance(models, dict)
        ):
            raise ValueError("unsupported or incomplete checksum-manifest schema")
        expected_models = {
            repo_id: {"revision": str(record["revision"])}
            for repo_id, record in lock["models"].items()
        }
        if models != expected_models:
            raise ValueError("checksum manifest does not match model_lock.json")
        expected: dict[str, dict[str, Any]] = {}
        for entry in files:
            relative = str(entry["path"])
            if (
                relative in expected
                or Path(relative).is_absolute()
                or ".." in Path(relative).parts
            ):
                raise ValueError(f"unsafe or duplicate checksum path: {relative}")
            expected[relative] = entry
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return {
            "status": "invalid",
            "manifest": str(manifest_path),
            "problem": str(exc),
        }

    actual_entries = _snapshot_file_entries(cache_root, lock)
    actual = {entry["path"]: entry for entry in actual_entries}
    missing_files = sorted(set(expected) - set(actual))
    unexpected_files = sorted(set(actual) - set(expected))
    mismatches = sorted(
        relative
        for relative in set(expected) & set(actual)
        if int(expected[relative]["size_bytes"]) != int(actual[relative]["size_bytes"])
        or str(expected[relative]["sha256"]) != str(actual[relative]["sha256"])
    )
    status = "pass" if not (missing_files or unexpected_files or mismatches) else "mismatch"
    return {
        "status": status,
        "manifest": str(manifest_path),
        "files": len(expected),
        "missing_files": missing_files,
        "unexpected_files": unexpected_files,
        "mismatches": mismatches,
    }


def snapshot_problems(snapshot: Path) -> list[str]:
    problems: list[str] = []

    config = _load_json_object(snapshot / "config.json")
    if config is None or not isinstance(config.get("model_type"), str):
        problems.append("config.json is missing, invalid, or lacks model_type")

    if not any(_resolved_nonempty_file(snapshot / name) for name in TOKENIZER_FILES):
        problems.append("no loadable tokenizer vocabulary/model file")

    index_paths = [
        snapshot / name
        for name in WEIGHT_INDEX_FILES
        if (snapshot / name).exists() or (snapshot / name).is_symlink()
    ]
    if index_paths:
        for index_path in index_paths:
            index = _load_json_object(index_path)
            weight_map = index.get("weight_map") if index is not None else None
            if not isinstance(weight_map, dict) or not weight_map:
                problems.append(f"{index_path.name} has no valid weight_map")
                continue
            for relative in sorted(set(str(value) for value in weight_map.values())):
                if (
                    Path(relative).is_absolute()
                    or ".." in Path(relative).parts
                    or not _resolved_nonempty_file(snapshot / relative)
                ):
                    problems.append(relative)
    else:
        weight_files = [
            path
            for pattern in ("*.safetensors", "pytorch_model*.bin")
            for path in snapshot.rglob(pattern)
            if _resolved_nonempty_file(path)
        ]
        if not weight_files:
            problems.append("no non-empty model weights or weight index")

    for item in snapshot.rglob("*"):
        if item.is_symlink() and not _resolved_nonempty_file(item):
            problems.append(item.relative_to(snapshot).as_posix())

    return sorted(set(problems))


def inspect_cache(
    cache_root: Path,
    lock: dict[str, Any] | None = None,
    checksum_manifest: Path | None = None,
    require_checksums: bool = True,
) -> dict[str, Any]:
    lock = load_lock() if lock is None else lock
    cache_root = cache_root.resolve()
    models: dict[str, dict[str, Any]] = lock["models"]
    expected_dirs = {cache_directory(repo_id): repo_id for repo_id in models}

    missing: list[dict[str, str]] = []
    misplaced: list[str] = []
    unexpected_models: list[str] = []
    unexpected_revisions: list[dict[str, str]] = []
    empty_snapshots: list[dict[str, str]] = []
    incomplete_snapshots: list[dict[str, Any]] = []
    present: list[dict[str, str]] = []

    if cache_root.is_dir():
        for item in cache_root.iterdir():
            if item.is_dir() and item.name.startswith("models--") and item.name not in expected_dirs:
                unexpected_models.append(item.name)

    for repo_id, record in models.items():
        revision = str(record["revision"])
        model_root = cache_root / cache_directory(repo_id)
        snapshot_root = model_root / "snapshots"
        snapshot = snapshot_root / revision
        direct_layout = cache_root.joinpath(*repo_id.split("/"))
        if direct_layout.exists():
            misplaced.append(direct_layout.relative_to(cache_root).as_posix())

        if snapshot_root.is_dir():
            for candidate in snapshot_root.iterdir():
                if candidate.is_dir() and candidate.name != revision:
                    unexpected_revisions.append(
                        {"repo_id": repo_id, "revision": candidate.name}
                    )

        if not snapshot.is_dir():
            missing.append({"repo_id": repo_id, "revision": revision})
            continue
        if not _snapshot_has_content(snapshot):
            empty_snapshots.append({"repo_id": repo_id, "revision": revision})
            continue
        problems = snapshot_problems(snapshot)
        if problems:
            incomplete_snapshots.append(
                {"repo_id": repo_id, "revision": revision, "problems": problems}
            )
            continue
        present.append({"repo_id": repo_id, "revision": revision})

    if not present:
        checksum_verification = {"status": "not_required"}
    elif not require_checksums:
        checksum_verification = {"status": "not_required"}
    else:
        inferred_manifest = (
            checksum_manifest
            if checksum_manifest is not None
            else cache_root.parents[1] / "model-checksums.json"
        )
        checksum_verification = verify_checksum_manifest(
            cache_root, inferred_manifest, lock
        )

    return {
        "cache_root": str(cache_root),
        "expected": len(models),
        "present": present,
        "missing": missing,
        "misplaced": sorted(misplaced),
        "unexpected_models": sorted(unexpected_models),
        "unexpected_revisions": sorted(
            unexpected_revisions, key=lambda row: (row["repo_id"], row["revision"])
        ),
        "empty_snapshots": empty_snapshots,
        "incomplete_snapshots": incomplete_snapshots,
        "checksum_verification": checksum_verification,
    }


def result_ok(result: dict[str, Any], allow_missing: bool) -> bool:
    structural_errors = any(
        result[key]
        for key in (
            "misplaced",
            "unexpected_models",
            "unexpected_revisions",
            "empty_snapshots",
            "incomplete_snapshots",
        )
    )
    checksum_status = result.get("checksum_verification", {}).get("status")
    checksum_ok = checksum_status in {"pass", "not_required"}
    return (
        not structural_errors
        and checksum_ok
        and (allow_missing or not result["missing"])
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the exact package-local Hugging Face cache layout."
    )
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument(
        "--checksum-manifest",
        type=Path,
        default=DEFAULT_CHECKSUM_MANIFEST,
        help="portable SHA-256 manifest generated after connected checksum verification",
    )
    parser.add_argument(
        "--write-checksum-manifest",
        type=Path,
        help="write a portable SHA-256 manifest for a complete verified cache",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="permit absent weights for CPU/mock acceptance; structural errors still fail",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args(argv)

    try:
        if args.write_checksum_manifest is not None:
            write_checksum_manifest(args.cache_dir, args.write_checksum_manifest)
            checksum_manifest = args.write_checksum_manifest
        else:
            checksum_manifest = args.checksum_manifest
        result = inspect_cache(
            args.cache_dir,
            checksum_manifest=checksum_manifest,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    ok = result_ok(result, args.allow_missing)
    result["allow_missing"] = bool(args.allow_missing)
    result["status"] = "pass" if ok else "fail"
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        print(f"cache: {result['cache_root']}")
        print(f"present: {len(result['present'])}/{result['expected']}")
        for key in (
            "missing",
            "misplaced",
            "unexpected_models",
            "unexpected_revisions",
            "empty_snapshots",
            "incomplete_snapshots",
        ):
            if result[key]:
                print(f"{key}: {json.dumps(result[key], sort_keys=True)}")
        print(
            "checksums: "
            + json.dumps(result["checksum_verification"], sort_keys=True)
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
