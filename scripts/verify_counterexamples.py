#!/usr/bin/env python3
"""Verify all four order-16 counterexamples and their paper metadata."""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

import networkx as nx

from _repo import ROOT, decode_graph6
from src.acyclic_matching import is_acyclic_matching, is_matching, is_maximal_acyclic_matching
from src.exact_solver import minimum_maximal_acyclic_matching
from src.structure import analyze_maximal_acyclic_matching


def triangle_count(graph: nx.Graph) -> int:
    return sum(nx.triangles(graph).values()) // 3


def four_cycle_count(graph: nx.Graph) -> int:
    opposite_pair_counts = 0
    for u, v in combinations(graph.nodes, 2):
        common = len(set(graph[u]).intersection(graph[v]))
        opposite_pair_counts += common * (common - 1) // 2
    return opposite_pair_counts // 2


def no_solution_below_three(graph: nx.Graph) -> bool:
    edges = tuple(graph.edges)
    for size in range(3):
        if any(is_maximal_acyclic_matching(graph, candidate) for candidate in combinations(edges, size)):
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metadata", type=Path, default=ROOT / "data" / "counterexamples" / "metadata.json"
    )
    parser.add_argument("--write-report", type=Path)
    args = parser.parse_args()
    records = json.loads(args.metadata.read_text(encoding="utf-8"))["graphs"]
    report: list[dict[str, object]] = []
    for record in records:
        graph = decode_graph6(record["graph6"])
        matching = tuple(tuple(edge) for edge in record["optimal_matching"])
        mapped = decode_graph6(record["geng_census_graph6"])
        result = minimum_maximal_acyclic_matching(graph)
        observed = {
            "cubic": all(degree == 3 for _, degree in graph.degree),
            "connected": nx.is_connected(graph),
            "simple": not graph.is_multigraph() and not any(u == v for u, v in graph.edges),
            "matching": is_matching(graph, matching),
            "acyclic": is_acyclic_matching(graph, matching),
            "maximal": is_maximal_acyclic_matching(graph, matching),
            "no_size_0_1_2_solution": no_solution_below_three(graph),
            "optimum_is_3": result.mu == 3,
            "diameter": nx.diameter(graph) == record["diameter"],
            "bridges": len(list(nx.bridges(graph))) == record["bridges"],
            "triangles": triangle_count(graph) == record["triangles"],
            "four_cycles": four_cycle_count(graph) == record["c4_count"],
            "isomorphic_to_geng_record": nx.is_isomorphic(graph, mapped),
        }
        if not all(observed.values()):
            failures = [name for name, passed in observed.items() if not passed]
            raise AssertionError(f"graph {record['paper_id']}: failed {failures}")
        structure = analyze_maximal_acyclic_matching(graph, matching).to_dict()
        report.append({"paper_id": record["paper_id"], "checks": observed, "structure": structure})
        print(f"graph {record['paper_id']}: PASS")
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(json.dumps({"graphs": report}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

