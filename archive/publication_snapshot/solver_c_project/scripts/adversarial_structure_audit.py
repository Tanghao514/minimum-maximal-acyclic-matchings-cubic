"""Independent adversarial audit of the structural proof.

This script deliberately does not import the project's structural analyzer or
maximality predicate.  It recomputes all relevant facts directly with NetworkX.
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]

Edge = tuple[int, int]


def all_matchings(G: nx.Graph) -> Iterator[tuple[Edge, ...]]:
    """Enumerate every matching once by a standard include/exclude recursion."""
    edges = tuple((min(u, v), max(u, v)) for u, v in G.edges())
    chosen: list[Edge] = []

    def rec(i: int, used: set[int]) -> Iterator[tuple[Edge, ...]]:
        if i == len(edges):
            yield tuple(chosen)
            return
        yield from rec(i + 1, used)
        u, v = edges[i]
        if u not in used and v not in used:
            chosen.append((u, v))
            used.add(u)
            used.add(v)
            yield from rec(i + 1, used)
            used.remove(u)
            used.remove(v)
            chosen.pop()

    yield from rec(0, set())


def endpoint_set(M: Iterable[Edge]) -> set[int]:
    return {x for e in M for x in e}


def direct_acyclic(G: nx.Graph, M: tuple[Edge, ...]) -> bool:
    S = endpoint_set(M)
    return not S or nx.is_forest(G.subgraph(S))


def f_component_data(G: nx.Graph, S: set[int]):
    F = G.subgraph(S)
    comps = [set(C) for C in nx.connected_components(F)]
    comp_of = {v: i for i, C in enumerate(comps) for v in C}
    return F, comps, comp_of


def blocker_predicate(
    G: nx.Graph, S: set[int], comp_of: dict[int, int], u: int, v: int
) -> bool:
    """Predict whether G[S union {u,v}] has a cycle, using only the lemma."""
    labels_u = [comp_of[x] for x in G.neighbors(u) if x in S]
    labels_v = [comp_of[x] for x in G.neighbors(v) if x in S]
    self_u = len(labels_u) != len(set(labels_u))
    self_v = len(labels_v) != len(set(labels_v))
    shared = bool(set(labels_u) & set(labels_v))
    return self_u or self_v or shared


def direct_maximal(G: nx.Graph, M: tuple[Edge, ...]) -> bool:
    if not direct_acyclic(G, M):
        return False
    S = endpoint_set(M)
    for u, v in G.edges():
        if u in S or v in S:
            continue
        if nx.is_forest(G.subgraph(S | {u, v})):
            return False
    return True


def classify_component(J: nx.Graph) -> str:
    n = len(J)
    degs = sorted(dict(J.degree()).values())
    if n == 1:
        return "P1"
    if nx.is_tree(J):
        if max(degs) <= 2:
            return f"P{n}"
        if n == 4 and degs == [1, 1, 1, 3]:
            return "K1,3"
        return "forbidden-tree"
    if J.number_of_edges() == n and all(d == 2 for d in degs):
        return f"C{n}"
    return "forbidden-nontree"


def audit_maximal_structure(G: nx.Graph, M: tuple[Edge, ...]) -> dict[str, object]:
    S = endpoint_set(M)
    U = set(G) - S
    F, fcomps, f_of = f_component_data(G, S)
    H = G.subgraph(U)

    t = 0
    h_types: list[str] = []
    incidence_edges: set[tuple[int, int]] = set()
    tree_neighbor_counts: list[int] = []

    hcomps = [set(C) for C in nx.connected_components(H)]
    for j, C in enumerate(hcomps):
        J = H.subgraph(C)
        typ = classify_component(J)
        if typ.startswith("forbidden"):
            raise AssertionError(("forbidden H component", typ, sorted(C), nx.to_graph6_bytes(G, header=False)))
        labels = {f_of[s] for u in C for s in G.neighbors(u) if s in S}
        incidence_edges.update((i, j) for i in labels)
        if nx.is_tree(J):
            t += 1
            tree_neighbor_counts.append(len(labels))
            if len(labels) > 3:
                raise AssertionError(("tree H component touches >3 F components", typ, labels))
        else:
            if len(labels) != 1:
                raise AssertionError(("cycle H component does not touch exactly one F component", typ, labels))
        h_types.append(typ)

    c = len(fcomps)
    k = len(M)
    if F.number_of_edges() != 2 * k - c:
        raise AssertionError("forest edge count failed")
    e_su = sum((u in S) ^ (v in S) for u, v in G.edges())
    if e_su != 2 * k + 2 * c:
        raise AssertionError("S-side cut count failed")
    if e_su != len(U) + 2 * t:
        raise AssertionError("U-side cut count failed")
    if len(G) != 4 * k + 2 * (c - t):
        raise AssertionError("master identity failed")

    B = nx.Graph()
    B.add_nodes_from(("F", i) for i in range(c))
    B.add_nodes_from(("H", j) for j in range(len(hcomps)))
    B.add_edges_from((("F", i), ("H", j)) for i, j in incidence_edges)
    if len(B) > 1 and not nx.is_connected(B):
        raise AssertionError("full incidence graph disconnected")

    cycle_h = [j for j, C in enumerate(hcomps) if not nx.is_tree(H.subgraph(C))]
    core = B.copy()
    core.remove_nodes_from(("H", j) for j in cycle_h)
    if len(core) > 1 and not nx.is_connected(core):
        raise AssertionError("incidence core disconnected after deleting cycle leaves")
    if c > 2 * t + 1:
        raise AssertionError(("c <= 2t+1 failed", c, t))
    if c > k:
        raise AssertionError(("c <= k failed", c, k))

    parity_upper = 5 * k + (k % 2)
    if len(G) > parity_upper:
        raise AssertionError(("parity upper bound failed", len(G), k, parity_upper))

    return {
        "k": k,
        "c": c,
        "t": t,
        "h_types": h_types,
        "max_tree_f_neighbors": max(tree_neighbor_counts, default=0),
    }


def graph_suite() -> list[tuple[str, nx.Graph]]:
    suite: list[tuple[str, nx.Graph]] = [
        ("K4", nx.complete_graph(4)),
        ("K33", nx.complete_bipartite_graph(3, 3)),
        ("triangular_prism", nx.circular_ladder_graph(3)),
        ("cube", nx.cubical_graph()),
        ("petersen", nx.petersen_graph()),
        ("pentagonal_prism", nx.circular_ladder_graph(5)),
        ("hexagonal_prism", nx.circular_ladder_graph(6)),
        ("heawood", nx.heawood_graph()),
        ("moebius_k4", nx.complete_graph(4)),
    ]
    rng = random.Random(20260816)
    # Exhaustive matching enumeration remains quick at these orders, while the
    # random graphs exercise many local configurations independently.
    counts = {8: 8, 10: 10, 12: 10, 14: 6, 16: 4}
    for n, count in counts.items():
        seen: set[bytes] = set()
        attempts = 0
        while len(seen) < count and attempts < 20000:
            attempts += 1
            G = nx.random_regular_graph(3, n, seed=rng.randrange(2**63))
            if not nx.is_connected(G):
                continue
            G = nx.convert_node_labels_to_integers(G, ordering="sorted")
            # This key only removes identical labelled samples; isomorphic
            # duplicates are harmless for an adversarial audit.
            key = nx.to_graph6_bytes(G, header=False)
            if key in seen:
                continue
            seen.add(key)
            suite.append((f"random_cubic_{n}_{len(seen)-1}", G))
    return suite


def main() -> None:
    totals = Counter()
    type_counts = Counter()
    size_counts = Counter()
    per_graph: list[dict[str, object]] = []

    for name, G in graph_suite():
        if not (nx.is_connected(G) and all(d == 3 for _, d in G.degree())):
            raise AssertionError(f"bad cubic input {name}")
        graph_matchings = graph_acyclic = graph_maximal = 0
        for M in all_matchings(G):
            graph_matchings += 1
            S = endpoint_set(M)
            if not direct_acyclic(G, M):
                continue
            graph_acyclic += 1
            _, _, comp_of = f_component_data(G, S)
            maximal = True
            for u, v in G.edges():
                if u in S or v in S:
                    continue
                predicted_cycle = blocker_predicate(G, S, comp_of, u, v)
                actual_cycle = not nx.is_forest(G.subgraph(S | {u, v}))
                totals["extension_edges_checked"] += 1
                if predicted_cycle != actual_cycle:
                    raise AssertionError(
                        {
                            "kind": "local blocker equivalence failed",
                            "graph": name,
                            "matching": M,
                            "edge": (u, v),
                            "predicted_cycle": predicted_cycle,
                            "actual_cycle": actual_cycle,
                            "graph6": nx.to_graph6_bytes(G, header=False).decode().strip(),
                        }
                    )
                if not actual_cycle:
                    maximal = False
            if not maximal:
                continue
            graph_maximal += 1
            info = audit_maximal_structure(G, M)
            type_counts.update(info["h_types"])
            size_counts[len(M)] += 1

        totals["graphs"] += 1
        totals["matchings"] += graph_matchings
        totals["acyclic_matchings"] += graph_acyclic
        totals["maximal_acyclic_matchings"] += graph_maximal
        per_graph.append(
            {
                "name": name,
                "n": len(G),
                "matchings": graph_matchings,
                "acyclic_matchings": graph_acyclic,
                "maximal_acyclic_matchings": graph_maximal,
            }
        )
        print(
            f"{name:28s} n={len(G):2d} matchings={graph_matchings:8d} "
            f"acyclic={graph_acyclic:8d} maximal={graph_maximal:6d}",
            flush=True,
        )

    result = {
        "seed": 20260816,
        "status": "PASS: no counterexample to any audited structural lemma",
        "totals": dict(totals),
        "H_component_type_counts": dict(sorted(type_counts.items())),
        "maximal_matching_size_counts": {str(k): v for k, v in sorted(size_counts.items())},
        "graphs": per_graph,
        "independence_note": (
            "The script imports neither src.structure nor the project's maximality predicate; "
            "all cycle, maximality, incidence, and counting checks are recomputed directly."
        ),
    }
    out = ROOT / "results" / "adversarial_structure_audit.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["totals"], indent=2))
    print(result["status"])


if __name__ == "__main__":
    main()
