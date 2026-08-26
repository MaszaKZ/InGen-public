from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path


W11 = Path(__file__).resolve().parent
ROOT = W11.parent
PACKAGE = W11 / "W11_Reproducibility_Package"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_upstream_continuity() -> None:
    pairs = (
        (ROOT / "week-06/W06_Analysis.json", PACKAGE / "source/week-06/W06_Analysis.json"),
        (ROOT / "week-07/W07_Analysis.json", PACKAGE / "source/week-07/W07_Analysis.json"),
        (ROOT / "week-07/W07_Results.csv", PACKAGE / "source/week-07/W07_Results.csv"),
        (ROOT / "week-10/W10_Judge_Sensitivity.json", PACKAGE / "source/week-10/W10_Judge_Sensitivity.json"),
    )
    for admitted, packaged in pairs:
        require(admitted.is_file() and packaged.is_file(), f"missing continuity pair: {admitted} / {packaged}")
        require(sha256(admitted) == sha256(packaged), f"packaged evidence differs from admitted source: {admitted}")


def verify_artifact_copies() -> None:
    pairs = (
        (W11 / "W11_Capstone_Report.pdf", PACKAGE / "artifacts/report/Capstone_Report.pdf"),
        (W11 / "W11_Capstone_Report.tex", PACKAGE / "artifacts/report/Capstone_Report.tex"),
        (W11 / "W11_Research_Review_Deck.pptx", PACKAGE / "artifacts/slides/Research_Review_Deck.pptx"),
    )
    for primary, packaged in pairs:
        require(primary.is_file() and packaged.is_file(), f"missing artifact pair: {primary} / {packaged}")
        require(sha256(primary) == sha256(packaged), f"packaged artifact differs from primary: {primary}")


def verify_receipt() -> None:
    receipt_path = PACKAGE / "receipts/isolated-cpu-mock.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    require(receipt.get("status") == "mock_only", "isolated receipt must remain mock_only")
    require(receipt.get("network_used") is False, "isolated receipt used network")
    require(receipt.get("model_download_attempted") is False, "isolated receipt attempted a model download")
    require(receipt.get("full_inference_executed") is False, "isolated receipt incorrectly claims full inference")
    require(receipt.get("models_present") == 0 and receipt.get("models_expected") == 10, "isolated model boundary changed")
    manifest = json.loads(
        (PACKAGE / "package_manifest.json").read_text(encoding="utf-8")
    )
    entries = {entry["path"]: entry for entry in manifest["files"]}
    relative = receipt_path.relative_to(PACKAGE).as_posix()
    require(relative in entries, "isolated receipt is not manifest-pinned")
    require(
        entries[relative]["sha256"] == sha256(receipt_path),
        "isolated receipt differs from its manifest-pinned bytes",
    )


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(W11), pattern="test_w11.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    package_verifier = load_module("w11_package_verifier", PACKAGE / "verify_package.py")
    package_verifier.verify_all()
    verify_upstream_continuity()
    verify_artifact_copies()
    verify_receipt()

    print("PASS: Week 11 capstone submission verified")
    print("PASS: upstream evidence continuity verified")
    print("PASS: standalone package and isolated mock_only receipt verified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
