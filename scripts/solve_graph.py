#!/usr/bin/env python3
"""Run publication Solver A, B, or C on one graph6 input."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _repo import decode_graph6, read_graph6
from src.exact_solver import (
    minimum_maximal_acyclic_matching,
    minimum_maximal_acyclic_matching_bruteforce,
)
from src.solver_c import minimum_maximal_acyclic_matching_cubic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--graph6", help="one graph6 string")
    source.add_argument("--input", type=Path, help="graph6 file")
    parser.add_argument("--index", type=int, default=0, help="zero-based record for --input")
    parser.add_argument("--solver", choices=("A", "B", "C"), required=True)
    args = parser.parse_args()

    if args.graph6 is not None:
        graph6, graph = args.graph6.strip(), decode_graph6(args.graph6)
    else:
        graph6, graph = read_graph6(args.input, args.index)

    solve = {
        "A": minimum_maximal_acyclic_matching_bruteforce,
        "B": minimum_maximal_acyclic_matching,
        "C": minimum_maximal_acyclic_matching_cubic,
    }[args.solver]
    result = solve(graph)
    payload = {
        "graph6": graph6,
        "order": graph.number_of_nodes(),
        "size": graph.number_of_edges(),
        "solver": result.solver,
        "optimum": result.mu,
        "matching": [list(edge) for edge in result.matching],
        "runtime_seconds": result.runtime_seconds,
        "states_examined": result.states_examined,
        "forest_tests": result.forest_tests,
        "maximality_tests": result.maximality_tests,
        "metadata": result.metadata,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

