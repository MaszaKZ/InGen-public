"""Restore externalized raw evidence from a separately supplied local bundle.

The six verifier-consumed raw files are intentionally absent from this public
repository. A reviewer who has independently received the registered bundle
can restore it with --from-path. This script never downloads data and has no
network fallback.

Usage (from the repository root):
    python week-10/W10_Reproducibility_Package/fetch_data.py --check
    python week-10/W10_Reproducibility_Package/fetch_data.py --from-path BUNDLE.zip
    python week-10/W10_Reproducibility_Package/fetch_data.py --from-path BUNDLE.zip --force

Exit status is 0 only if every manifest file is present with a matching size
and SHA-256.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
import zipfile
from pathlib import Path, PurePosixPath


PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]
MANIFEST_PATH = PACKAGE / "data_manifest.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "w10-data-manifest-public-v1":
        raise SystemExit("FAIL: unsupported public data-manifest schema")
    return manifest


def safe_target(relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise SystemExit(f"FAIL: unsafe manifest path {relative!r}")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in relative.split("/")):
        raise SystemExit(f"FAIL: unsafe manifest path {relative!r}")
    target = (ROOT / Path(*pure.parts)).resolve(strict=False)
    try:
        target.relative_to(ROOT.resolve(strict=True))
    except ValueError as exc:
        raise SystemExit(f"FAIL: manifest path escapes repository root: {relative}") from exc
    return target


def check_files(manifest: dict, verbose: bool = True) -> int:
    """Verify on-disk files against the manifest; return the number of problems."""
    problems = 0
    for entry in manifest["files"]:
        target = safe_target(entry["path"])
        if not target.is_file():
            status = "MISSING"
            problems += 1
        elif target.stat().st_size != entry["size_bytes"]:
            status = "SIZE MISMATCH"
            problems += 1
        elif sha256_bytes(target.read_bytes()) != entry["sha256"]:
            status = "HASH MISMATCH"
            problems += 1
        else:
            status = "OK"
        if verbose or status != "OK":
            print(f"{status:>13}  {entry['path']}")
    return problems


def validate_bundle(manifest: dict, bundle_path: Path) -> dict[str, bytes]:
    if not bundle_path.is_file():
        raise SystemExit(f"FAIL: local bundle is not a file: {bundle_path}")
    bundle = manifest["bundle"]
    actual_size = bundle_path.stat().st_size
    if actual_size != bundle["size_bytes"]:
        raise SystemExit(
            f"FAIL: bundle size {actual_size} does not match manifest {bundle['size_bytes']}"
        )
    bundle_bytes = bundle_path.read_bytes()
    actual_hash = sha256_bytes(bundle_bytes)
    if actual_hash != bundle["sha256"]:
        raise SystemExit(
            f"FAIL: bundle hash {actual_hash} does not match manifest {bundle['sha256']}"
        )
    print(f"bundle OK  {bundle_path.name}  sha256 {actual_hash}")

    entries_by_name = {entry["name"]: entry for entry in manifest["files"]}
    if len(entries_by_name) != len(manifest["files"]):
        raise SystemExit("FAIL: data manifest contains duplicate bundle member names")
    validated: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(bundle_path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                raise SystemExit("FAIL: local bundle contains duplicate member names")
            expected_names = set(entries_by_name)
            actual_names = set(names)
            if actual_names != expected_names:
                missing = sorted(expected_names - actual_names)
                extra = sorted(actual_names - expected_names)
                raise SystemExit(f"FAIL: bundle member mismatch; missing={missing}; extra={extra}")
            for info in infos:
                entry = entries_by_name[info.filename]
                if info.is_dir() or info.file_size != entry["size_bytes"]:
                    raise SystemExit(f"FAIL: bundle size mismatch for {info.filename}")
                data = archive.read(info)
                if len(data) != entry["size_bytes"] or sha256_bytes(data) != entry["sha256"]:
                    raise SystemExit(f"FAIL: bundle content mismatch for {entry['path']}")
                validated[info.filename] = data
    except zipfile.BadZipFile as exc:
        raise SystemExit(f"FAIL: local bundle is not a valid ZIP archive: {exc}") from exc
    return validated


def atomic_write(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / f".{target.name}.restore-{uuid.uuid4().hex}.tmp"
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def restore(manifest: dict, bundle_path: Path, force: bool) -> int:
    validated = validate_bundle(manifest, bundle_path)
    problems = 0
    for entry in manifest["files"]:
        target = safe_target(entry["path"])
        data = validated[entry["name"]]
        if target.exists():
            if not target.is_file():
                print(f"{'REFUSED':>13}  {entry['path']} is not a regular file")
                problems += 1
                continue
            existing = sha256_bytes(target.read_bytes())
            if existing == entry["sha256"] and target.stat().st_size == entry["size_bytes"]:
                print(f"{'OK (present)':>13}  {entry['path']}")
                continue
            if not force:
                print(
                    f"{'REFUSED':>13}  {entry['path']} exists with different bytes; "
                    "rerun with --force to overwrite"
                )
                problems += 1
                continue
        atomic_write(target, data)
        print(f"{'RESTORED':>13}  {entry['path']}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="verify already-present files")
    mode.add_argument("--from-path", type=Path, metavar="BUNDLE", help="restore from a local bundle")
    parser.add_argument("--force", action="store_true", help="overwrite mismatched regular files")
    args = parser.parse_args()
    if args.force and args.from_path is None:
        parser.error("--force requires --from-path")

    manifest = load_manifest()
    problems = check_files(manifest) if args.check else restore(manifest, args.from_path, args.force)
    if problems:
        raise SystemExit(f"FAIL: {problems} problem(s); raw evidence is not fully restored")
    print(f"PASS: all {len(manifest['files'])} raw-evidence files verified against the manifest")


if __name__ == "__main__":
    main()
