#!/usr/bin/env python3
"""Run the short, non-benchmark release verification suite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.exact_solver import minimum_maximal_acyclic_matching, minimum_maximal_acyclic_matching_bruteforce
from src.solver_c import minimum_maximal_acyclic_matching_cubic


def run(relative: str, *arguments: str) -> None:
    subprocess.run([sys.executable, str(ROOT / relative), *arguments], cwd=ROOT, check=True)


def compare_small_graphs() -> None:
    graphs = {
        "K4": nx.complete_graph(4),
        "K3,3": nx.complete_bipartite_graph(3, 3),
        "cube": nx.cubical_graph(),
    }
    for name, graph in graphs.items():
        results = [
            minimum_maximal_acyclic_matching_bruteforce(graph),
            minimum_maximal_acyclic_matching(graph),
            minimum_maximal_acyclic_matching_cubic(graph),
        ]
        optima = {result.mu for result in results}
        if len(optima) != 1:
            raise AssertionError(f"{name}: Solver A/B/C disagreement {optima}")
        print(f"{name}: Solver A/B/C optimum {results[0].mu} PASS")


def main() -> None:
    subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, check=True)
    run("scripts/verify_census_counts.py")
    run("scripts/verify_counterexamples.py")
    run("scripts/verify_structural_certificates.py")
    run("scripts/reproduce_tables/reproduce_all.py")
    run("scripts/verify_paper_numbers.py")
    run("scripts/verify_hashes.py")
    compare_small_graphs()
    print("RELEASE VERIFICATION PASSED")


if __name__ == "__main__":
    main()

