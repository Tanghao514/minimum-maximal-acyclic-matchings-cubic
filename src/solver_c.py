"""Structure-aware exact solver for connected cubic graphs.

Solver C contracts every selected matching edge to one auxiliary vertex.  For
candidate graph edges e and f:

* they are a hard conflict if they share an endpoint, or if at least two graph
  edges run between their endpoint pairs;
* they are linked if they are disjoint and exactly one graph edge runs between
  their endpoint pairs.

For any matching M, G[V(M)] is a forest exactly when no selected pair is a
hard conflict and the linked graph induced by M is a forest.  A rollback DSU
therefore maintains acyclicity on selected *edges* without repeatedly rebuilding
an induced vertex subgraph.

If k=|M| and delta is the number of links in this contracted forest, then
c(G[V(M)])=k-delta.  The cubic structural theorem implies

    delta <= 5k + 1 - n.

At k=ceil((n-1)/5), the budget is at most four.  This gives a strong, proved
branch-and-bound rule at the first possible objective value.

The solver intentionally uses the proved cubic theorem.  It is an exact
post-theorem algorithm, not an independent verifier of that theorem.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from time import perf_counter
from typing import Hashable, TypeAlias

import networkx as nx

from .acyclic_matching import is_maximal_acyclic_matching
from .exact_solver import SolverResult, _require_finite_simple_undirected_graph

Node: TypeAlias = Hashable
Edge: TypeAlias = tuple[Node, Node]


class _RollbackDSU:
    """Rollback union-find without path compression."""

    __slots__ = ("parent", "size", "active", "components", "history")

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n
        self.active = [False] * n
        self.components = 0
        self.history: list[tuple[str, int, int, int]] = []

    def snapshot(self) -> int:
        return len(self.history)

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def activate(self, x: int) -> None:
        if self.active[x]:
            raise AssertionError("DSU vertex activated twice")
        self.history.append(("a", x, 0, 0))
        self.active[x] = True
        self.parent[x] = x
        self.size[x] = 1
        self.components += 1

    def union(self, a: int, b: int) -> bool:
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.history.append(("u", rb, ra, self.size[ra]))
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.components -= 1
        return True

    def rollback(self, snapshot: int) -> None:
        while len(self.history) > snapshot:
            kind, x, y, old_size = self.history.pop()
            if kind == "u":
                rb, ra = x, y
                self.parent[rb] = rb
                self.size[ra] = old_size
                self.components += 1
            else:
                self.active[x] = False
                self.parent[x] = x
                self.size[x] = 1
                self.components -= 1


@dataclass(frozen=True)
class _CandidateInfo:
    index: int
    defect_increment: int


class _CubicInteractionSolver:
    """Exact branch-and-bound solver specialized to connected cubic graphs."""

    def __init__(self, G: nx.Graph) -> None:
        _require_finite_simple_undirected_graph(G)
        if len(G) == 0 or not nx.is_connected(G):
            raise ValueError("Solver C requires a nonempty connected graph.")
        if any(deg != 3 for _, deg in G.degree):
            raise ValueError("Solver C is specialized to cubic graphs.")

        self.original_graph = G
        self.nodes: tuple[Node, ...] = tuple(G.nodes)
        self.node_to_index = {v: i for i, v in enumerate(self.nodes)}
        self.n = len(self.nodes)

        adjacency_masks = [0] * self.n
        raw_edges: list[tuple[int, int]] = []
        for a, b in G.edges:
            u = self.node_to_index[a]
            v = self.node_to_index[b]
            if u > v:
                u, v = v, u
            raw_edges.append((u, v))
            adjacency_masks[u] |= 1 << v
            adjacency_masks[v] |= 1 << u
        self.adjacency_masks: tuple[int, ...] = tuple(adjacency_masks)

        # Compute a deterministic high-interaction edge order.  Edges that
        # invalidate or link many other candidates tend to produce a small
        # maximal solution early and improve fail-first behavior.
        endpoint0, cycle0, link0 = self._build_pair_relations(tuple(raw_edges))
        ranking = []
        for i, (u, v) in enumerate(raw_edges):
            hard_degree = (endpoint0[i] | cycle0[i]).bit_count()
            link_degree = link0[i].bit_count()
            ranking.append((-(2 * hard_degree + link_degree), u, v, i))
        permutation = [row[3] for row in sorted(ranking)]

        self.edges: tuple[tuple[int, int], ...] = tuple(raw_edges[i] for i in permutation)
        self.m = len(self.edges)
        self.edge_endpoint_masks: tuple[int, ...] = tuple(
            (1 << u) | (1 << v) for u, v in self.edges
        )
        (
            self.endpoint_conflict_masks,
            self.cycle_conflict_masks,
            self.link_masks,
        ) = self._build_pair_relations(self.edges)
        self.hard_conflict_masks: tuple[int, ...] = tuple(
            self.endpoint_conflict_masks[i] | self.cycle_conflict_masks[i]
            for i in range(self.m)
        )
        # In a zero-defect solution no pair of selected matching edges may be
        # linked.  Hence pairwise incompatibility is hard-conflict OR link,
        # while maximality domination is supplied only by hard conflicts (or
        # by selecting the edge itself).
        self.zero_defect_conflict_masks: tuple[int, ...] = tuple(
            self.hard_conflict_masks[i] | self.link_masks[i]
            for i in range(self.m)
        )
        self.hard_domination_masks: tuple[int, ...] = tuple(
            self.hard_conflict_masks[i] | (1 << i)
            for i in range(self.m)
        )

        suffix = [0] * (self.m + 1)
        for i in range(self.m - 1, -1, -1):
            suffix[i] = suffix[i + 1] | (1 << i)
        self.suffix_masks: tuple[int, ...] = tuple(suffix)
        self.all_edges_mask = (1 << self.m) - 1

        self.dsu = _RollbackDSU(self.m)
        self.recursion_nodes = 0
        self.complete_candidates = 0
        self.maximality_tests = 0
        self.prune_cycle = 0
        self.prune_defect = 0
        self.prune_capacity = 0
        self.prune_defect_lb = 0
        self.prune_profile = 0
        self.prune_rigid_maximality = 0
        self.zero_defect_nodes = 0
        self.zero_defect_failed_cache_hits = 0
        self.zero_defect_failed_states = 0
        self.target_attempts: list[dict[str, int | float | bool | str]] = []

    def _build_pair_relations(
        self, edges: tuple[tuple[int, int], ...]
    ) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
        m = len(edges)
        endpoint = [0] * m
        cycle = [0] * m
        link = [0] * m
        endpoint_masks = [(1 << u) | (1 << v) for u, v in edges]

        for i in range(m):
            u, v = edges[i]
            for j in range(i + 1, m):
                bit_i = 1 << i
                bit_j = 1 << j
                if endpoint_masks[i] & endpoint_masks[j]:
                    endpoint[i] |= bit_j
                    endpoint[j] |= bit_i
                    continue

                pair_j = endpoint_masks[j]
                cross_edges = (
                    (self.adjacency_masks[u] & pair_j).bit_count()
                    + (self.adjacency_masks[v] & pair_j).bit_count()
                )
                if cross_edges >= 2:
                    cycle[i] |= bit_j
                    cycle[j] |= bit_i
                elif cross_edges == 1:
                    link[i] |= bit_j
                    link[j] |= bit_i

        return tuple(endpoint), tuple(cycle), tuple(link)

    def _neighbors_in_distinct_components(self, neighbors: int) -> bool:
        roots: set[int] = set()
        while neighbors:
            bit = neighbors & -neighbors
            j = bit.bit_length() - 1
            root = self.dsu.find(j)
            if root in roots:
                return False
            roots.add(root)
            neighbors ^= bit
        return True

    def _try_add(self, i: int, selected_mask: int) -> tuple[int, int] | None:
        link_neighbors = self.link_masks[i] & selected_mask
        if not self._neighbors_in_distinct_components(link_neighbors):
            return None

        snapshot = self.dsu.snapshot()
        self.dsu.activate(i)
        remaining = link_neighbors
        while remaining:
            bit = remaining & -remaining
            j = bit.bit_length() - 1
            if not self.dsu.union(i, j):
                self.dsu.rollback(snapshot)
                return None
            remaining ^= bit
        return snapshot, link_neighbors.bit_count()

    def _is_maximal(self, selected_mask: int) -> bool:
        """Test exact maximality in the contracted interaction forest."""
        self.maximality_tests += 1
        unselected = self.all_edges_mask & ~selected_mask
        while unselected:
            bit = unselected & -unselected
            i = bit.bit_length() - 1

            if self.endpoint_conflict_masks[i] & selected_mask:
                unselected ^= bit
                continue
            if self.cycle_conflict_masks[i] & selected_mask:
                unselected ^= bit
                continue

            link_neighbors = self.link_masks[i] & selected_mask
            if self._neighbors_in_distinct_components(link_neighbors):
                # Adding i joins distinct components through a new auxiliary
                # vertex, so the endpoint-induced graph remains a forest.
                return False
            unselected ^= bit
        return True

    def _count_tree_components_of_unmatched(self, selected_mask: int) -> int:
        matched_vertices = 0
        remaining = selected_mask
        while remaining:
            bit = remaining & -remaining
            i = bit.bit_length() - 1
            matched_vertices |= self.edge_endpoint_masks[i]
            remaining ^= bit

        unmatched = ((1 << self.n) - 1) & ~matched_vertices
        unseen = unmatched
        tree_components = 0
        while unseen:
            seed = unseen & -unseen
            frontier = seed
            unseen ^= seed
            component = 0
            while frontier:
                component |= frontier
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

            twice_edges = 0
            layer = component
            while layer:
                bit = layer & -layer
                v = bit.bit_length() - 1
                twice_edges += (self.adjacency_masks[v] & component).bit_count()
                layer ^= bit
            vertices = component.bit_count()
            edges = twice_edges // 2
            if edges == vertices - 1:
                tree_components += 1
            elif edges != vertices:
                return -1
        return tree_components

    def _candidate_infos(
        self,
        start: int,
        selected_mask: int,
        forbidden_mask: int,
        defect: int,
        defect_budget: int,
    ) -> tuple[list[_CandidateInfo], int]:
        available = self.suffix_masks[start] & ~forbidden_mask
        infos: list[_CandidateInfo] = []
        endpoint_union = 0
        while available:
            bit = available & -available
            i = bit.bit_length() - 1
            neighbors = self.link_masks[i] & selected_mask
            increment = neighbors.bit_count()
            if (
                defect + increment <= defect_budget
                and self._neighbors_in_distinct_components(neighbors)
            ):
                infos.append(_CandidateInfo(i, increment))
                endpoint_union |= self.edge_endpoint_masks[i]
            available ^= bit
        return infos, endpoint_union


    def _is_blocked_by_selected(self, i: int, selected_mask: int) -> bool:
        if self.endpoint_conflict_masks[i] & selected_mask:
            return True
        if self.cycle_conflict_masks[i] & selected_mask:
            return True
        neighbors = self.link_masks[i] & selected_mask
        return not self._neighbors_in_distinct_components(neighbors)

    @staticmethod
    def _small_hitting_set_exists(constraints: list[int], slots: int) -> bool:
        """Whether the bit-mask family has a hitting set of size <= slots."""
        if not constraints:
            return True
        if slots == 0:
            return False
        first = min(constraints, key=int.bit_count)
        choices = first
        while choices:
            bit = choices & -choices
            residual = [mask for mask in constraints if not (mask & bit)]
            if _CubicInteractionSolver._small_hitting_set_exists(residual, slots - 1):
                return True
            choices ^= bit
        return False

    def _rigid_maximality_filter(
        self,
        infos: list[_CandidateInfo],
        selected_mask: int,
        need: int,
    ) -> list[_CandidateInfo] | None:
        """Safe near-leaf pruning from edges that cannot be cycle-blocked.

        If an unselected edge can have at most one linked selected edge over
        the whole remaining branch, it can never be blocked by creating a
        cycle in the contracted forest.  It must therefore be selected itself
        or hard-conflicted by a future selected edge.
        """
        if need > 2:
            return infos
        available_mask = 0
        for info in infos:
            available_mask |= 1 << info.index
        possible_selected = selected_mask | available_mask
        constraints: list[int] = []
        remaining_edges = self.all_edges_mask & ~selected_mask
        while remaining_edges:
            bit = remaining_edges & -remaining_edges
            j = bit.bit_length() - 1
            remaining_edges ^= bit
            if self._is_blocked_by_selected(j, selected_mask):
                continue
            if (self.link_masks[j] & possible_selected).bit_count() >= 2:
                continue
            dominators = (self.hard_conflict_masks[j] | bit) & available_mask
            if dominators == 0:
                self.prune_rigid_maximality += 1
                return None
            constraints.append(dominators)

        if not constraints:
            return infos
        if not self._small_hitting_set_exists(constraints, need):
            self.prune_rigid_maximality += 1
            return None
        if need == 1:
            allowed = constraints[0]
            for mask in constraints[1:]:
                allowed &= mask
            if allowed == 0:
                self.prune_rigid_maximality += 1
                return None
            return [info for info in infos if allowed & (1 << info.index)]
        return infos

    def _find_size_k_zero_defect(self, k: int) -> tuple[int, ...] | None:
        """Solve the defect-zero target as a two-relation domination problem.

        When the contracted interaction forest has no link edge, selected
        candidates must be independent in ``hard OR link``.  Moreover an
        unselected graph edge cannot be cycle-blocked through the link forest;
        it must be selected itself or hard-conflicted by a selected candidate.

        Thus the target is an independent dominating set with one relation for
        incompatibility and a (smaller) relation for domination.  Branching on
        an undominated edge is complete: every solution must choose that edge
        or one of its hard-conflict neighbours.
        """
        chosen: list[int] = []
        failed: set[tuple[int, int, int]] = set()

        def dfs(
            available_mask: int,
            dominated_mask: int,
            need: int,
        ) -> tuple[int, ...] | None:
            self.recursion_nodes += 1
            self.zero_defect_nodes += 1

            if need == 0:
                if dominated_mask == self.all_edges_mask:
                    self.complete_candidates += 1
                    return tuple(chosen)
                return None
            if available_mask.bit_count() < need:
                self.prune_capacity += 1
                return None

            state = (available_mask, dominated_mask, need)
            if state in failed:
                self.zero_defect_failed_cache_hits += 1
                return None

            undominated = self.all_edges_mask & ~dominated_mask
            best_choices = 0
            best_count = self.m + 1
            layer = undominated
            max_cover = 0

            # Fail-first domination constraint: every currently undominated
            # candidate e must be selected or hard-dominated by a future edge.
            while layer:
                bit = layer & -layer
                e = bit.bit_length() - 1
                choices = self.hard_domination_masks[e] & available_mask
                count = choices.bit_count()
                if count == 0:
                    failed.add(state)
                    self.zero_defect_failed_states = len(failed)
                    return None
                if count < best_count:
                    best_count = count
                    best_choices = choices
                layer ^= bit

            # A safe set-cover lower bound on the number of remaining choices.
            layer = available_mask
            while layer:
                bit = layer & -layer
                i = bit.bit_length() - 1
                cover = (self.hard_domination_masks[i] & undominated).bit_count()
                if cover > max_cover:
                    max_cover = cover
                layer ^= bit
            if max_cover == 0 or (undominated.bit_count() + max_cover - 1) // max_cover > need:
                self.prune_capacity += 1
                failed.add(state)
                self.zero_defect_failed_states = len(failed)
                return None

            options: list[tuple[int, int, int]] = []
            layer = best_choices
            while layer:
                bit = layer & -layer
                i = bit.bit_length() - 1
                coverage = (self.hard_domination_masks[i] & undominated).bit_count()
                residual_freedom = (
                    available_mask & ~self.zero_defect_conflict_masks[i]
                ).bit_count()
                options.append((-coverage, -residual_freedom, i))
                layer ^= bit
            options.sort()

            for _, _, i in options:
                bit_i = 1 << i
                chosen.append(i)
                result = dfs(
                    available_mask
                    & ~self.zero_defect_conflict_masks[i]
                    & ~bit_i,
                    dominated_mask | self.hard_domination_masks[i],
                    need - 1,
                )
                if result is not None:
                    return result
                chosen.pop()

            failed.add(state)
            self.zero_defect_failed_states = len(failed)
            return None

        return dfs(self.all_edges_mask, 0, k)

    def _find_size_k(self, k: int, defect_budget: int) -> tuple[int, ...] | None:
        chosen: list[int] = []

        def dfs(
            start: int,
            selected_mask: int,
            forbidden_mask: int,
            defect: int,
        ) -> tuple[int, ...] | None:
            self.recursion_nodes += 1
            need = k - len(chosen)
            if need == 0:
                self.complete_candidates += 1
                if not self._is_maximal(selected_mask):
                    return None

                c = k - defect
                t = self._count_tree_components_of_unmatched(selected_mask)
                if t < 0 or self.n != 4 * k + 2 * (c - t):
                    self.prune_profile += 1
                    return None
                return tuple(chosen)

            if self.m - start < need:
                self.prune_capacity += 1
                return None

            infos, endpoint_union = self._candidate_infos(
                start, selected_mask, forbidden_mask, defect, defect_budget
            )
            if len(infos) < need or endpoint_union.bit_count() < 2 * need:
                self.prune_capacity += 1
                return None
            filtered = self._rigid_maximality_filter(infos, selected_mask, need)
            if filtered is None or len(filtered) < need:
                return None
            infos = filtered

            increments = sorted(info.defect_increment for info in infos)
            if defect + sum(increments[:need]) > defect_budget:
                self.prune_defect_lb += 1
                return None

            remaining_budget = defect_budget - defect
            average_needed = remaining_budget / need
            infos.sort(
                key=lambda info: (
                    abs(info.defect_increment - average_needed),
                    -(
                        (self.hard_conflict_masks[info.index] | self.link_masks[info.index])
                        & self.suffix_masks[start]
                    ).bit_count(),
                    info.index,
                )
            )

            for info in infos:
                i = info.index
                bit_i = 1 << i
                if defect + info.defect_increment > defect_budget:
                    self.prune_defect += 1
                    continue

                trial = self._try_add(i, selected_mask)
                if trial is None:
                    self.prune_cycle += 1
                    continue
                snapshot, increment = trial
                chosen.append(i)
                result = dfs(
                    i + 1,
                    selected_mask | bit_i,
                    forbidden_mask | self.hard_conflict_masks[i] | bit_i,
                    defect + increment,
                )
                if result is not None:
                    return result
                chosen.pop()
                self.dsu.rollback(snapshot)
            return None

        return dfs(0, 0, 0, 0)

    def _greedy_upper_bound(self) -> tuple[int, tuple[int, ...]]:
        selected = 0
        chosen: list[int] = []
        dsu = _RollbackDSU(self.m)

        while True:
            best_key: tuple[int, int, int] | None = None
            best_i = -1
            for i in range(self.m):
                bit = 1 << i
                if selected & bit:
                    continue
                if self.endpoint_conflict_masks[i] & selected:
                    continue
                if self.cycle_conflict_masks[i] & selected:
                    continue

                neighbors = self.link_masks[i] & selected
                roots: set[int] = set()
                valid = True
                layer = neighbors
                while layer:
                    b = layer & -layer
                    j = b.bit_length() - 1
                    root = dsu.find(j)
                    if root in roots:
                        valid = False
                        break
                    roots.add(root)
                    layer ^= b
                if not valid:
                    continue

                domination = (
                    (self.hard_conflict_masks[i] | self.link_masks[i]) & ~selected
                ).bit_count()
                key = (domination, neighbors.bit_count(), -i)
                if best_key is None or key > best_key:
                    best_key = key
                    best_i = i

            if best_i < 0:
                break

            dsu.activate(best_i)
            neighbors = self.link_masks[best_i] & selected
            while neighbors:
                bit = neighbors & -neighbors
                j = bit.bit_length() - 1
                if not dsu.union(best_i, j):
                    raise AssertionError("greedy interaction forest inconsistency")
                neighbors ^= bit
            selected |= 1 << best_i
            chosen.append(best_i)

        return len(chosen), tuple(chosen)

    def solve(self) -> SolverResult:
        start_time = perf_counter()
        lower_bound = ceil((self.n - 1) / 5)

        def attempt(k: int) -> tuple[int, ...] | None:
            defect_budget = min(k - 1, 5 * k + 1 - self.n)
            if defect_budget < 0:
                return None
            before_nodes = self.recursion_nodes
            before_complete = self.complete_candidates
            attempt_start = perf_counter()
            if defect_budget == 0:
                search_mode = "zero-defect-domination"
                witness = self._find_size_k_zero_defect(k)
            else:
                search_mode = "interaction-forest-bnb"
                witness = self._find_size_k(k, defect_budget)
            self.target_attempts.append(
                {
                    "k": k,
                    "defect_budget": defect_budget,
                    "runtime_seconds": perf_counter() - attempt_start,
                    "recursion_nodes": self.recursion_nodes - before_nodes,
                    "complete_candidates": self.complete_candidates - before_complete,
                    "found": witness is not None,
                    "search_mode": search_mode,
                }
            )
            return witness

        # Search the proved lower-bound target before spending time on a
        # heuristic upper bound.  Equality instances terminate here, and the
        # zero-defect residue class is then essentially a domination search.
        best_witness = attempt(lower_bound)
        greedy_size: int | None = None
        if best_witness is not None:
            optimum = lower_bound
        else:
            greedy_size, greedy_witness = self._greedy_upper_bound()
            optimum = greedy_size
            best_witness = greedy_witness
            for k in range(lower_bound + 1, greedy_size + 1):
                witness = attempt(k)
                if witness is not None:
                    optimum = k
                    best_witness = witness
                    break

        if best_witness is None:
            raise RuntimeError("Solver C failed to obtain any maximal acyclic matching.")
        matching: tuple[Edge, ...] = tuple(
            (self.nodes[self.edges[i][0]], self.nodes[self.edges[i][1]])
            for i in best_witness
        )
        if not is_maximal_acyclic_matching(self.original_graph, matching):
            raise AssertionError("Solver C produced an invalid certificate.")

        return SolverResult(
            mu=optimum,
            matching=matching,
            solver="C-cubic-interaction-BnB",
            runtime_seconds=perf_counter() - start_time,
            states_examined=self.complete_candidates,
            forest_tests=0,
            forest_cache_hits=0,
            maximality_tests=self.maximality_tests,
            metadata={
                "lower_bound": lower_bound,
                "greedy_upper_bound": greedy_size,
                "recursion_nodes": self.recursion_nodes,
                "complete_candidates": self.complete_candidates,
                "prune_cycle": self.prune_cycle,
                "prune_defect": self.prune_defect,
                "prune_capacity": self.prune_capacity,
                "prune_defect_lower_bound": self.prune_defect_lb,
                "prune_profile": self.prune_profile,
                "prune_rigid_maximality": self.prune_rigid_maximality,
                "zero_defect_nodes": self.zero_defect_nodes,
                "zero_defect_failed_cache_hits": self.zero_defect_failed_cache_hits,
                "zero_defect_failed_states": self.zero_defect_failed_states,
                "target_attempts": self.target_attempts,
            },
        )



def minimum_maximal_acyclic_matching_cubic(G: nx.Graph) -> SolverResult:
    """Solver C: exact structure-aware solver for connected cubic graphs."""
    return _CubicInteractionSolver(G).solve()


def find_maximal_acyclic_matching_at_most_k_cubic(
    G: nx.Graph, parameter_k: int
) -> tuple[Edge, ...] | None:
    """Decision/search form with the 5k+1 kernel rule.

    Returns one maximal acyclic matching of cardinality at most ``parameter_k``
    or ``None`` if no such matching exists.  If ``n > 5*parameter_k + 1``, the
    structural theorem rejects the instance before any exponential search.
    """
    if parameter_k < 0:
        return None
    solver = _CubicInteractionSolver(G)
    if solver.n > 5 * parameter_k + 1:
        return None

    lower_bound = ceil((solver.n - 1) / 5)
    for k in range(lower_bound, min(parameter_k, solver.n // 2) + 1):
        defect_budget = min(k - 1, 5 * k + 1 - solver.n)
        if defect_budget < 0:
            continue
        witness = (
            solver._find_size_k_zero_defect(k)
            if defect_budget == 0
            else solver._find_size_k(k, defect_budget)
        )
        if witness is None:
            continue
        matching: tuple[Edge, ...] = tuple(
            (solver.nodes[solver.edges[i][0]], solver.nodes[solver.edges[i][1]])
            for i in witness
        )
        if not is_maximal_acyclic_matching(G, matching):
            raise AssertionError("Solver C decision routine produced an invalid certificate.")
        return matching
    return None
