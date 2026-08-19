"""Independent adversarial audit of the one-fifth theorem.

This script intentionally reimplements all definition and structural checks without
calling ``src.acyclic_matching`` or ``src.structure``.  NetworkX is used only as a
graph container/generator; matching, induced-forest, maximality, component, local
blocking, and incidence calculations below are independent code paths.
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, deque
from itertools import combinations
from math import ceil
from pathlib import Path
from time import perf_counter

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.constructions import (  # noqa: E402
    extremal_graph_for_order,
    extremal_graph_for_order_direct,
)
from src.exact_solver import minimum_maximal_acyclic_matching  # noqa: E402

Edge = tuple[int, int]


class DSU:
    def __init__(self, vertices: set[int]) -> None:
        self.parent = {v: v for v in vertices}
        self.rank = {v: 0 for v in vertices}

    def find(self, x: int) -> int:
        p = self.parent[x]
        if p != x:
            self.parent[x] = self.find(p)
        return self.parent[x]

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def endpoint_set(M: tuple[Edge, ...]) -> set[int]:
    return {x for e in M for x in e}


def raw_is_matching(G: nx.Graph, M: tuple[Edge, ...]) -> bool:
    edges = {frozenset(e) for e in G.edges}
    used: set[int] = set()
    for u, v in M:
        if u == v or frozenset((u, v)) not in edges or u in used or v in used:
            return False
        used.add(u)
        used.add(v)
    return True


def raw_induced_forest(G: nx.Graph, vertices: set[int]) -> bool:
    dsu = DSU(vertices)
    for u, v in G.edges:
        if u in vertices and v in vertices:
            if not dsu.union(u, v):
                return False
    return True


def raw_is_acyclic_matching(G: nx.Graph, M: tuple[Edge, ...]) -> bool:
    return raw_is_matching(G, M) and raw_induced_forest(G, endpoint_set(M))


def raw_is_maximal_acyclic_matching(G: nx.Graph, M: tuple[Edge, ...]) -> bool:
    if not raw_is_acyclic_matching(G, M):
        return False
    S = endpoint_set(M)
    for u, v in G.edges:
        if u not in S and v not in S:
            if raw_induced_forest(G, S | {u, v}):
                return False
    return True


def components(G: nx.Graph, vertices: set[int]) -> list[set[int]]:
    unseen = set(vertices)
    out: list[set[int]] = []
    while unseen:
        start = next(iter(unseen))
        unseen.remove(start)
        comp = {start}
        q = deque([start])
        while q:
            u = q.popleft()
            for v in G.neighbors(u):
                if v in unseen:
                    unseen.remove(v)
                    comp.add(v)
                    q.append(v)
        out.append(comp)
    return out


def local_blocking_prediction(
    G: nx.Graph,
    S: set[int],
    f_index: dict[int, int],
    u: int,
    v: int,
) -> bool:
    counts_u: Counter[int] = Counter(f_index[x] for x in G.neighbors(u) if x in S)
    counts_v: Counter[int] = Counter(f_index[x] for x in G.neighbors(v) if x in S)
    self_u = any(value >= 2 for value in counts_u.values())
    self_v = any(value >= 2 for value in counts_v.values())
    common = bool(set(counts_u) & set(counts_v))
    return self_u or self_v or common


def raw_structural_audit(G: nx.Graph, M: tuple[Edge, ...]) -> dict[str, int]:
    if not raw_is_maximal_acyclic_matching(G, M):
        raise AssertionError("invalid maximal acyclic matching")
    if not nx.is_connected(G) or any(d != 3 for _, d in G.degree):
        raise AssertionError("connected cubic graph required")

    k = len(M)
    S = endpoint_set(M)
    U = set(G) - S
    f_comps = components(G, S)
    h_comps = components(G, U)
    f_index = {v: i for i, C in enumerate(f_comps) for v in C}

    c = len(f_comps)
    t = 0
    cycle_count = 0
    incidence: set[tuple[int, int]] = set()

    # Local blocking equivalence and structural classification.
    for u, v in G.edges:
        if u in U and v in U:
            predicted = local_blocking_prediction(G, S, f_index, u, v)
            actual = not raw_induced_forest(G, S | {u, v})
            if predicted != actual:
                raise AssertionError("local blocking criterion mismatch")
            if not actual:
                raise AssertionError("maximality failed on an H-edge")

    for j, C in enumerate(h_comps):
        degrees = sorted(sum(v in C for v in G.neighbors(u)) for u in C)
        edge_count = sum(degrees) // 2
        is_tree = edge_count == len(C) - 1
        is_cycle = edge_count == len(C) and all(d == 2 for d in degrees)
        if is_tree:
            t += 1
            if len(C) == 1:
                pass
            elif max(degrees) <= 2:
                if degrees.count(1) != 2:
                    raise AssertionError("tree of max degree 2 is not a path")
            elif len(C) == 4 and degrees == [1, 1, 1, 3]:
                pass
            else:
                raise AssertionError(f"forbidden H-tree degree sequence {degrees}")
        elif is_cycle:
            cycle_count += 1
        else:
            raise AssertionError("H-component is neither a path, cycle, nor K1,3")

        adjacent_f = {
            f_index[s]
            for u in C
            for s in G.neighbors(u)
            if s in S
        }
        incidence.update((i, j) for i in adjacent_f)
        if is_tree and len(adjacent_f) > 3:
            raise AssertionError("H-tree component sees more than three F-components")
        if is_cycle and len(adjacent_f) != 1:
            raise AssertionError("H-cycle component does not see exactly one F-component")

    # Quotient incidence graph: verify connectivity by raw BFS.
    quotient_vertices = {("F", i) for i in range(c)} | {
        ("H", j) for j in range(len(h_comps))
    }
    quotient_adj = {x: set() for x in quotient_vertices}
    for i, j in incidence:
        a, b = ("F", i), ("H", j)
        quotient_adj[a].add(b)
        quotient_adj[b].add(a)
    seen = set()
    if quotient_vertices:
        q = deque([next(iter(quotient_vertices))])
        seen.add(q[0])
        while q:
            x = q.popleft()
            for y in quotient_adj[x]:
                if y not in seen:
                    seen.add(y)
                    q.append(y)
    if seen != quotient_vertices:
        raise AssertionError("component incidence graph is disconnected")

    # Delete H-cycle leaves and verify that the remaining core is connected.
    cycle_indices = set()
    for j, C in enumerate(h_comps):
        degrees = [sum(v in C for v in G.neighbors(u)) for u in C]
        if len(C) >= 3 and all(d == 2 for d in degrees):
            cycle_indices.add(j)
    core = {("F", i) for i in range(c)} | {
        ("H", j) for j in range(len(h_comps)) if j not in cycle_indices
    }
    core_seen: set[tuple[str, int]] = set()
    if core:
        q = deque([next(iter(core))])
        core_seen.add(q[0])
        while q:
            x = q.popleft()
            for y in quotient_adj[x]:
                if y in core and y not in core_seen:
                    core_seen.add(y)
                    q.append(y)
    if core_seen != core:
        raise AssertionError("incidence core disconnected after deleting cycle leaves")

    e_f = sum(1 for u, v in G.edges if u in S and v in S)
    e_h = sum(1 for u, v in G.edges if u in U and v in U)
    e_su = sum(1 for u, v in G.edges if (u in S) ^ (v in S))
    if e_f != 2 * k - c:
        raise AssertionError("F forest edge count failed")
    if e_h != len(U) - t:
        raise AssertionError("H pseudoforest edge count failed")
    if e_su != 2 * k + 2 * c or e_su != len(U) + 2 * t:
        raise AssertionError("cut-edge identities failed")
    if len(G) != 4 * k + 2 * (c - t):
        raise AssertionError("master identity failed")
    if c > k or c > 2 * t + 1:
        raise AssertionError("component inequalities failed")
    if c - t > ceil(k / 2):
        raise AssertionError("optimization inequality failed")
    if len(G) > 5 * k + (k % 2):
        raise AssertionError("parity-refined upper bound failed")
    if k < ceil((len(G) - 1) / 5):
        raise AssertionError("one-fifth theorem failed")

    return {
        "n": len(G),
        "k": k,
        "c": c,
        "t": t,
        "h_cycles": cycle_count,
    }


def all_matchings(G: nx.Graph):
    edges = tuple(G.edges)
    chosen: list[Edge] = []

    def rec(i: int, used: set[int]):
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


def exhaustive_local_suite() -> dict[str, object]:
    graphs = [
        ("K4", nx.complete_graph(4)),
        ("K33", nx.complete_bipartite_graph(3, 3)),
        ("triangular_prism", nx.circular_ladder_graph(3)),
        ("cube", nx.cubical_graph()),
        ("petersen", nx.petersen_graph()),
        ("pentagonal_prism", nx.circular_ladder_graph(5)),
    ]
    rows = []
    total_matchings = total_acyclic = total_maximal = local_edge_tests = 0
    for name, G in graphs:
        gm = ga = gx = 0
        for M in all_matchings(G):
            gm += 1
            acyclic = raw_is_acyclic_matching(G, M)
            if not acyclic:
                continue
            ga += 1
            S = endpoint_set(M)
            f_comps = components(G, S) if S else []
            f_index = {v: i for i, C in enumerate(f_comps) for v in C}
            for u, v in G.edges:
                if u not in S and v not in S:
                    predicted = local_blocking_prediction(G, S, f_index, u, v)
                    actual = not raw_induced_forest(G, S | {u, v})
                    local_edge_tests += 1
                    if predicted != actual:
                        raise AssertionError("local lemma failed on an acyclic matching")
            if raw_is_maximal_acyclic_matching(G, M):
                gx += 1
                raw_structural_audit(G, M)
        rows.append(
            {
                "name": name,
                "n": len(G),
                "matchings": gm,
                "acyclic": ga,
                "maximal": gx,
            }
        )
        total_matchings += gm
        total_acyclic += ga
        total_maximal += gx
    return {
        "graphs": rows,
        "total_matchings": total_matchings,
        "total_acyclic": total_acyclic,
        "total_maximal": total_maximal,
        "local_edge_tests": local_edge_tests,
    }


def construction_suite() -> dict[str, object]:
    direct = old = 0
    equality_rows = []
    for n in range(4, 502, 2):
        for builder_name, builder in (
            ("direct", extremal_graph_for_order_direct),
            ("replacement", extremal_graph_for_order),
        ):
            item = builder(n)
            cert = raw_structural_audit(item.graph, item.matching)
            expected = ceil((n - 1) / 5)
            if len(item.graph) != n or len(item.matching) != expected:
                raise AssertionError("sharpness construction failed")
            if builder_name == "direct":
                direct += 1
                if n <= 40:
                    equality_rows.append(cert)
            else:
                old += 1
    return {
        "orders_checked_per_builder": direct,
        "direct_certificates_n_le_40": equality_rows,
        "replacement_orders_checked": old,
    }


def random_exact_suite() -> dict[str, object]:
    rng = random.Random(20260816)
    rows = []
    total = 0
    start = perf_counter()
    schedule = {14: 12, 16: 12, 18: 10, 20: 10, 22: 8, 24: 4}
    for n, count in schedule.items():
        for j in range(count):
            while True:
                G = nx.random_regular_graph(3, n, seed=rng.randrange(2**32))
                if nx.is_connected(G):
                    break
            sol = minimum_maximal_acyclic_matching(G)
            if not raw_is_maximal_acyclic_matching(G, tuple(sol.matching)):
                raise AssertionError("exact solver witness failed independent definition")
            raw_structural_audit(G, tuple(sol.matching))
            lower = ceil((n - 1) / 5)
            if sol.mu < lower:
                raise AssertionError("random exact lower-bound counterexample")
            rows.append(
                {
                    "n": n,
                    "sample": j,
                    "mu": sol.mu,
                    "lower": lower,
                    "runtime_seconds": sol.runtime_seconds,
                }
            )
            total += 1
    return {
        "graphs": total,
        "runtime_seconds": perf_counter() - start,
        "rows": rows,
    }


def main() -> None:
    result = {
        "status": "passed",
        "independence_note": (
            "Definition, DSU forest, maximality, local blocking, H-component, "
            "incidence, and counting checks are reimplemented in this script."
        ),
        "exhaustive_local_suite": exhaustive_local_suite(),
        "construction_suite": construction_suite(),
        "random_exact_suite": random_exact_suite(),
    }
    out = ROOT / "results" / "independent_proof_audit.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "exhaustive": result["exhaustive_local_suite"],
        "constructors_each": result["construction_suite"]["orders_checked_per_builder"],
        "random_exact_graphs": result["random_exact_suite"]["graphs"],
        "random_runtime_seconds": result["random_exact_suite"]["runtime_seconds"],
    }, indent=2))


if __name__ == "__main__":
    main()
