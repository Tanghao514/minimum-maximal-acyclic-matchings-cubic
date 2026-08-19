from __future__ import annotations

import csv
import gc
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import Callable

import networkx as nx

from src.acyclic_matching import is_maximal_acyclic_matching
from src.solver_c import _CubicInteractionSolver


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "results" / "solver_bc_full_census_20260819"
CENSUS_CSV = RUN_DIR / "solver_bc_census_per_graph.csv"
OUT = RUN_DIR / "solver_c_ablation_complete.csv"
REPEATS = 3
SAMPLE_SIZE = 100


def no_memo_zero_defect(solver: _CubicInteractionSolver, k: int) -> tuple[int, ...] | None:
    chosen: list[int] = []

    def dfs(available_mask: int, dominated_mask: int, need: int) -> tuple[int, ...] | None:
        solver.recursion_nodes += 1
        solver.zero_defect_nodes += 1
        if need == 0:
            if dominated_mask == solver.all_edges_mask:
                solver.complete_candidates += 1
                return tuple(chosen)
            return None
        if available_mask.bit_count() < need:
            solver.prune_capacity += 1
            return None

        undominated = solver.all_edges_mask & ~dominated_mask
        best_choices = 0
        best_count = solver.m + 1
        layer = undominated
        max_cover = 0
        while layer:
            bit = layer & -layer
            edge = bit.bit_length() - 1
            choices = solver.hard_domination_masks[edge] & available_mask
            count = choices.bit_count()
            if count == 0:
                return None
            if count < best_count:
                best_count = count
                best_choices = choices
            layer ^= bit

        layer = available_mask
        while layer:
            bit = layer & -layer
            index = bit.bit_length() - 1
            cover = (solver.hard_domination_masks[index] & undominated).bit_count()
            max_cover = max(max_cover, cover)
            layer ^= bit
        if max_cover == 0 or math.ceil(undominated.bit_count() / max_cover) > need:
            solver.prune_capacity += 1
            return None

        options = []
        layer = best_choices
        while layer:
            bit = layer & -layer
            index = bit.bit_length() - 1
            coverage = (solver.hard_domination_masks[index] & undominated).bit_count()
            freedom = (available_mask & ~solver.zero_defect_conflict_masks[index]).bit_count()
            options.append((-coverage, -freedom, index))
            layer ^= bit
        options.sort()
        for _, _, index in options:
            bit = 1 << index
            chosen.append(index)
            result = dfs(
                available_mask & ~solver.zero_defect_conflict_masks[index] & ~bit,
                dominated_mask | solver.hard_domination_masks[index],
                need - 1,
            )
            if result is not None:
                return result
            chosen.pop()
        return None

    return dfs(solver.all_edges_mask, 0, k)


def select_representative_rows() -> list[dict[str, str]]:
    with CENSUS_CSV.open(newline="", encoding="utf-8") as fh:
        rows = [row for row in csv.DictReader(fh) if int(row["n"]) == 16]
    strata: dict[tuple[int, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        strata[(int(row["mu_solver_b"]), int(row["defect_budget"]))].append(row)
    selected: list[dict[str, str]] = []
    keys = sorted(strata)
    quota = math.ceil(SAMPLE_SIZE / len(keys))
    for key in keys:
        group = strata[key]
        take = min(quota, len(group))
        indices = [round(i * (len(group) - 1) / max(1, take - 1)) for i in range(take)]
        selected.extend(group[index] for index in indices)
    if len(selected) < SAMPLE_SIZE:
        used = {row["graph_id"] for row in selected}
        selected.extend(row for row in rows if row["graph_id"] not in used) 
    return sorted(selected[:SAMPLE_SIZE], key=lambda row: row["graph_id"])


def run_variant(G: nx.Graph, mu: int, variant: str) -> dict[str, object]:
    runtimes = []
    last: dict[str, object] | None = None
    for _ in range(REPEATS):
        solver = _CubicInteractionSolver(G)
        budget = min(mu - 1, 5 * mu + 1 - len(G))
        if variant == "c_without_near_leaf_maximality_pruning":
            solver._rigid_maximality_filter = lambda infos, selected, need: infos  # type: ignore[method-assign]

        def search() -> tuple[int, ...] | None:
            if variant == "c_without_defect_budget":
                return solver._find_size_k(mu, mu - 1)
            if variant == "c_without_zero_defect_special_solver":
                return solver._find_size_k(mu, budget)
            if variant == "c_without_failed_state_memoization" and budget == 0:
                return no_memo_zero_defect(solver, mu)
            if budget == 0:
                return solver._find_size_k_zero_defect(mu)
            return solver._find_size_k(mu, budget)

        gc.collect()
        gc.disable()
        try:
            start = perf_counter()
            witness = search()
            elapsed = perf_counter() - start
        finally:
            gc.enable()
        if witness is None:
            raise AssertionError(f"Ablation variant {variant} failed to find the known optimum")
        matching = tuple(
            (solver.nodes[solver.edges[i][0]], solver.nodes[solver.edges[i][1]]) for i in witness
        )
        if not is_maximal_acyclic_matching(G, matching):
            raise AssertionError(f"Ablation variant {variant} returned an invalid witness")
        runtimes.append(elapsed)
        last = {
            "search_nodes": solver.recursion_nodes,
            "complete_candidates": solver.complete_candidates,
            "rigid_prunes": solver.prune_rigid_maximality,
            "failed_cache_hits": solver.zero_defect_failed_cache_hits,
            "failed_states": solver.zero_defect_failed_states,
        }
    assert last is not None
    return {
        "runtime_seconds": statistics.median(runtimes),
        "raw_times": json.dumps(runtimes),
        **last,
    }


def main() -> None:
    variants = (
        "c_full",
        "c_without_defect_budget",
        "c_without_zero_defect_special_solver",
        "c_without_failed_state_memoization",
        "c_without_near_leaf_maximality_pruning",
    )
    rows = []
    sample = select_representative_rows()
    for number, source in enumerate(sample, start=1):
        G = nx.from_graph6_bytes(source["graph6"].encode("ascii"))
        mu = int(source["mu_solver_b"])
        for variant in variants:
            result = run_variant(G, mu, variant)
            rows.append(
                {
                    "graph_id": source["graph_id"],
                    "n": 16,
                    "mu": mu,
                    "defect_budget": int(source["defect_budget"]),
                    "variant": variant,
                    "repetitions": REPEATS,
                    **result,
                }
            )
        if number % 10 == 0:
            print(f"Ablation {number}/{len(sample)} graphs complete", flush=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} ablation rows to {OUT}", flush=True)


if __name__ == "__main__":
    main()
