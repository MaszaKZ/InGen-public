from __future__ import annotations

import argparse
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent.parent
ANALYSIS = Path(__file__).resolve().parent
sys.path.insert(0, str(ANALYSIS))

from build_figures import build_all  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate all four publication figures.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PACKAGE / "regenerated-figures",
        help="destination; defaults to package-local regenerated-figures",
    )
    args = parser.parse_args()
    outputs = build_all(PACKAGE / "source", args.output_dir)
    for output in outputs:
        print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

