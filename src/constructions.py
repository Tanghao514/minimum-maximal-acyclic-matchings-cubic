"""Constructions witnessing sharpness of the revised lower bound."""
from __future__ import annotations
from dataclasses import dataclass
import networkx as nx
Edge = tuple[int, int]

@dataclass(frozen=True)
class ConstructedMatching:
    graph: nx.Graph
    matching: tuple[Edge, ...]
    metadata: dict[str, int | str | bool]

def expand_vertex_to_triangle(G: nx.Graph, v: int) -> nx.Graph:
    H = nx.convert_node_labels_to_integers(G, ordering="sorted")
    nbrs = sorted(H.neighbors(v))
    if len(nbrs) != 3: raise ValueError("triangle expansion requires degree 3")
    H.remove_node(v)
    H = nx.convert_node_labels_to_integers(H, ordering="sorted")
    mapped = [x if x < v else x - 1 for x in nbrs]
    base = len(H); tri = [base, base+1, base+2]
    H.add_edges_from([(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])])
    H.add_edges_from(zip(mapped, tri, strict=True))
    return H

def _degree_1_or_4_tree(r: int) -> nx.Graph:
    if r < 0: raise ValueError("r must be nonnegative")
    T = nx.Graph()
    if r == 0:
        T.add_edge(0, 1); return T
    T.add_nodes_from(range(r))
    T.add_edges_from((i, i+1) for i in range(r-1))
    nxt = r
    for x in range(r):
        for _ in range(4-T.degree(x)):
            T.add_edge(x, nxt); nxt += 1
    assert nx.is_tree(T)
    assert sum(T.degree(x)==1 for x in T) == 2*r+2
    return T

class _Builder:
    def __init__(self):
        self.G=nx.Graph(); self.next_vertex=0; self.matching=[]
    def vertices(self,count):
        out=list(range(self.next_vertex,self.next_vertex+count)); self.next_vertex+=count
        self.G.add_nodes_from(out); return out
    def f_path(self, matching_edges: int):
        """Alternating P_{2s} in S, with 2s+2 residual cubic stubs."""
        s=matching_edges
        if s < 1: raise ValueError
        V=self.vertices(2*s)
        self.G.add_edges_from((V[i],V[i+1]) for i in range(2*s-1))
        self.matching.extend((V[2*i],V[2*i+1]) for i in range(s))
        stubs=[]
        for i,v in enumerate(V):
            stubs.extend([v]*(3-self.G.degree(v)))
        assert len(stubs)==2*s+2
        return V,stubs

def one_fifth_extremal_family(r: int, *, leaf_excess: int = 0) -> ConstructedMatching:
    r"""Family with k=6r+3+q and n=30r+16+4q, q=leaf_excess.

    For 0<=q<=4 the distinguished matching meets ceil((n-1)/5) exactly.
    The construction remains valid for all q>=0; one selected leaf's F=K2
    component and U=C3 are replaced by F=P_{2(q+1)} and U=C_{2q+3}.
    """
    if leaf_excess < 0: raise ValueError("leaf_excess must be nonnegative")
    q=leaf_excess; T=_degree_1_or_4_tree(r); leaves=sorted(x for x in T if T.degree(x)==1)
    special=leaves[0]
    B=_Builder(); stubs={}
    for x in sorted(T.nodes):
        s=q+1 if x==special else 1
        _,stubs[x]=B.f_path(s)
    for x,y in sorted((min(a,b),max(a,b)) for a,b in T.edges):
        xs=stubs[x].pop(); ys=stubs[y].pop()
        _,hub=B.f_path(1)
        p=B.vertices(4)
        B.G.add_edges_from((p[i],p[i+1]) for i in range(3))
        B.G.add_edges_from([(p[0],xs),(p[3],ys)])
        B.G.add_edges_from(zip(p,hub,strict=True))
    for x in sorted(T.nodes):
        if T.degree(x)==4:
            assert not stubs[x]; continue
        L=2*q+3 if x==special else 3
        assert len(stubs[x])==L
        C=B.vertices(L)
        B.G.add_edges_from((C[i],C[(i+1)%L]) for i in range(L))
        B.G.add_edges_from(zip(C,stubs[x],strict=True)); stubs[x].clear()
    G=nx.convert_node_labels_to_integers(B.G,ordering="sorted")
    M=tuple(B.matching); k=6*r+3+q; n=30*r+16+4*q
    assert len(M)==k and len(G)==n and nx.is_connected(G) and all(d==3 for _,d in G.degree)
    return ConstructedMatching(G,M,{"family":"one_fifth","r":r,"leaf_excess":q,"n":n,"k":k,"formula":"n=5k+1-q"})


