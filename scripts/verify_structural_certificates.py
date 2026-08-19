#!/usr/bin/env python3
"""Machine-check the structural identities used in the manuscript."""

from __future__ import annotations

import json

from _repo import ROOT, decode_graph6
from src.constructions import extremal_graph_for_order_direct
from src.structure import analyze_maximal_acyclic_matching


def main() -> None:
    path = ROOT / "data" / "counterexamples" / "metadata.json"
    for record in json.loads(path.read_text(encoding="utf-8"))["graphs"]:
        graph = decode_graph6(record["graph6"])
        matching = tuple(tuple(edge) for edge in record["optimal_matching"])
        analyze_maximal_acyclic_matching(graph, matching)
        print(f"counterexample {record['paper_id']}: structural certificate PASS")
    for n in range(4, 58, 2):
        item = extremal_graph_for_order_direct(n)
        certificate = analyze_maximal_acyclic_matching(item.graph, item.matching)
        if certificate.n != n:
            raise AssertionError(f"n={n}: certificate order mismatch")
        print(f"construction n={n}: structural certificate PASS")


if __name__ == "__main__":
    main()

