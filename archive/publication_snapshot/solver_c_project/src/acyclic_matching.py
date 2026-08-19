"""Reference definitions for induced acyclic matchings."""
from __future__ import annotations
from collections.abc import Iterable
from typing import Hashable, TypeAlias
import networkx as nx
Node: TypeAlias = Hashable
Edge: TypeAlias = tuple[Node, Node]

def _canonical_edge(u: Node, v: Node) -> frozenset[Node]:
    return frozenset((u, v))

def is_matching(G: nx.Graph, M: Iterable[Edge]) -> bool:
    graph_edges = {_canonical_edge(u, v) for u, v in G.edges}
    used: set[Node] = set()
    for item in M:
        try: u, v = item
        except Exception: return False
        if u == v or _canonical_edge(u, v) not in graph_edges or u in used or v in used:
            return False
        used.update((u, v))
    return True

def matching_vertices(M: Iterable[Edge]) -> set[Node]:
    return {x for e in M for x in e}

def induced_endpoint_graph(G: nx.Graph, M: Iterable[Edge]) -> nx.Graph:
    return G.subgraph(matching_vertices(M)).copy()

def is_acyclic_matching(G: nx.Graph, M: Iterable[Edge]) -> bool:
    edges = tuple(M)
    if not is_matching(G, edges): return False
    H = induced_endpoint_graph(G, edges)
    return H.number_of_nodes() == 0 or nx.is_forest(H)

def is_maximal_acyclic_matching(G: nx.Graph, M: Iterable[Edge]) -> bool:
    edges = tuple(M)
    if not is_acyclic_matching(G, edges): return False
    S = matching_vertices(edges)
    return not any(
        is_acyclic_matching(G, (*edges, (u, v)))
        for u, v in G.edges if u not in S and v not in S
    )
