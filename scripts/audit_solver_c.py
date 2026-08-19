from __future__ import annotations

from itertools import combinations
import json
from pathlib import Path

import networkx as nx

from src.acyclic_matching import is_acyclic_matching, is_matching, is_maximal_acyclic_matching
from src.exact_solver import minimum_maximal_acyclic_matching
from src.solver_c import _CubicInteractionSolver, minimum_maximal_acyclic_matching_cubic

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "solver_c_audit.json"


def canonical(e):
    return frozenset(e)


def interaction_state(solver: _CubicInteractionSolver, selected_indices: tuple[int, ...]):
    snapshot = solver.dsu.snapshot()
    selected_mask = 0
    valid = True
    for i in sorted(selected_indices):
        if solver.hard_conflict_masks[i] & selected_mask:
            valid = False
            break
        trial = solver._try_add(i, selected_mask)
        if trial is None:
            valid = False
            break
        _, _ = trial
        selected_mask |= 1 << i
    return snapshot, selected_mask, valid


def audit_all_matchings(G: nx.Graph):
    solver = _CubicInteractionSolver(G)
    index = {canonical((solver.nodes[u], solver.nodes[v])): i for i, (u, v) in enumerate(solver.edges)}
    edges = tuple(G.edges)
    counts = {"subsets": 0, "matchings": 0, "acyclic": 0, "maximal_acyclic": 0}

    for r in range(len(G) // 2 + 1):
        for cand in combinations(edges, r):
            counts["subsets"] += 1
            if not is_matching(G, cand):
                continue
            counts["matchings"] += 1
            selected = tuple(index[canonical(e)] for e in cand)
            snap, selected_mask, interaction_acyclic = interaction_state(solver, selected)
            reference_acyclic = is_acyclic_matching(G, cand)
            if interaction_acyclic != reference_acyclic:
                raise AssertionError(("acyclic mismatch", nx.to_graph6_bytes(G).strip(), cand))
            if reference_acyclic:
                counts["acyclic"] += 1
                interaction_maximal = solver._is_maximal(selected_mask)
                reference_maximal = is_maximal_acyclic_matching(G, cand)
                if interaction_maximal != reference_maximal:
                    raise AssertionError(("maximal mismatch", nx.to_graph6_bytes(G).strip(), cand))
                if reference_maximal:
                    counts["maximal_acyclic"] += 1
            solver.dsu.rollback(snap)
    return counts


def main():
    graphs = [
        ("K4", nx.complete_graph(4)),
        ("K33", nx.complete_bipartite_graph(3, 3)),
        ("cube", nx.cubical_graph()),
        ("Petersen", nx.petersen_graph()),
        ("prism10", nx.circular_ladder_graph(5)),
    ]
    exhaustive = {}
    for name, G in graphs:
        exhaustive[name] = audit_all_matchings(G)
        print(name, exhaustive[name], flush=True)

    random_crosschecks = 0
    for n in (10, 12, 14, 16, 18, 20):
        made = 0
        seed = 0
        while made < 20:
            G = nx.random_regular_graph(3, n, seed=500000 + 1000 * n + seed)
            seed += 1
            if not nx.is_connected(G):
                continue
            b = minimum_maximal_acyclic_matching(G)
            c = minimum_maximal_acyclic_matching_cubic(G)
            if b.mu != c.mu:
                raise AssertionError(("optimum mismatch", n, seed, b.mu, c.mu))
            random_crosschecks += 1
            made += 1
        print("random", n, made, flush=True)

    result = {
        "exhaustive_interaction_equivalence": exhaustive,
        "random_solver_b_c_crosschecks": random_crosschecks,
        "discrepancies": 0,
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
