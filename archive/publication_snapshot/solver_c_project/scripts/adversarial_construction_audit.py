"""Direct-definition audit of every even-order sharpness construction.

Only the graph constructors are imported.  Matching, acyclicity, maximality,
and arithmetic are checked here from scratch rather than through project
validation helpers.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from math import ceil
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.constructions import extremal_graph_for_order  # noqa: E402


def endpoints(M):
    return {x for e in M for x in e}


def direct_check(n: int):
    item = extremal_graph_for_order(n)
    G = item.graph
    M = tuple(item.matching)

    assert isinstance(G, nx.Graph) and not G.is_directed() and not G.is_multigraph()
    assert len(G) == n
    assert nx.number_of_selfloops(G) == 0
    assert G.number_of_edges() == 3 * n // 2
    assert nx.is_connected(G)
    assert all(d == 3 for _, d in G.degree())

    graph_edges = {frozenset(e) for e in G.edges()}
    used = set()
    for u, v in M:
        assert u != v and frozenset((u, v)) in graph_edges
        assert u not in used and v not in used
        used.update((u, v))

    S = endpoints(M)
    U = set(G) - S
    F = G.subgraph(S)
    assert nx.is_forest(F)

    # Maximality under the exact induced-subgraph definition.  For orders up
    # to 120 we call NetworkX's forest test on every candidate extension.  For
    # all larger orders we use an independent union-of-tree-components test:
    # F is a forest, so adding u,v and uv creates a cycle exactly when u or v
    # hits one F-component twice, or they hit a common F-component.
    f_components = [set(C) for C in nx.connected_components(F)]
    f_of = {x: i for i, C in enumerate(f_components) for x in C}
    addable = []
    blocked_cycle_lengths = Counter()
    for u, v in G.subgraph(U).edges():
        labels_u = [f_of[x] for x in G.neighbors(u) if x in S]
        labels_v = [f_of[x] for x in G.neighbors(v) if x in S]
        fast_cycle = (
            len(labels_u) != len(set(labels_u))
            or len(labels_v) != len(set(labels_v))
            or bool(set(labels_u) & set(labels_v))
        )
        if n <= 120:
            J = G.subgraph(S | {u, v})
            direct_cycle = not nx.is_forest(J)
            assert direct_cycle == fast_cycle
            if direct_cycle:
                cycle = nx.find_cycle(J)
                blocked_cycle_lengths[len(cycle)] += 1
        if not fast_cycle:
            addable.append((u, v))
    assert not addable

    k = len(M)
    assert k == ceil((n - 1) / 5)
    assert n <= 5 * k + (k % 2)

    # Graph6 must reproduce the same simple graph up to isomorphism.
    g6 = nx.to_graph6_bytes(G, header=False)
    R = nx.from_graph6_bytes(g6.strip())
    assert len(R) == len(G)
    assert nx.to_graph6_bytes(R, header=False).strip() == g6.strip()
    assert nx.is_connected(R) and all(d == 3 for _, d in R.degree())

    return {
        "n": n,
        "k": k,
        "family": item.metadata.get("family", "unknown"),
        "u_edges": G.subgraph(U).number_of_edges(),
        "blocked_cycle_length_counts": dict(sorted(blocked_cycle_lengths.items())),
        "graph6": g6.decode().strip(),
    }


def main():
    rows = []
    family_counts = Counter()
    cycle_counts = Counter()
    # Check every admissible order through 300; this covers all residue cases
    # many times while keeping the audit reproducible on modest hardware.
    for n in range(4, 302, 2):
        row = direct_check(n)
        rows.append(row)
        family_counts[row["family"]] += 1
        cycle_counts.update(row["blocked_cycle_length_counts"])
        if n <= 30 or n % 100 == 0:
            print(n, row["k"], row["family"], flush=True)

    result = {
        "status": "PASS: direct-definition verification for every even n from 4 through 300",
        "orders_checked": len(rows),
        "min_order": rows[0]["n"],
        "max_order": rows[-1]["n"],
        "family_counts": dict(sorted(family_counts.items())),
        "aggregate_blocking_cycle_length_counts": {
            str(k): v for k, v in sorted(cycle_counts.items())
        },
        "rows": rows,
    }
    out = ROOT / "results" / "adversarial_construction_audit_n4_n300.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(result["status"])


if __name__ == "__main__":
    main()
