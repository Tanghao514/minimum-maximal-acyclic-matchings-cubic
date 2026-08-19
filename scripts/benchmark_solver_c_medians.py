from __future__ import annotations

import csv
import gc
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
OUT = ROOT / "results" / "solver_c_benchmark_medians.csv"
SUMMARY = ROOT / "results" / "solver_c_benchmark_medians.json"
REPEATS = 3


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
    for n in (16, 18, 20, 22, 24, 26, 28):
        yield "equality", f"equality_n{n}", shuffled_graph(
            extremal_graph_for_order_direct(n).graph, 9000 + n
        )

    for n in (16, 18, 20, 22, 24):
        for s in range(1):
            seed = 10000 * n + s
            G = nx.random_regular_graph(3, n, seed=seed)
            if nx.is_connected(G):
                yield "random", f"random_n{n}_s{s}", G

    g6_path = ROOT.parents[1] / "cubic_acyclic_matching" / "results" / "counterexamples_n16.g6"
    if g6_path.exists():
        for idx, line in enumerate(g6_path.read_bytes().splitlines()):
            if line.strip():
                yield "counterexample", f"counterexample_{idx}", nx.from_graph6_bytes(line.strip())


def timed(func, G):
    values = []
    result = None
    for _ in range(REPEATS):
        gc.collect()
        t0 = perf_counter()
        result = func(G)
        values.append(perf_counter() - t0)
    return result, median(values), values


def main():
    rows = []
    for family, name, G in cases():
        b, tb, raw_b = timed(minimum_maximal_acyclic_matching, G)
        c, tc, raw_c = timed(minimum_maximal_acyclic_matching_cubic, G)
        assert b.mu == c.mu
        row = {
            "family": family,
            "case": name,
            "n": len(G),
            "m": G.number_of_edges(),
            "mu": b.mu,
            "repeats": REPEATS,
            "solver_b_median_seconds": tb,
            "solver_c_median_seconds": tc,
            "median_speedup_b_over_c": tb / tc,
            "solver_b_times": json.dumps(raw_b),
            "solver_c_times": json.dumps(raw_c),
            "solver_b_complete_candidates": b.states_examined,
            "solver_c_complete_candidates": c.states_examined,
            "solver_c_recursion_nodes": c.metadata["recursion_nodes"],
        }
        rows.append(row)
        print(
            f"{family:14s} {name:22s} n={len(G):2d} mu={b.mu:2d} "
            f"Bmed={tb:8.5f}s Cmed={tc:8.5f}s speedup={tb/tc:7.2f}x",
            flush=True,
        )

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "cases": len(rows),
        "repeats": REPEATS,
        "all_median_speedup": median(r["median_speedup_b_over_c"] for r in rows),
        "families": {},
        "all_results_equal": True,
    }
    for family in sorted({r["family"] for r in rows}):
        vals = [r["median_speedup_b_over_c"] for r in rows if r["family"] == family]
        summary["families"][family] = {
            "cases": len(vals),
            "median_speedup": median(vals),
            "min_speedup": min(vals),
            "max_speedup": max(vals),
        }
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
