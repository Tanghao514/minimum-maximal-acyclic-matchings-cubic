from __future__ import annotations

import random

import networkx as nx
import pytest

from src.acyclic_matching import is_maximal_acyclic_matching
from src.constructions import extremal_graph_for_order_direct
from src.exact_solver import minimum_maximal_acyclic_matching
from src.solver_c import minimum_maximal_acyclic_matching_cubic


def _shuffle_insertion_order(G: nx.Graph, seed: int) -> nx.Graph:
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


def test_solver_c_matches_solver_b_on_standard_cubic_graphs() -> None:
    graphs = [
        nx.complete_graph(4),
        nx.complete_bipartite_graph(3, 3),
        nx.cubical_graph(),
        nx.petersen_graph(),
        nx.circular_ladder_graph(5),
        nx.circular_ladder_graph(6),
    ]
    for G in graphs:
        b = minimum_maximal_acyclic_matching(G)
        c = minimum_maximal_acyclic_matching_cubic(G)
        assert c.mu == b.mu
        assert is_maximal_acyclic_matching(G, c.matching)


def test_solver_c_on_equality_family_with_random_orders() -> None:
    for n in range(4, 27, 2):
        G = _shuffle_insertion_order(extremal_graph_for_order_direct(n).graph, 1000 + n)
        b = minimum_maximal_acyclic_matching(G)
        c = minimum_maximal_acyclic_matching_cubic(G)
        assert c.mu == b.mu
        assert is_maximal_acyclic_matching(G, c.matching)


def test_solver_c_on_fixed_random_cubic_graphs() -> None:
    for n in (10, 12, 14, 16, 18):
        for seed in range(3):
            G = nx.random_regular_graph(3, n, seed=100 * n + seed)
            if not nx.is_connected(G):
                continue
            b = minimum_maximal_acyclic_matching(G)
            c = minimum_maximal_acyclic_matching_cubic(G)
            assert c.mu == b.mu
            assert is_maximal_acyclic_matching(G, c.matching)


def test_solver_c_rejects_wrong_scope() -> None:
    with pytest.raises(ValueError):
        minimum_maximal_acyclic_matching_cubic(nx.path_graph(6))
    G = nx.disjoint_union(nx.complete_graph(4), nx.complete_graph(4))
    with pytest.raises(ValueError):
        minimum_maximal_acyclic_matching_cubic(G)


def test_solver_c_parameter_kernel_decision() -> None:
    from src.solver_c import find_maximal_acyclic_matching_at_most_k_cubic

    G = extremal_graph_for_order_direct(16).graph
    assert find_maximal_acyclic_matching_at_most_k_cubic(G, 2) is None
    witness = find_maximal_acyclic_matching_at_most_k_cubic(G, 3)
    assert witness is not None
    assert len(witness) == 3
    assert is_maximal_acyclic_matching(G, witness)
