#!/usr/bin/env python3
"""Generate connected simple cubic graph6 censuses with nauty 2.9.3 geng."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from _repo import ROOT
from verify_census_counts import EXPECTED


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geng", default="geng", help="path to nauty 2.9.3 geng executable")
    parser.add_argument("--orders", nargs="+", type=int, default=sorted(EXPECTED))
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reproduced" / "census")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for n in args.orders:
        if n not in EXPECTED:
            raise ValueError(f"publication census supports {sorted(EXPECTED)}; received {n}")
        output = args.output_dir / f"connected_cubic_n{n}.g6"
        command = [args.geng, "-c", "-q", "-d3", "-D3", str(n), str(3 * n // 2)]
        print("running:", " ".join(command))
        with output.open("wb") as stream:
            subprocess.run(command, stdout=stream, check=True)
        count = sum(1 for line in output.read_bytes().splitlines() if line)
        if count != EXPECTED[n]:
            raise AssertionError(f"n={n}: expected {EXPECTED[n]} records, found {count}")
        print(f"n={n}: {count} records -> {output}")


if __name__ == "__main__":
    main()