def bridgeless_n20_counterexample() -> ConstructedMatching:
    """A bridge-free (but 2-edge-connected) n=20 graph with mu=4.

    Four K2 components form F=G[S].  Two P6 components form G[U].
    In each P6, both endpoints self-block against an endpoint F-component,
    while all four internal vertices attach to one central F-component.
    """
    G = nx.Graph()
    F: dict[int, tuple[int, int]] = {}
    matching: list[Edge] = []
    for lab in range(4):
        a, b = 2 * lab, 2 * lab + 1
        G.add_edge(a, b)
        F[lab] = (a, b)
        matching.append((a, b))

    # (path vertices, left endpoint label, central label, right endpoint label)
    specifications = [
        (list(range(8, 14)), 1, 0, 2),
        (list(range(14, 20)), 1, 3, 2),
    ]
    for path, left, central, right in specifications:
        G.add_edges_from((path[i], path[i + 1]) for i in range(5))
        G.add_edges_from((path[0], s) for s in F[left])
        G.add_edges_from((path[-1], s) for s in F[right])
        # Two internal vertices go to each endpoint of the central K2.
        G.add_edges_from((path[i], F[central][0]) for i in (1, 2))
        G.add_edges_from((path[i], F[central][1]) for i in (3, 4))

    assert len(G) == 20 and G.number_of_edges() == 30
    assert nx.is_connected(G) and all(d == 3 for _, d in G.degree)
    assert not list(nx.bridges(G))
    return ConstructedMatching(
        G,
        tuple(matching),
        {
            "family": "bridgeless_n20_counterexample",
            "n": 20,
            "k": 4,
            "edge_connectivity": nx.edge_connectivity(G),
        },
    )


def n26_equality_example() -> ConstructedMatching:
    """A 26-vertex equality graph with a size-5 maximal acyclic matching.

    F consists of five K2s.  G[U] consists of two P2 components sharing one
    F-component in the incidence graph and four C3 components.
    """
    G = nx.Graph()
    F: dict[int, tuple[int, int]] = {}
    matching: list[Edge] = []
    next_vertex = 0
    for lab in range(5):
        a, b = next_vertex, next_vertex + 1
        next_vertex += 2
        G.add_edge(a, b)
        F[lab] = (a, b)
        matching.append((a, b))

    requirements: list[tuple[int, int]] = []
    for left, right in ((1, 2), (3, 4)):
        u, v = next_vertex, next_vertex + 1
        next_vertex += 2
        G.add_edge(u, v)
        # The P2 edge is blocked because the endpoints share label 0.
        requirements.extend([(u, 0), (u, left), (v, 0), (v, right)])

    for lab in (1, 2, 3, 4):
        cycle = [next_vertex, next_vertex + 1, next_vertex + 2]
        next_vertex += 3
        G.add_edges_from(
            [(cycle[0], cycle[1]), (cycle[1], cycle[2]), (cycle[2], cycle[0])]
        )
        requirements.extend((u, lab) for u in cycle)

    for lab in range(5):
        users = [u for u, assigned in requirements if assigned == lab]
        assert len(users) == 4
        for u, s in zip(users, (F[lab][0], F[lab][0], F[lab][1], F[lab][1]), strict=True):
            G.add_edge(u, s)

    assert len(G) == 26 and G.number_of_edges() == 39
    assert nx.is_connected(G) and all(d == 3 for _, d in G.degree)
    return ConstructedMatching(
        G,
        tuple(matching),
        {"family": "n26_equality", "n": 26, "k": 5, "formula": "n=5k+1"},
    )


