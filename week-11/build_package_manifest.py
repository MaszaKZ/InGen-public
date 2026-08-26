from __future__ import annotations

import hashlib
import json
from pathlib import Path


W11 = Path(__file__).resolve().parent
PACKAGE = W11 / "W11_Reproducibility_Package"
TARGET = PACKAGE / "package_manifest.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def included(relative: str) -> bool:
    if relative == "package_manifest.json":
        return False
    if relative.startswith("generated-receipts/") or relative.startswith("regenerated-figures/"):
        return False
    if "/__pycache__/" in f"/{relative}" or relative.endswith(".pyc"):
        return False
    if relative.startswith("models/huggingface/hub/"):
        return relative == "models/huggingface/hub/PUT_MODELS_HERE.txt"
    return True


def main() -> int:
    files = []
    for path in sorted((item for item in PACKAGE.rglob("*") if item.is_file())):
        relative = path.relative_to(PACKAGE).as_posix()
        if not included(relative):
            continue
        files.append(
            {
                "path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": digest(path),
            }
        )
    payload = {
        "schema_version": "ingen-final-package-manifest-v1",
        "model_weights_included": False,
        "model_cache_root": "models/huggingface/hub",
        "receipt_status_for_default_acceptance": "mock_only",
        "files": files,
    }
    with TARGET.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"wrote {TARGET} with {len(files)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
