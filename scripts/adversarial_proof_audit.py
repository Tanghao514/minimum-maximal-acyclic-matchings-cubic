"""Independent adversarial checks for the cubic lower-bound proof.

This script deliberately does not import src.structure or the reference
acyclic-matching predicates.  It checks:
  1. the local H-component lemmas by exhaustive abstract label enumeration
     for every connected subcubic graph in NetworkX's graph atlas (<=7 vertices);
  2. all-order extremal constructions by direct induced-subgraph cycle tests;
  3. the integer optimization used in the lower bound.
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
from src.constructions import extremal_graph_for_order  # construction only


def restricted_growth_strings(n: int):
    """Enumerate set partitions of n labelled slots canonically."""
    if n == 0:
        yield ()
        return
    a = [0] * n

    def rec(i: int, maximum: int):
        if i == n:
            yield tuple(a)
            return
        for value in range(maximum + 2):
            a[i] = value
            yield from rec(i + 1, max(maximum, value))

    yield from rec(1, 0)


def edge_is_blocked(labels_u: tuple[int, ...], labels_v: tuple[int, ...]) -> bool:
    self_u = len(set(labels_u)) < len(labels_u)
    self_v = len(set(labels_v)) < len(labels_v)
    shared = bool(set(labels_u) & set(labels_v))
    return self_u or self_v or shared


def permitted_h_component(J: nx.Graph) -> bool:
    n = len(J)
    degrees = sorted(dict(J.degree()).values())
    if n == 1:
        return True
    if J.number_of_edges() == n and all(d == 2 for d in degrees):
        return True
    if nx.is_tree(J):
        if max(degrees) <= 2:
            return True
        if n == 4 and degrees == [1, 1, 1, 3]:
            return True
    return False


def audit_local_component_lemmas() -> dict:
    atlas = [
        nx.convert_node_labels_to_integers(G)
        for G in nx.graph_atlas_g()
        if len(G) >= 1
        and nx.is_connected(G)
        and max(dict(G.degree()).values(), default=0) <= 3
    ]
    assignments_checked = 0
    valid_assignments = 0
    type_counts: Counter[str] = Counter()

    for J in atlas:
        slots: list[int] = []
        for v in J:
            slots.extend([v] * (3 - J.degree(v)))

        for partition in restricted_growth_strings(len(slots)):
            assignments_checked += 1
            by_vertex: dict[int, list[int]] = {v: [] for v in J}
            for v, label in zip(slots, partition, strict=True):
                by_vertex[v].append(label)
            labels = {v: tuple(values) for v, values in by_vertex.items()}

            if not all(edge_is_blocked(labels[u], labels[v]) for u, v in J.edges):
                continue
            valid_assignments += 1

            if not permitted_h_component(J):
                raise AssertionError(
                    "forbidden H component satisfies all local blocking constraints: "
                    + nx.to_graph6_bytes(J, header=False).decode().strip()
                )

            touched = len(set(partition)) if partition else 0
            if nx.is_tree(J) and touched > 3:
                raise AssertionError("an H-tree component can touch more than three F-components")
            if (
                J.number_of_edges() == len(J)
                and all(d == 2 for _, d in J.degree)
                and touched > 1
            ):
                raise AssertionError("an H-cycle component can touch more than one F-component")

        if len(J) == 1:
            type_counts["P1"] += 1
        elif nx.is_tree(J) and max(dict(J.degree()).values()) <= 2:
            type_counts[f"P{len(J)}"] += 1
        elif nx.is_tree(J):
            type_counts["K1,3-or-forbidden-tree"] += 1
        elif J.number_of_edges() == len(J) and all(d == 2 for _, d in J.degree):
            type_counts[f"C{len(J)}"] += 1
        else:
            type_counts["forbidden-shape"] += 1

    return {
        "atlas_connected_subcubic_graphs": len(atlas),
        "abstract_label_assignments_checked": assignments_checked,
        "valid_blocking_assignments": valid_assignments,
        "status": "pass",
    }


def is_forest_direct(J: nx.Graph) -> bool:
    """Independent DFS cycle test; no nx.is_forest call."""
    seen: set[int] = set()
    for root in J:
        if root in seen:
            continue
        stack = [(root, None)]
        seen.add(root)
        while stack:
            v, parent = stack.pop()
            for w in J.neighbors(v):
                if w == parent:
                    continue
                if w in seen:
                    return False
                seen.add(w)
                stack.append((w, v))
    return True


def direct_witness_check(G: nx.Graph, matching: tuple[tuple[int, int], ...]) -> None:
    if G.is_directed() or nx.number_of_selfloops(G):
        raise AssertionError("construction is not a finite simple undirected graph")
    if not nx.is_connected(G) or any(d != 3 for _, d in G.degree):
        raise AssertionError("construction is not connected cubic")

    used: set[int] = set()
    graph_edges = {frozenset(e) for e in G.edges}
    for u, v in matching:
        if frozenset((u, v)) not in graph_edges or u in used or v in used:
            raise AssertionError("distinguished set is not a matching")
        used.update((u, v))

    F = G.subgraph(used).copy()
    if not is_forest_direct(F):
        raise AssertionError("G[V(M)] is not a forest")

    U = set(G) - used
    for u, v in G.subgraph(U).edges:
        enlarged = G.subgraph(used | {u, v}).copy()
        if is_forest_direct(enlarged):
            raise AssertionError(f"matching is not maximal; addable edge {(u, v)}")


def audit_all_order_constructions(max_n: int = 300) -> dict:
    checked = 0
    family_counts: Counter[str] = Counter()
    for n in range(4, max_n + 1, 2):
        item = extremal_graph_for_order(n)
        direct_witness_check(item.graph, item.matching)
        target = ceil((n - 1) / 5)
        if len(item.matching) != target:
            raise AssertionError((n, len(item.matching), target))
        checked += 1
        family_counts[str(item.metadata.get("family"))] += 1
    return {
        "orders_checked": checked,
        "range": f"4..{max_n} even",
        "family_counts": dict(sorted(family_counts.items())),
        "status": "pass",
    }


def audit_integer_optimization(max_k: int = 500) -> dict:
    for k in range(1, max_k + 1):
        best = -10**9
        witnesses = []
        for t in range(0, 2 * k + 3):
            for c in range(1, k + 1):
                if c <= 2 * t + 1:
                    value = c - t
                    if value > best:
                        best = value
                        witnesses = [(c, t)]
                    elif value == best:
                        witnesses.append((c, t))
        if best != ceil(k / 2):
            raise AssertionError((k, best, ceil(k / 2), witnesses))
        upper = 4 * k + 2 * best
        expected = 5 * k + (k % 2)
        if upper != expected:
            raise AssertionError((k, upper, expected))
    return {"k_checked": max_k, "status": "pass"}


def main() -> None:
    result = {
        "local_component_audit": audit_local_component_lemmas(),
        "all_order_construction_audit": audit_all_order_constructions(),
        "integer_optimization_audit": audit_integer_optimization(),
        "overall_status": "pass",
    }
    out = ROOT / "results" / "adversarial_proof_audit.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