def p2_cycle_equality_family(leaf_excess: int = 0) -> ConstructedMatching:
    """Equality examples at n=26+4q, k=5+q for 0<=q<=4.

    The incidence core has five F-components and two P2 components.  Four
    leaf F-components carry cycles; one selected leaf is enlarged from K2/C3
    to an alternating P_{2(q+1)}/C_{2q+3} pair.
    """
    q = leaf_excess
    if q < 0:
        raise ValueError("leaf_excess must be nonnegative")
    B = _Builder()
    f_stubs: dict[int, list[int]] = {}
    for lab in range(5):
        size = q + 1 if lab == 1 else 1
        _, f_stubs[lab] = B.f_path(size)

    # Two P2s.  Their endpoints share F-component 0, so each P2 edge is blocked.
    for left, right in ((1, 2), (3, 4)):
        u, v = B.vertices(2)
        B.G.add_edge(u, v)
        B.G.add_edge(u, f_stubs[0].pop())
        B.G.add_edge(v, f_stubs[0].pop())
        B.G.add_edge(u, f_stubs[left].pop())
        B.G.add_edge(v, f_stubs[right].pop())

    assert not f_stubs[0]
    for lab in (1, 2, 3, 4):
        length = 2 * q + 3 if lab == 1 else 3
        assert len(f_stubs[lab]) == length
        cycle = B.vertices(length)
        B.G.add_edges_from(
            (cycle[i], cycle[(i + 1) % length]) for i in range(length)
        )
        B.G.add_edges_from(zip(cycle, f_stubs[lab], strict=True))
        f_stubs[lab].clear()

    G = nx.convert_node_labels_to_integers(B.G, ordering="sorted")
    matching = tuple(B.matching)
    n, k = 26 + 4 * q, 5 + q
    assert len(G) == n and len(matching) == k
    assert nx.is_connected(G) and all(d == 3 for _, d in G.degree)
    return ConstructedMatching(
        G,
        matching,
        {
            "family": "p2_cycle_equality",
            "leaf_excess": q,
            "n": n,
            "k": k,
            "formula": "n=5k+1-q",
        },
    )


def path_cycle_family(k: int) -> ConstructedMatching:
    """Cubic graph with F=P_{2k}, H=C_{2k+2}, and distinguished |M|=k.

    For 1<=k<=5 this attains ceil((n-1)/5), giving equality examples at
    n=6,10,14,18,22.  It remains a valid maximal-acyclic-matching
    construction for every k>=1.
    """
    if k < 1:
        raise ValueError("k must be positive")
    B = _Builder()
    _, stubs = B.f_path(k)
    cycle = B.vertices(2 * k + 2)
    B.G.add_edges_from(
        (cycle[i], cycle[(i + 1) % len(cycle)]) for i in range(len(cycle))
    )
    # Interleave duplicate endpoint stubs around the cycle when possible;
    # any bijection works for maximality because all S vertices lie in one
    # component of F.
    B.G.add_edges_from(zip(cycle, stubs, strict=True))
    G = nx.convert_node_labels_to_integers(B.G, ordering="sorted")
    matching = tuple(B.matching)
    assert len(G) == 4 * k + 2 and len(matching) == k
    assert nx.is_connected(G) and all(d == 3 for _, d in G.degree)
    return ConstructedMatching(
        G,
        matching,
        {"family": "path_cycle", "n": 4 * k + 2, "k": k, "formula": "n=4k+2"},
    )


def _find_marked_triangle_leaf(
    G: nx.Graph, matching: tuple[Edge, ...]
) -> tuple[frozenset[int], frozenset[int]]:
    """Find a K2 F-component carrying a U-triangle and one external edge."""
    S = {v for e in matching for v in e}
    F = G.subgraph(S)
    f_components = [frozenset(C) for C in nx.connected_components(F)]
    f_of = {v: C for C in f_components for v in C}
    H = G.subgraph(set(G) - S)
    for C in nx.connected_components(H):
        triangle = frozenset(C)
        J = H.subgraph(C)
        if len(C) != 3 or J.number_of_edges() != 3:
            continue
        adjacent_f = {f_of[s] for u in C for s in G.neighbors(u) if s in S}
        if len(adjacent_f) != 1:
            continue
        leaf = next(iter(adjacent_f))
        if len(leaf) != 2 or F.subgraph(leaf).number_of_edges() != 1:
            continue
        outside_edges = [
            (u, v)
            for u in leaf
            for v in G.neighbors(u)
            if v not in leaf and v not in triangle
        ]
        triangle_cross = sum(
            1 for u in leaf for v in G.neighbors(u) if v in triangle
        )
        if len(outside_edges) == 1 and triangle_cross == 3:
            return leaf, triangle
    raise ValueError("no marked K2-plus-triangle leaf gadget found")


