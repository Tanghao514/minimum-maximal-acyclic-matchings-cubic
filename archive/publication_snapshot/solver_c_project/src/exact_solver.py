"""Two independent exact solvers for minimum maximal acyclic matching.

Solver A (``minimum_maximal_acyclic_matching_bruteforce``) is deliberately
naive: it enumerates edge subsets with ``itertools.combinations`` and invokes
the reference definition functions.

Solver B (``minimum_maximal_acyclic_matching``) relabels vertices to bit
positions, enumerates matchings by increasing cardinality, and caches exact
induced-forest and maximality tests.  It never replaces G[S] by a graph that
contains only the matching edges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from time import perf_counter
from typing import Any, Hashable, TypeAlias

import networkx as nx

from .acyclic_matching import is_matching, is_maximal_acyclic_matching

Node: TypeAlias = Hashable
Edge: TypeAlias = tuple[Node, Node]


@dataclass(frozen=True)
class SolverResult:
    """Exact optimum and one certificate, with reproducibility diagnostics."""

    mu: int
    matching: tuple[Edge, ...]
    solver: str
    runtime_seconds: float
    states_examined: int = 0
    forest_tests: int = 0
    forest_cache_hits: int = 0
    maximality_tests: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


def _require_finite_simple_undirected_graph(G: nx.Graph) -> None:
    if G.is_directed():
        raise TypeError("The parameter is defined here for undirected graphs.")
    if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
        raise TypeError("The parameter is defined here for simple graphs.")
    if any(u == v for u, v in G.edges):
        raise ValueError("The parameter is defined here for loopless graphs.")


def minimum_maximal_acyclic_matching_bruteforce(G: nx.Graph) -> SolverResult:
    """Solver A: enumerate every edge subset, filter, and minimize cardinality.

    This is intentionally simple and intended only for small cross-validation
    instances.  Enumerating by cardinality lets it return once the first
    maximal acyclic matching size is found, while still considering every
    candidate subset of all smaller sizes.
    """
    _require_finite_simple_undirected_graph(G)
    start = perf_counter()
    edges: tuple[Edge, ...] = tuple(G.edges)
    states = 0

    for k in range(len(edges) + 1):
        for candidate in combinations(edges, k):
            states += 1
            if not is_matching(G, candidate):
                continue
            if is_maximal_acyclic_matching(G, candidate):
                return SolverResult(
                    mu=k,
                    matching=tuple(candidate),
                    solver="A-bruteforce",
                    runtime_seconds=perf_counter() - start,
                    states_examined=states,
                )

    # The empty graph has the empty matching as a maximal acyclic matching, so
    # this line is unreachable for every finite simple graph.
    raise RuntimeError("No maximal acyclic matching found; definition bug suspected.")


class _BitsetExactSolver:
    """Solver B implementation for one graph."""

    def __init__(self, G: nx.Graph) -> None:
        _require_finite_simple_undirected_graph(G)
        self.original_graph = G
        self.nodes: tuple[Node, ...] = tuple(G.nodes)
        self.node_to_index = {v: i for i, v in enumerate(self.nodes)}
        self.n = len(self.nodes)

        indexed_edges = [
            (self.node_to_index[u], self.node_to_index[v]) for u, v in G.edges
        ]
        # A deterministic order improves reproducibility.  Put edges whose
        # endpoints have many common/nearby neighbours first, because they are
        # more likely to expose an induced cycle early.
        adjacency_sets = [set() for _ in range(self.n)]
        for u, v in indexed_edges:
            adjacency_sets[u].add(v)
            adjacency_sets[v].add(u)

        def edge_score(edge: tuple[int, int]) -> tuple[int, int, int]:
            u, v = edge
            two_hop_overlap = len(
                (set().union(*(adjacency_sets[x] for x in adjacency_sets[u])) if adjacency_sets[u] else set())
                & (set().union(*(adjacency_sets[x] for x in adjacency_sets[v])) if adjacency_sets[v] else set())
            )
            return (-two_hop_overlap, min(u, v), max(u, v))

        indexed_edges.sort(key=edge_score)
        self.edges: tuple[tuple[int, int], ...] = tuple(indexed_edges)
        self.edge_masks: tuple[int, ...] = tuple(
            (1 << u) | (1 << v) for u, v in self.edges
        )

        adjacency_masks = [0] * self.n
        for u, v in self.edges:
            adjacency_masks[u] |= 1 << v
            adjacency_masks[v] |= 1 << u
        self.adjacency_masks: tuple[int, ...] = tuple(adjacency_masks)

        self.forest_cache: dict[int, bool] = {0: True}
        self.maximal_cache: dict[int, bool] = {}
        self.states_examined = 0
        self.forest_tests = 0
        self.forest_cache_hits = 0
        self.maximality_tests = 0

    def is_induced_forest(self, vertex_mask: int) -> bool:
        """Test exactly whether G[vertex_mask] is a forest."""
        cached = self.forest_cache.get(vertex_mask)
        if cached is not None:
            self.forest_cache_hits += 1
            return cached

        self.forest_tests += 1
        vertices = vertex_mask.bit_count()
        if vertices <= 1:
            self.forest_cache[vertex_mask] = True
            return True

        # Count all induced edges.  Each is seen twice in adjacency sums.
        twice_edges = 0
        remaining = vertex_mask
        while remaining:
            bit = remaining & -remaining
            v = bit.bit_length() - 1
            twice_edges += (self.adjacency_masks[v] & vertex_mask).bit_count()
            remaining ^= bit
        induced_edges = twice_edges // 2

        # Count connected components by bit-parallel DFS.  A finite undirected
        # graph is a forest exactly when |E| = |V| - number_of_components.
        components = 0
        unseen = vertex_mask
        while unseen:
            components += 1
            frontier = unseen & -unseen
            unseen ^= frontier
            while frontier:
                reached = 0
                layer = frontier
                while layer:
                    bit = layer & -layer
                    v = bit.bit_length() - 1
                    reached |= self.adjacency_masks[v]
                    layer ^= bit
                reached &= unseen
                unseen ^= reached
                frontier = reached

        result = induced_edges == vertices - components
        self.forest_cache[vertex_mask] = result
        return result

    def is_maximal_endpoint_set(self, matched_vertices: int) -> bool:
        cached = self.maximal_cache.get(matched_vertices)
        if cached is not None:
            return cached

        self.maximality_tests += 1
        # Every edge disjoint from S is an edge of G[U].  Adding it produces
        # endpoint set S union {u,v}; test the complete induced graph there.
        for edge_mask in self.edge_masks:
            if edge_mask & matched_vertices == 0:
                if self.is_induced_forest(matched_vertices | edge_mask):
                    self.maximal_cache[matched_vertices] = False
                    return False
        self.maximal_cache[matched_vertices] = True
        return True

    def _find_size_k(self, k: int) -> tuple[int, ...] | None:
        """Return edge indices of a size-k certificate, or None."""
        chosen: list[int] = []
        m = len(self.edges)

        def dfs(start_index: int, used_vertices: int) -> tuple[int, ...] | None:
            need = k - len(chosen)
            if need == 0:
                self.states_examined += 1
                if self.is_maximal_endpoint_set(used_vertices):
                    return tuple(chosen)
                return None

            # There are too few edge positions left even before disjointness.
            if m - start_index < need:
                return None
            # Matching cardinality cannot exceed half the number of unused
            # vertices.  This is an exact, definition-independent bound.
            if (self.n - used_vertices.bit_count()) // 2 < need:
                return None

            last_start = m - need
            for i in range(start_index, last_start + 1):
                edge_mask = self.edge_masks[i]
                if edge_mask & used_vertices:
                    continue
                new_vertices = used_vertices | edge_mask
                # Cycles in an induced subgraph persist after adding vertices,
                # so this is a safe monotone pruning rule.
                if not self.is_induced_forest(new_vertices):
                    continue
                chosen.append(i)
                result = dfs(i + 1, new_vertices)
                if result is not None:
                    return result
                chosen.pop()
            return None

        return dfs(0, 0)

    def solve(self) -> SolverResult:
        start = perf_counter()
        for k in range(self.n // 2 + 1):
            witness_indices = self._find_size_k(k)
            if witness_indices is not None:
                matching: tuple[Edge, ...] = tuple(
                    (self.nodes[self.edges[i][0]], self.nodes[self.edges[i][1]])
                    for i in witness_indices
                )
                # Final certificate check uses the independent reference code.
                if not is_maximal_acyclic_matching(self.original_graph, matching):
                    raise AssertionError(
                        "Bitset solver produced an invalid certificate; aborting."
                    )
                return SolverResult(
                    mu=k,
                    matching=matching,
                    solver="B-bitset-size-search",
                    runtime_seconds=perf_counter() - start,
                    states_examined=self.states_examined,
                    forest_tests=self.forest_tests,
                    forest_cache_hits=self.forest_cache_hits,
                    maximality_tests=self.maximality_tests,
                    metadata={
                        "forest_cache_size": len(self.forest_cache),
                        "maximal_cache_size": len(self.maximal_cache),
                    },
                )
        raise RuntimeError("No maximal acyclic matching found.")


def minimum_maximal_acyclic_matching(G: nx.Graph) -> SolverResult:
    """Solver B: exact bitset branch-and-bound / cardinality search."""
    return _BitsetExactSolver(G).solve()
