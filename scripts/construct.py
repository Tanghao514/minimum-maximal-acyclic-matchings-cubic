#!/usr/bin/env python3
"""Construct and verify a sharpness example at any admissible even order."""

from __future__ import annotations

import argparse
import json
from math import ceil
from pathlib import Path

from _repo import encode_graph6
from src.acyclic_matching import is_acyclic_matching, is_matching, is_maximal_acyclic_matching
from src.constructions import extremal_graph_for_order_direct
from src.structure import analyze_maximal_acyclic_matching


def construction_payload(n: int) -> dict[str, object]:
    item = extremal_graph_for_order_direct(n)
    graph, matching = item.graph, item.matching
    expected = ceil((n - 1) / 5)
    checks = {
        "simple": not graph.is_multigraph() and not any(u == v for u, v in graph.edges),
        "connected": __import__("networkx").is_connected(graph),
        "cubic": all(degree == 3 for _, degree in graph.degree),
        "matching": is_matching(graph, matching),
        "acyclic": is_acyclic_matching(graph, matching),
        "maximal": is_maximal_acyclic_matching(graph, matching),
        "sharp_size": len(matching) == expected,
    }
    if not all(checks.values()):
        raise AssertionError(f"construction failed: {checks}")
    structure = analyze_maximal_acyclic_matching(graph, matching).to_dict()
    return {
        "n": n,
        "formula_value": expected,
        "graph6": encode_graph6(graph),
        "matching": [list(edge) for edge in matching],
        "construction": item.metadata,
        "checks": checks,
        "structural_certificate": structure,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, required=True, help="even order n >= 4")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-g6", type=Path)
    args = parser.parse_args()
    payload = construction_payload(args.n)
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(rendered + "\n", encoding="utf-8")
    if args.output_g6:
        args.output_g6.parent.mkdir(parents=True, exist_ok=True)
        args.output_g6.write_text(str(payload["graph6"]) + "\n", encoding="ascii")
    print(rendered)


if __name__ == "__main__":
    main()