def _branch_expand_marked_leaf(
    G: nx.Graph,
    matching: tuple[Edge, ...],
    mark: tuple[frozenset[int], frozenset[int]],
) -> tuple[nx.Graph, tuple[Edge, ...], tuple[frozenset[int], frozenset[int]]]:
    """Replace one marked triangle by a P3 and two new marked leaf gadgets.

    This adds 10 vertices and 2 matching edges, preserving n=5|M|+1.
    One of the two new leaves is returned as the next mark.
    """
    H = G.copy()
    M = list(matching)
    old_f, old_triangle = mark
    H.remove_nodes_from(old_triangle)

    free_old = [v for v in sorted(old_f) for _ in range(3 - H.degree(v))]
    if len(free_old) != 3:
        raise AssertionError("expanded leaf should expose exactly three old-F stubs")

    nxt = max(H.nodes, default=-1) + 1
    p0, p1, p2 = nxt, nxt + 1, nxt + 2
    H.add_edges_from([(p0, p1), (p1, p2)])
    for p, s in zip((p0, p1, p2), free_old, strict=True):
        H.add_edge(p, s)
    nxt += 3

    new_marks: list[tuple[frozenset[int], frozenset[int]]] = []
    for connector in (p0, p2):
        a, b = nxt, nxt + 1
        nxt += 2
        H.add_edge(a, b)
        M.append((a, b))
        stubs = [a, a, b, b]
        H.add_edge(connector, stubs.pop())
        tri = [nxt, nxt + 1, nxt + 2]
        nxt += 3
        H.add_edges_from([(tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])])
        for u, s in zip(tri, stubs, strict=True):
            H.add_edge(u, s)
        new_marks.append((frozenset((a, b)), frozenset(tri)))

    if not nx.is_connected(H) or any(d != 3 for _, d in H.degree):
        raise AssertionError("branch expansion failed to preserve connected cubic structure")
    return H, tuple(M), new_marks[0]


