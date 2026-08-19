#!/usr/bin/env python3
"""Check census cardinalities and graph invariants for all 4,681 records."""

from __future__ import annotations

import argparse
from pathlib import Path

import networkx as nx

from _repo import ROOT, decode_graph6

EXPECTED = {4: 1, 6: 2, 8: 5, 10: 19, 12: 85, 14: 509, 16: 4060}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--census-dir", type=Path, default=ROOT / "data" / "census" / "canonical"
    )
    args = parser.parse_args()
    total = 0
    for n, expected in EXPECTED.items():
        path = args.census_dir / f"connected_cubic_n{n}.g6"
        records = [line for line in path.read_text(encoding="ascii").splitlines() if line]
        if len(records) != expected:
            raise AssertionError(f"n={n}: expected {expected}, found {len(records)}")
        if len(set(records)) != len(records):
            raise AssertionError(f"n={n}: duplicate graph6 records")
        for index, record in enumerate(records):
            graph = decode_graph6(record)
            valid = (
                len(graph) == n
                and nx.is_connected(graph)
                and not graph.is_multigraph()
                and not any(u == v for u, v in graph.edges)
                and all(degree == 3 for _, degree in graph.degree)
            )
            if not valid:
                raise AssertionError(f"n={n}, record={index}: invalid census graph")
        total += len(records)
        print(f"n={n}: {len(records)} PASS")
    if total != 4681:
        raise AssertionError(f"expected 4681 total graphs, found {total}")
    print("total=4681 PASS")


if __name__ == "__main__":
    main()

