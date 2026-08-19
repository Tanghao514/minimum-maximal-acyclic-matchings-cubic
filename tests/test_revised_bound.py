from __future__ import annotations
from math import ceil
import networkx as nx
from src.acyclic_matching import is_maximal_acyclic_matching
from src.constructions import (
    bridgeless_n20_counterexample,
    n26_equality_example,
    one_fifth_extremal_family,
    p2_cycle_equality_family,
    path_cycle_family,
)
from src.exact_solver import minimum_maximal_acyclic_matching
from src.structure import analyze_maximal_acyclic_matching


def test_infinite_family_certificates_and_equality() -> None:
    for r in range(3):
        for q in range(5):
            item = one_fifth_extremal_family(r, leaf_excess=q)
            assert is_maximal_acyclic_matching(item.graph, item.matching)
            cert = analyze_maximal_acyclic_matching(item.graph, item.matching)
            assert len(item.matching) == ceil((len(item.graph) - 1) / 5)
            assert cert.n <= 5 * cert.k + (cert.k % 2)


def test_small_family_members_are_exact_by_solver() -> None:
    for q, expected in ((0, 3), (1, 4), (2, 5)):
        item = one_fifth_extremal_family(0, leaf_excess=q)
        assert minimum_maximal_acyclic_matching(item.graph).mu == expected


def test_bridgeless_does_not_restore_quarter_bound() -> None:
    item = bridgeless_n20_counterexample()
    assert not list(nx.bridges(item.graph))
    assert nx.edge_connectivity(item.graph) == 2
    assert is_maximal_acyclic_matching(item.graph, item.matching)
    assert minimum_maximal_acyclic_matching(item.graph).mu == 4
    assert 4 < len(item.graph) // 4


def test_n26_shows_minus_one_is_necessary() -> None:
    item = n26_equality_example()
    assert is_maximal_acyclic_matching(item.graph, item.matching)
    assert minimum_maximal_acyclic_matching(item.graph).mu == 5
    assert len(item.matching) == ceil((len(item.graph) - 1) / 5)
    assert len(item.matching) < ceil(len(item.graph) / 5)


def test_p2_cycle_equality_family() -> None:
    for q in range(5):
        item = p2_cycle_equality_family(q)
        assert is_maximal_acyclic_matching(item.graph, item.matching)
        assert len(item.matching) == ceil((len(item.graph) - 1) / 5)
        analyze_maximal_acyclic_matching(item.graph, item.matching)


def test_path_cycle_small_equality_examples() -> None:
    for k in range(1, 6):
        item = path_cycle_family(k)
        assert is_maximal_acyclic_matching(item.graph, item.matching)
        assert k == ceil((len(item.graph) - 1) / 5)
        analyze_maximal_acyclic_matching(item.graph, item.matching)


def test_direct_chain_family_and_all_orders() -> None:
    from src.constructions import chain_extremal_family, extremal_graph_for_order_direct

    for base_k in (3, 5, 7, 9):
        for q in range(5):
            item = chain_extremal_family(base_k, leaf_excess=q)
            assert is_maximal_acyclic_matching(item.graph, item.matching)
            assert len(item.matching) == ceil((len(item.graph) - 1) / 5)
            analyze_maximal_acyclic_matching(item.graph, item.matching)

    for n in range(4, 202, 2):
        item = extremal_graph_for_order_direct(n)
        assert len(item.graph) == n
        assert is_maximal_acyclic_matching(item.graph, item.matching)
        assert len(item.matching) == ceil((n - 1) / 5)
        analyze_maximal_acyclic_matching(item.graph, item.matching)
