from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from statistics import median
from time import perf_counter

import networkx as nx

from src.constructions import extremal_graph_for_order_direct
from src.exact_solver import minimum_maximal_acyclic_matching
from src.solver_c import minimum_maximal_acyclic_matching_cubic

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "solver_c_benchmark.csv"
SUMMARY = ROOT / "results" / "solver_c_benchmark_summary.json"


def shuffled_graph(G: nx.Graph, seed: int) -> nx.Graph:
    rng = random.Random(seed)
    old = list(G.nodes)
    rng.shuffle(old)
    mapping = {v: i for i, v in enumerate(old)}
    edges = [(mapping[u], mapping[v]) for u, v in G.edges]
    rng.shuffle(edges)
    H = nx.Graph()
    H.add_nodes_from(range(len(old)))
    H.add_edges_from(edges)
    return H


def cases():
    standard = [
        ("K4", nx.complete_graph(4)),
        ("K33", nx.complete_bipartite_graph(3, 3)),
        ("cube", nx.cubical_graph()),
        ("Petersen", nx.petersen_graph()),
        ("prism10", nx.circular_ladder_graph(5)),
        ("prism12", nx.circular_ladder_graph(6)),
    ]
    for name, G in standard:
        yield "standard", name, G

    for n in range(14, 31, 2):
        G = shuffled_graph(extremal_graph_for_order_direct(n).graph, 9000 + n)
        yield "equality", f"equality_n{n}", G

    for n in (14, 16, 18, 20, 22, 24):
        made = 0
        seed = 0
        while made < 2:
            G = nx.random_regular_graph(3, n, seed=10000 * n + seed)
            seed += 1
            if nx.is_connected(G):
                yield "random", f"random_n{n}_s{made}", G
                made += 1

    g6_path = ROOT.parents[1] / "cubic_acyclic_matching" / "results" / "counterexamples_n16.g6"
    if g6_path.exists():
        for idx, line in enumerate(g6_path.read_bytes().splitlines()):
            if line.strip():
                yield "counterexample", f"counterexample_{idx}", nx.from_graph6_bytes(line.strip())


def main() -> None:
    rows = []
    for family, name, G in cases():
        t0 = perf_counter()
        b = minimum_maximal_acyclic_matching(G)
        wall_b = perf_counter() - t0
        t0 = perf_counter()
        c = minimum_maximal_acyclic_matching_cubic(G)
        wall_c = perf_counter() - t0
        assert b.mu == c.mu
        speedup = wall_b / wall_c if wall_c > 0 else float("inf")
        row = {
            "family": family,
            "case": name,
            "n": len(G),
            "m": G.number_of_edges(),
            "mu": b.mu,
            "solver_b_seconds": wall_b,
            "solver_c_seconds": wall_c,
            "speedup_b_over_c": speedup,
            "solver_b_complete_candidates": b.states_examined,
            "solver_b_forest_tests": b.forest_tests,
            "solver_c_complete_candidates": c.states_examined,
            "solver_c_recursion_nodes": c.metadata["recursion_nodes"],
            "solver_c_defect_budget_first": c.metadata["target_attempts"][0]["defect_budget"] if c.metadata["target_attempts"] else "",
            "solver_c_greedy_upper_bound": c.metadata["greedy_upper_bound"],
        }
        rows.append(row)
        print(
            f"{family:14s} {name:24s} n={len(G):2d} mu={b.mu:2d} "
            f"B={wall_b:9.5f}s C={wall_c:9.5f}s speedup={speedup:8.2f}x",
            flush=True,
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_family = {}
    for family in sorted({r["family"] for r in rows}):
        values = [r["speedup_b_over_c"] for r in rows if r["family"] == family]
        by_family[family] = {
            "cases": len(values),
            "median_speedup": median(values),
            "min_speedup": min(values),
            "max_speedup": max(values),
        }
    summary = {
        "cases": len(rows),
        "all_median_speedup": median(r["speedup_b_over_c"] for r in rows),
        "families": by_family,
        "all_results_equal": True,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
