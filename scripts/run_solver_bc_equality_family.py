from __future__ import annotations

import csv
import multiprocessing as mp
import statistics
from pathlib import Path
from time import perf_counter
from typing import Any

import networkx as nx

from src.acyclic_matching import is_maximal_acyclic_matching
from src.constructions import extremal_graph_for_order_direct
from src.exact_solver import minimum_maximal_acyclic_matching
from src.solver_c import minimum_maximal_acyclic_matching_cubic


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "results" / "solver_bc_full_census_20260819"
OUT = RUN_DIR / "solver_bc_equality_family.csv"
ORDERS = (16, 20, 24, 26, 28, 32, 36, 46, 56)
TIMEOUT_SECONDS = 300


def worker(connection: Any, encoded: bytes, solver_label: str) -> None:
    try:
        G = nx.from_graph6_bytes(encoded)
        solver = (
            minimum_maximal_acyclic_matching
            if solver_label == "B"
            else minimum_maximal_acyclic_matching_cubic
        )
        start = perf_counter()
        result = solver(G)
        elapsed = perf_counter() - start
        valid = is_maximal_acyclic_matching(G, result.matching)
        connection.send(
            {
                "status": "solved",
                "runtime_seconds": elapsed,
                "mu": result.mu,
                "witness_valid": valid,
                "complete_candidates": result.states_examined,
                "recursion_nodes": result.metadata.get("recursion_nodes", ""),
            }
        )
    except BaseException as exc:
        connection.send({"status": "error", "error": repr(exc)})
    finally:
        connection.close()


def timed_subprocess(encoded: bytes, solver_label: str) -> dict[str, Any]:
    context = mp.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=worker, args=(sender, encoded, solver_label))
    process.start()
    sender.close()
    if receiver.poll(TIMEOUT_SECONDS):
        result = receiver.recv()
        process.join(5)
        if process.is_alive():
            process.terminate()
            process.join()
        return result
    process.terminate()
    process.join()
    return {"status": "timeout", "runtime_seconds": TIMEOUT_SECONDS}


def main() -> None:
    rows = []
    for n in ORDERS:
        item = extremal_graph_for_order_direct(n)
        G = item.graph
        encoded = nx.to_graph6_bytes(G, header=False).strip()
        repeat_count = 3 if n <= 28 else 1
        per_solver: dict[str, list[dict[str, Any]]] = {"B": [], "C": []}
        for repetition in range(repeat_count):
            order = ("B", "C") if repetition % 2 == 0 else ("C", "B")
            for label in order:
                result = timed_subprocess(encoded, label)
                per_solver[label].append(result)
                print(
                    f"equality n={n} repeat={repetition + 1}/{repeat_count} "
                    f"solver={label} status={result['status']} "
                    f"seconds={result.get('runtime_seconds', '')}",
                    flush=True,
                )
        b_solved = [result for result in per_solver["B"] if result["status"] == "solved"]
        c_solved = [result for result in per_solver["C"] if result["status"] == "solved"]
        if b_solved and c_solved:
            if any(result["mu"] != b_solved[0]["mu"] for result in b_solved + c_solved):
                raise AssertionError(f"Equality-family optimum discrepancy at n={n}")
            if not all(result["witness_valid"] for result in b_solved + c_solved):
                raise AssertionError(f"Equality-family witness failure at n={n}")
        tb = statistics.median(result["runtime_seconds"] for result in b_solved) if b_solved else ""
        tc = statistics.median(result["runtime_seconds"] for result in c_solved) if c_solved else ""
        rows.append(
            {
                "n": n,
                "construction": item.metadata.get("family", "extremal_graph_for_order_direct"),
                "expected_equality_value": (n - 2) // 5 + 1,
                "solver_b_status": "solved" if len(b_solved) == repeat_count else per_solver["B"][-1]["status"],
                "solver_c_status": "solved" if len(c_solved) == repeat_count else per_solver["C"][-1]["status"],
                "solver_b_solved_repetitions": len(b_solved),
                "solver_c_solved_repetitions": len(c_solved),
                "repetitions": repeat_count,
                "timeout_seconds": TIMEOUT_SECONDS,
                "mu_solver_b": b_solved[0]["mu"] if b_solved else "",
                "mu_solver_c": c_solved[0]["mu"] if c_solved else "",
                "runtime_solver_b": tb,
                "runtime_solver_c": tc,
                "speedup": tb / tc if isinstance(tb, float) and isinstance(tc, float) else "",
                "search_nodes_solver_b": b_solved[-1]["complete_candidates"] if b_solved else "",
                "search_nodes_solver_c": c_solved[-1]["complete_candidates"] if c_solved else "",
                "solver_c_recursion_nodes": c_solved[-1]["recursion_nodes"] if c_solved else "",
            }
        )
        with OUT.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(f"Wrote equality-family results to {OUT}", flush=True)


if __name__ == "__main__":
    mp.freeze_support()
    main()
