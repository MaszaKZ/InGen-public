"""One-command regeneration and verification driver for the whole repository.

Tier 0 restores the externalized raw evidence and runs every verifier without
regenerating anything. Tier 1 additionally reruns every deterministic analysis,
table, and figure script whose outputs are committed, then proves the working
tree is byte-identical before verifying. Tier 2 (fresh full model inference)
uses reproduce_fresh.py, which creates an isolated detached worktree, locks
every model revision, and verifies the new evidence without changing the
historical record.

Usage (from the repository root):
    python week-10/W10_Reproducibility_Package/regenerate_all.py --tier 1 --bundle BUNDLE.zip
    python week-10/W10_Reproducibility_Package/regenerate_all.py --tier 0
    python week-10/W10_Reproducibility_Package/regenerate_all.py --tier 1 --with-tests
    python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode full --accept-compute-cost --bundle BUNDLE.zip

The verify_w07 confirmation phase rewrites its receipt's verified_utc
timestamp by design; the driver asserts that the timestamp is the only change
and restores the committed receipt, so a fully successful run ends with a
clean working tree.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]
RECEIPT = "week-07/W07_Independent_Verification.json"

REGENERATION_STEPS = [
    ["week-07/analyze_w07.py"],
    ["week-08/analyze_w08_pressure_cues.py"],
    ["week-09/build_w09_paper_tables.py"],
    ["week-09/build_w09_paper_figures.py"],
    ["week-10/analyze_w10_judge_sensitivity.py"],
]
# week-07/analyze_w07_panel_ceiling.py is deliberately absent: its output is
# the registered pre-run simulation record, replay-validated at acceptance
# time, and is not an input to any paper table or figure. Rerun it manually
# if you want to reproduce the ceiling analysis itself.

TEST_STEPS = [
    ["week-06/test_w06_experiment2.py"],
    ["-m", "unittest", "week-07.test_w07_replication"],
]

VERIFIER_STEPS = [
    ["week-06/verify_w06_independent.py"],
    ["week-07/verify_w07_independent.py", "--phase", "precalibration"],
    ["week-07/verify_w07_independent.py", "--phase", "confirmation"],
    ["week-08/verify_w08.py"],
    ["week-09/verify_w09.py"],
    ["week-10/verify_w10.py"],
]


def run(step: list[str]) -> None:
    command = [sys.executable, *step]
    print(f"\n=== {' '.join(step)}", flush=True)
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"FAIL: {' '.join(step)} exited {result.returncode}")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True
    ).stdout


def require_clean_tree(context: str, allow_receipt: bool = False) -> None:
    # Untracked files (a venv, an editor backup) are not regeneration drift;
    # drift can only appear as a modified or deleted tracked file.
    status = [
        line
        for line in git("status", "--porcelain", "--untracked-files=no").splitlines()
        if line.strip()
    ]
    if allow_receipt and status == [f" M {RECEIPT}"]:
        changed = [
            line for line in git("diff", RECEIPT).splitlines()
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        ]
        if all("verified_utc" in line for line in changed) and changed:
            git("checkout", "--", RECEIPT)
            print(f"restored {RECEIPT} (timestamp-only rewrite, as documented)")
            status = [
                line
                for line in git("status", "--porcelain", "--untracked-files=no").splitlines()
                if line.strip()
            ]
    if status:
        print("\n".join(status))
        raise SystemExit(f"FAIL: working tree not byte-identical {context}")
    print(f"OK: working tree byte-identical {context}")


def ensure_data(skip_fetch: bool, bundle: Path | None) -> None:
    manifest = json.loads((PACKAGE / "data_manifest.json").read_text(encoding="utf-8"))
    missing = [e["path"] for e in manifest["files"] if not (ROOT / e["path"]).exists()]
    if missing and (skip_fetch or bundle is None):
        reason = "--skip-fetch given" if skip_fetch else "no --bundle path supplied"
        raise SystemExit(f"FAIL: {len(missing)} raw-evidence file(s) missing and {reason}")
    if missing:
        run(["week-10/W10_Reproducibility_Package/fetch_data.py", "--from-path", str(bundle.resolve())])
    else:
        run(["week-10/W10_Reproducibility_Package/fetch_data.py", "--check"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tier", type=int, choices=(0, 1), default=1)
    parser.add_argument("--with-tests", action="store_true",
                        help="also run the week-06 and week-07 test suites")
    parser.add_argument("--skip-fetch", action="store_true",
                        help="fail instead of restoring if raw evidence is missing")
    parser.add_argument("--bundle", type=Path,
                        help="separately supplied local bundle used when raw evidence is missing")
    args = parser.parse_args()

    ensure_data(args.skip_fetch, args.bundle)

    if args.tier >= 1:
        for step in REGENERATION_STEPS:
            run(step)
        require_clean_tree("after regeneration")

    if args.with_tests:
        for step in TEST_STEPS:
            run(step)

    for step in VERIFIER_STEPS:
        run(step)
    require_clean_tree("after verification", allow_receipt=True)

    print(f"\nPASS: tier {args.tier} regeneration and verification complete")


if __name__ == "__main__":
    main()