def _odd_max_base_marked(
    k: int,
) -> tuple[ConstructedMatching, tuple[frozenset[int], frozenset[int]]]:
    """Return a marked equality graph with odd k>=3 and n=5k+1."""
    if k < 3 or k % 2 == 0:
        raise ValueError("k must be odd and at least 3")
    item = one_fifth_extremal_family(0, leaf_excess=0)
    G, M = item.graph.copy(), item.matching
    mark = _find_marked_triangle_leaf(G, M)
    for _ in range((k - 3) // 2):
        G, M, mark = _branch_expand_marked_leaf(G, M, mark)
    if len(M) != k or len(G) != 5 * k + 1:
        raise AssertionError("odd maximum-order construction count mismatch")
    return (
        ConstructedMatching(
            G,
            M,
            {"family": "odd_max_base", "n": len(G), "k": k, "formula": "n=5k+1"},
        ),
        mark,
    )


def _enlarge_marked_leaf(
    item: ConstructedMatching,
    mark: tuple[frozenset[int], frozenset[int]],
    q: int,
) -> ConstructedMatching:
    """Safe implementation of marked-leaf enlargement with explicit relabelling."""
    if q < 0:
        raise ValueError("q must be nonnegative")
    if q == 0:
        return item
    G = item.graph.copy()
    M = list(item.matching)
    old_f, old_triangle = mark
    external = [(u, v) for u in old_f for v in G.neighbors(u) if v not in old_f and v not in old_triangle]
    if len(external) != 1:
        raise AssertionError("marked leaf should have exactly one external edge")
    external_neighbor = external[0][1]
    old_match = next((e for e in M if set(e) == set(old_f)), None)
    if old_match is None:
        raise AssertionError("marked matching edge not found")
    M.remove(old_match)
    G.remove_nodes_from(set(old_f) | set(old_triangle))

    nxt = max(G.nodes, default=-1) + 1
    f_path = list(range(nxt, nxt + 2 * (q + 1)))
    nxt += len(f_path)
    G.add_edges_from((f_path[i], f_path[i + 1]) for i in range(len(f_path) - 1))
    M.extend((f_path[2 * i], f_path[2 * i + 1]) for i in range(q + 1))
    stubs = [v for v in f_path for _ in range(3 - G.degree(v))]
    G.add_edge(external_neighbor, stubs.pop())
    cycle = list(range(nxt, nxt + 2 * q + 3))
    G.add_edges_from((cycle[i], cycle[(i + 1) % len(cycle)]) for i in range(len(cycle)))
    G.add_edges_from(zip(cycle, stubs, strict=True))

    old_nodes = sorted(G.nodes)
    relabel = {v: i for i, v in enumerate(old_nodes)}
    H = nx.relabel_nodes(G, relabel, copy=True)
    new_M = tuple((relabel[u], relabel[v]) for u, v in M)
    if not nx.is_connected(H) or any(d != 3 for _, d in H.degree):
        raise AssertionError("leaf enlargement failed to preserve connected cubic structure")
    return ConstructedMatching(
        H,
        new_M,
        {
            "family": "all_orders_extremal",
            "n": len(H),
            "k": len(new_M),
            "leaf_excess": q,
            "formula": "n=5k+1-q",
        },
    )


def extremal_graph_for_order(n: int) -> ConstructedMatching:
    r"""Construct a connected simple cubic graph attaining ceil((n-1)/5).

    This works for every even n>=4, hence—combined with the structural lower
    bound—determines the exact extremal function f_3(n) for every admissible n.
    """
    from math import ceil

    if n < 4 or n % 2:
        raise ValueError("a connected cubic graph has even order n>=4")
    k = ceil((n - 1) / 5)

    if n == 4:
        G = nx.complete_graph(4)
        return ConstructedMatching(G, ((0, 1),), {"family": "K4", "n": 4, "k": 1})
    if n == 8:
        G = nx.convert_node_labels_to_integers(nx.cubical_graph())
        return ConstructedMatching(G, ((0, 1), (2, 6)), {"family": "cube", "n": 8, "k": 2})
    if n == 12:
        G = nx.convert_node_labels_to_integers(nx.circular_ladder_graph(6))
        return ConstructedMatching(
            G,
            ((0, 1), (2, 3), (4, 10)),
            {"family": "hexagonal_prism", "n": 12, "k": 3},
        )

    q = 5 * k + 1 - n
    k0 = k - q
    if not (0 <= q <= 4) or k0 % 2 != 1:
        raise AssertionError("arithmetic decomposition failed")
    if k0 == 1:
        item = path_cycle_family(k)
        if len(item.graph) != n:
            raise AssertionError("small path-cycle order mismatch")
        return item
    if k0 < 3:
        raise AssertionError("unexpected small base")

    base, mark = _odd_max_base_marked(k0)
    result = _enlarge_marked_leaf(base, mark, q)
    if len(result.graph) != n or len(result.matching) != k:
        raise AssertionError("all-orders construction count mismatch")
    return result


def chain_extremal_family(base_k: int, *, leaf_excess: int = 0) -> ConstructedMatching:
    r"""Direct sharpness construction with no graph-replacement operations.

    Parameters
    ----------
    base_k:
        An odd integer at least 3.  Writing ``base_k = 2t+1``, the base
        construction has ``t`` tree components in ``G[U]``: one ``P4`` root
        and ``t-1`` ``P3`` branch components.  Its ``base_k`` components in
        ``G[S]`` are paths, initially all copies of ``K2``.
    leaf_excess:
        An integer ``q>=0``.  One terminal ``K2``/``C3`` pair is replaced at
        construction time by an alternating ``P_{2(q+1)}``/``C_{2q+3}``
        pair.  Thus ``k=base_k+q`` and ``n=5k+1-q``.

    For ``0<=q<=4``, the distinguished maximal acyclic matching attains
    ``ceil((n-1)/5)``.  The implementation is intentionally direct so that it
    serves as an independent check of the earlier replacement-based builder.
    """
    if base_k < 3 or base_k % 2 == 0:
        raise ValueError("base_k must be odd and at least 3")
    if leaf_excess < 0:
        raise ValueError("leaf_excess must be nonnegative")

    q = leaf_excess
    t = (base_k - 1) // 2
    B = _Builder()

    # Every entry stores the unused cubic stubs of one F-component.  Component
    # L0 is the terminal component enlarged by q; all others are K2s.
    _, root_central = B.f_path(1)
    _, terminal_0 = B.f_path(q + 1)
    _, active = B.f_path(1)

    terminal_stubs: list[list[int]] = [terminal_0]

    # Root H-component: P4.  All four path vertices see the central
    # F-component; its two endpoints additionally see the two leaf
    # F-components.  Hence each of its three edges is blocked through the
    # central F-component.
    root_path = B.vertices(4)
    B.G.add_edges_from((root_path[i], root_path[i + 1]) for i in range(3))
    for p in root_path:
        B.G.add_edge(p, root_central.pop())
    B.G.add_edge(root_path[0], terminal_0.pop())
    B.G.add_edge(root_path[3], active.pop())
    if root_central:
        raise AssertionError("root central F-component should have no free stubs")

    # Each branch H-component is a P3.  Its three vertices use the three
    # remaining stubs of the current active F-component, while its endpoints
    # each start one new leaf F-component.  The second new leaf remains active
    # for the next branch, giving a simple chain of branch gadgets.
    for _ in range(t - 1):
        _, new_terminal = B.f_path(1)
        _, new_active = B.f_path(1)
        branch = B.vertices(3)
        B.G.add_edges_from([(branch[0], branch[1]), (branch[1], branch[2])])
        for p in branch:
            B.G.add_edge(p, active.pop())
        B.G.add_edge(branch[0], new_terminal.pop())
        B.G.add_edge(branch[2], new_active.pop())
        if active:
            raise AssertionError("expanded active F-component has unused stubs")
        terminal_stubs.append(new_terminal)
        active = new_active

    terminal_stubs.append(active)

    # Close every terminal F-component with one U-cycle.  A K2 leaf has three
    # free stubs and therefore receives C3.  The enlarged terminal has
    # 2q+3 free stubs and receives C_{2q+3}.
    for stubs in terminal_stubs:
        length = len(stubs)
        if length < 3:
            raise AssertionError("a terminal cycle must have length at least 3")
        cycle = B.vertices(length)
        B.G.add_edges_from(
            (cycle[i], cycle[(i + 1) % length]) for i in range(length)
        )
        B.G.add_edges_from(zip(cycle, stubs, strict=True))
        stubs.clear()

    G = nx.convert_node_labels_to_integers(B.G, ordering="sorted")
    M = tuple(B.matching)
    k = base_k + q
    n = 5 * k + 1 - q
    if len(M) != k or len(G) != n:
        raise AssertionError("chain construction count mismatch")
    if not nx.is_connected(G) or any(d != 3 for _, d in G.degree):
        raise AssertionError("chain construction is not connected cubic")
    return ConstructedMatching(
        G,
        M,
        {
            "family": "chain_extremal",
            "base_k": base_k,
            "leaf_excess": q,
            "n": n,
            "k": k,
            "formula": "n=5k+1-q",
        },
    )


def extremal_graph_for_order_direct(n: int) -> ConstructedMatching:
    r"""A second, direct construction attaining ``ceil((n-1)/5)``.

    This is independent of ``extremal_graph_for_order`` for every order
    ``n>=16``.  The exceptional small orders use standard cubic graphs, and
    orders 6,10,14,18,22 use the path--cycle family.
    """
    from math import ceil

    if n < 4 or n % 2:
        raise ValueError("a connected cubic graph has even order n>=4")
    k = ceil((n - 1) / 5)
    if n == 4:
        G = nx.complete_graph(4)
        return ConstructedMatching(G, ((0, 1),), {"family": "K4", "n": 4, "k": 1})
    if n == 8:
        G = nx.convert_node_labels_to_integers(nx.cubical_graph())
        return ConstructedMatching(G, ((0, 1), (2, 6)), {"family": "cube", "n": 8, "k": 2})
    if n == 12:
        G = nx.convert_node_labels_to_integers(nx.circular_ladder_graph(6))
        return ConstructedMatching(
            G,
            ((0, 1), (2, 3), (4, 10)),
            {"family": "hexagonal_prism", "n": 12, "k": 3},
        )

    q = 5 * k + 1 - n
    base_k = k - q
    if not (0 <= q <= 4) or base_k % 2 != 1:
        raise AssertionError("arithmetic decomposition failed")
    if base_k == 1:
        item = path_cycle_family(k)
        if len(item.graph) != n:
            raise AssertionError("path-cycle order mismatch")
        return item
    return chain_extremal_family(base_k, leaf_excess=q)
