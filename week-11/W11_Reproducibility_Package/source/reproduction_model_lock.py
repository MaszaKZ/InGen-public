"""Load immutable Hugging Face revisions for the registered reproduction runs."""
from __future__ import annotations

import json
import re
from pathlib import Path


LOCK_PATH = (
    Path(__file__).resolve().parent
    .parent
    / "model_lock.json"
)
REVISION_RE = re.compile(r"[0-9a-f]{40}")


def load_model_lock(path: Path = LOCK_PATH) -> dict[str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "ingen-final-model-lock-v1":
        raise ValueError("unsupported model-lock schema")
    models = payload.get("models")
    if not isinstance(models, dict) or not models:
        raise ValueError("model lock has no models")
    for repo_id, spec in models.items():
        revision = str(spec.get("revision", ""))
        if REVISION_RE.fullmatch(revision) is None:
            raise ValueError(f"model lock has a mutable revision for {repo_id}")
    return models


def revision_for(repo_id: str) -> str:
    try:
        return str(load_model_lock()[repo_id]["revision"])
    except KeyError as exc:
        raise KeyError(f"model is absent from the lock: {repo_id}") from exc
