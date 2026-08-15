"""Fetch the immutable snapshots required by a full reproduction run."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from huggingface_hub import snapshot_download


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reproduction_model_lock import load_model_lock


def prefetch(cache_dir: Path, selected: set[str] | None = None) -> dict[str, str]:
    """Download the selected immutable model snapshots into ``cache_dir``."""
    models = load_model_lock()
    selected_models = sorted(models) if selected is None else sorted(selected)
    resolved: dict[str, str] = {}
    for repo_id in selected_models:
        revision = str(models[repo_id]["revision"])
        resolved[repo_id] = str(snapshot_download(
            repo_id=repo_id,
            revision=revision,
            cache_dir=str(cache_dir),
        ))
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache_dir", type=Path)
    parser.add_argument("--model", dest="selected", action="append")
    args = parser.parse_args()

    # This is the sole network-enabled entry point. Fresh experiment stages
    # receive the offline environment assembled by reproduce_fresh.py.
    os.environ.pop("HF_HUB_OFFLINE", None)
    os.environ.pop("TRANSFORMERS_OFFLINE", None)
    print(json.dumps(prefetch(args.cache_dir, set(args.selected) if args.selected else None), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
