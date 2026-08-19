#!/usr/bin/env python3
"""Run the publication Solver B/C protocol against the preserved census."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _repo import ROOT
import run_solver_bc_full_census as publication


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("all", "correctness", "census"), default="all")
    parser.add_argument("--output", type=Path, default=ROOT / "reproduced" / "solver_bc_full_census")
    args = parser.parse_args()
    publication.RUN_DIR = args.output.resolve()
    publication.CENSUS_DIR = ROOT / "data" / "census" / "canonical"
    old_argv = sys.argv
    try:
        sys.argv = [str(Path(__file__).name), "--phase", args.phase]
        publication.main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()

