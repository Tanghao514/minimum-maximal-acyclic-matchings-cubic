from __future__ import annotations

import csv
import argparse
import gc
import hashlib
import json
import math
import os
import platform
import random
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

import networkx as nx

from src.acyclic_matching import is_maximal_acyclic_matching
from src.exact_solver import SolverResult, minimum_maximal_acyclic_matching
from src.solver_c import minimum_maximal_acyclic_matching_cubic


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "results" / "solver_bc_full_census_20260819"
CENSUS_DIR = RUN_DIR / "census"
EXPECTED_COUNTS = {4: 1, 6: 2, 8: 5, 10: 19, 12: 85, 14: 509, 16: 4060}
COUNTEREXAMPLES_N16 = (
    b"O^o?GGB?w????B@@`@??X",
    b"O^o?GGB?w??@?A@@`@??L",
    b"O^o?GGB?w??@?B@?`@??J",
    b"O^o?GGB?wW?@?@?@??W?F",
)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if not rows and fieldnames is None:
        raise ValueError(f"Cannot infer columns for empty CSV: {path}")
    columns = fieldnames or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def graph6_text(G: nx.Graph) -> str:
    return nx.to_graph6_bytes(G, header=False).strip().decode("ascii")


def validate_cubic_graph(G: nx.Graph, expected_n: int | None = None) -> None:
    if expected_n is not None and len(G) != expected_n:
        raise AssertionError(f"Expected n={expected_n}, got {len(G)}")
    if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)) or G.is_directed():
        raise AssertionError("Census graph is not simple undirected")
    if not nx.is_connected(G) or any(degree != 3 for _, degree in G.degree):
        raise AssertionError("Census graph is not connected cubic")


def checked_solve(
    solver: Callable[[nx.Graph], SolverResult], G: nx.Graph
) -> tuple[SolverResult, float]:
    gc.collect()
    gc.disable()
    try:
        start = perf_counter()
        result = solver(G)
        elapsed = perf_counter() - start
    finally:
        gc.enable()
    if not is_maximal_acyclic_matching(G, result.matching):
        raise AssertionError(f"{result.solver} returned an invalid witness")
    if len(result.matching) != result.mu:
        raise AssertionError(f"{result.solver} witness size does not equal mu")
    return result, elapsed


def correctness_cases() -> list[tuple[str, nx.Graph]]:
    cases: list[tuple[str, nx.Graph]] = [
        ("K4", nx.complete_graph(4)),
        ("K3,3", nx.complete_bipartite_graph(3, 3)),
        ("cube", nx.cubical_graph()),
        ("Petersen", nx.petersen_graph()),
    ]
    for n in (6, 8, 10, 12, 14, 16):
        cases.append((f"prism_n{n}", nx.circular_ladder_graph(n // 2)))
    for index, encoded in enumerate(COUNTEREXAMPLES_N16):
        cases.append((f"supplied_counterexample_{index}", nx.from_graph6_bytes(encoded)))

    made = 0
    candidate = 0
    rng = random.Random(20260819)
    while made < 50:
        n = (10, 12, 14, 16, 18)[made % 5]
        seed = rng.randrange(1, 2**31)
        G = nx.random_regular_graph(3, n, seed=seed)
        candidate += 1
        if not nx.is_connected(G):
            continue
        cases.append((f"random_connected_{made:02d}_n{n}_seed{seed}", G))
        made += 1
    return cases


def run_correctness_gate() -> dict[str, Any]:
    rows = []
    for name, G in correctness_cases():
        validate_cubic_graph(G)
        b, tb = checked_solve(minimum_maximal_acyclic_matching, G)
        c, tc = checked_solve(minimum_maximal_acyclic_matching_cubic, G)
        if b.mu != c.mu:
            raise AssertionError(f"Correctness discrepancy on {name}: B={b.mu}, C={c.mu}")
        rows.append(
            {
                "case": name,
                "n": len(G),
                "graph6": graph6_text(G),
                "mu_solver_b": b.mu,
                "mu_solver_c": c.mu,
                "solver_b_witness_valid": True,
                "solver_c_witness_valid": True,
                "solver_b_seconds": tb,
                "solver_c_seconds": tc,
            }
        )
    result = {
        "status": "passed",
        "cases": len(rows),
        "standard_and_prism_cases": 10,
        "supplied_counterexamples": 4,
        "fixed_seed_random_connected_cubic_cases": 50,
        "definition_level_witness_checks": 2 * len(rows),
        "discrepancies": 0,
        "details": rows,
    }
    write_json(RUN_DIR / "correctness_check.json", result)
    return result


def load_census() -> dict[int, list[tuple[str, nx.Graph]]]:
    census: dict[int, list[tuple[str, nx.Graph]]] = {}
    for n, expected in EXPECTED_COUNTS.items():
        path = CENSUS_DIR / f"connected_cubic_n{n}.g6"
        lines = [line.strip() for line in path.read_bytes().splitlines() if line.strip()]
        if len(lines) != expected:
            raise AssertionError(f"Census count mismatch at n={n}: {len(lines)} != {expected}")
        layer = []
        for index, encoded in enumerate(lines):
            G = nx.from_graph6_bytes(encoded)
            validate_cubic_graph(G, n)
            canonical = encoded.decode("ascii")
            layer.append((canonical, G))
        census[n] = layer
    if sum(map(len, census.values())) != 4681:
        raise AssertionError("Core census total is not 4681")
    return census


def quantile(values: list[float], q: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lo = math.floor(position)
    hi = math.ceil(position)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - position) + ordered[hi] * (position - lo)


def geometric_mean(values: list[float]) -> float:
    positive = [value for value in values if value > 0]
    if len(positive) != len(values):
        return math.nan
    return math.exp(sum(math.log(value) for value in positive) / len(positive))


def median_int(values: list[int]) -> int:
    return int(statistics.median(values))


def run_timed_layer(n: int, items: list[tuple[str, nx.Graph]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    repeats = 5 if n <= 12 else 3
    sample_count = len(items)
    times: dict[str, list[list[float]]] = {
        "B": [[] for _ in range(sample_count)],
        "C": [[] for _ in range(sample_count)],
    }
    results: dict[str, list[SolverResult | None]] = {
        "B": [None] * sample_count,
        "C": [None] * sample_count,
    }
    stage_totals: dict[str, list[float]] = {"B": [], "C": []}
    solvers = {
        "B": minimum_maximal_acyclic_matching,
        "C": minimum_maximal_acyclic_matching_cubic,
    }

    # Untimed warm-up. Solver instances and their caches are call-local.
    for label in ("B", "C"):
        warm = solvers[label](items[0][1])
        if not is_maximal_acyclic_matching(items[0][1], warm.matching):
            raise AssertionError(f"Warm-up witness failure in Solver {label}")

    for repetition in range(repeats):
        order = ("B", "C") if repetition % 2 == 0 else ("C", "B")
        for label in order:
            gc.collect()
            batch_start = perf_counter()
            for index, (_, G) in enumerate(items):
                gc.disable()
                try:
                    start = perf_counter()
                    result = solvers[label](G)
                    elapsed = perf_counter() - start
                finally:
                    gc.enable()
                if not is_maximal_acyclic_matching(G, result.matching):
                    raise AssertionError(f"Invalid witness at n={n}, index={index}, Solver {label}")
                previous = results[label][index]
                if previous is not None and previous.mu != result.mu:
                    raise AssertionError(f"Non-deterministic optimum at n={n}, index={index}, Solver {label}")
                results[label][index] = result
                times[label][index].append(elapsed)
            stage_totals[label].append(perf_counter() - batch_start)
            print(
                f"n={n:2d} repeat={repetition + 1}/{repeats} solver={label} "
                f"graphs={sample_count} batch={stage_totals[label][-1]:.6f}s",
                flush=True,
            )

    rows: list[dict[str, Any]] = []
    for index, (encoded, _) in enumerate(items):
        b = results["B"][index]
        c = results["C"][index]
        assert b is not None and c is not None
        if b.mu != c.mu:
            raise AssertionError(f"Census discrepancy at n={n}, index={index}: B={b.mu}, C={c.mu}")
        tb = statistics.median(times["B"][index])
        tc = statistics.median(times["C"][index])
        b_candidates = b.states_examined
        c_candidates = c.states_examined
        row = {
            "n": n,
            "graph_id": f"n{n}_{index:04d}",
            "graph6": encoded,
            "mu_solver_b": b.mu,
            "mu_solver_c": c.mu,
            "runtime_solver_b": tb,
            "runtime_solver_c": tc,
            "search_nodes_solver_b": b_candidates,
            "search_nodes_solver_c": c_candidates,
            "solver_c_recursion_nodes": c.metadata["recursion_nodes"],
            "speedup": tb / tc,
            "node_reduction": (b_candidates - c_candidates) / b_candidates if b_candidates else math.nan,
            "defect_budget": 5 * b.mu + 1 - n,
            "repetitions": repeats,
            "solver_b_times": json.dumps(times["B"][index]),
            "solver_c_times": json.dumps(times["C"][index]),
        }
        rows.append(row)

    checkpoint = RUN_DIR / f"checkpoint_census_n{n}.csv"
    write_csv(checkpoint, rows)
    stage = {
        "n": n,
        "graph_count": sample_count,
        "repetitions": repeats,
        "solver_b_batch_seconds": stage_totals["B"],
        "solver_c_batch_seconds": stage_totals["C"],
        "solver_b_batch_median_seconds": statistics.median(stage_totals["B"]),
        "solver_c_batch_median_seconds": statistics.median(stage_totals["C"]),
    }
    write_json(RUN_DIR / f"checkpoint_stage_n{n}.json", stage)
    return rows, stage


def summarize(all_rows: list[dict[str, Any]], stages: list[dict[str, Any]]) -> None:
    by_n = {n: [row for row in all_rows if row["n"] == n] for n in EXPECTED_COUNTS}
    stage_by_n = {stage["n"]: stage for stage in stages}
    summary_rows = []
    distribution_rows = []
    for n, rows in by_n.items():
        stage = stage_by_n[n]
        b_total = stage["solver_b_batch_median_seconds"]
        c_total = stage["solver_c_batch_median_seconds"]
        b_nodes = sum(int(row["search_nodes_solver_b"]) for row in rows)
        c_nodes = sum(int(row["search_nodes_solver_c"]) for row in rows)
        discrepancies = sum(row["mu_solver_b"] != row["mu_solver_c"] for row in rows)
        summary_rows.append(
            {
                "n": n,
                "graph_count": len(rows),
                "total_runtime_solver_b": b_total,
                "total_runtime_solver_c": c_total,
                "total_speedup": b_total / c_total,
                "total_search_nodes_solver_b": b_nodes,
                "total_search_nodes_solver_c": c_nodes,
                "total_node_reduction": (b_nodes - c_nodes) / b_nodes if b_nodes else math.nan,
                "discrepancies": discrepancies,
                "timeouts_solver_b": 0,
                "timeouts_solver_c": 0,
                "repetitions": stage["repetitions"],
            }
        )
        speedups = [float(row["speedup"]) for row in rows]
        distribution_rows.append(
            {
                "n": n,
                "graph_count": len(rows),
                "median_speedup": statistics.median(speedups),
                "mean_speedup": statistics.mean(speedups),
                "geometric_mean_speedup": geometric_mean(speedups),
                "min_speedup": min(speedups),
                "q25_speedup": quantile(speedups, 0.25),
                "q75_speedup": quantile(speedups, 0.75),
                "max_speedup": max(speedups),
                "solver_c_slower_count": sum(value < 1 for value in speedups),
            }
        )

    groups: dict[tuple[int, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in all_rows:
        defect = int(row["defect_budget"])
        defect_bin = str(defect) if defect <= 4 else ">=5"
        groups[(int(row["n"]), int(row["mu_solver_b"]), defect_bin)].append(row)
    defect_rows = []
    for (n, mu, defect_bin), rows in sorted(groups.items()):
        speedups = [float(row["speedup"]) for row in rows]
        defect_rows.append(
            {
                "n": n,
                "mu": mu,
                "defect_budget_bin": defect_bin,
                "graph_count": len(rows),
                "median_speedup": statistics.median(speedups),
                "geometric_mean_speedup": geometric_mean(speedups),
                "median_runtime_solver_b": statistics.median(float(row["runtime_solver_b"]) for row in rows),
                "median_runtime_solver_c": statistics.median(float(row["runtime_solver_c"]) for row in rows),
                "solver_c_slower_count": sum(value < 1 for value in speedups),
            }
        )

    write_csv(RUN_DIR / "solver_bc_census_summary.csv", summary_rows)
    write_csv(RUN_DIR / "solver_bc_speedup_distribution.csv", distribution_rows)
    write_csv(RUN_DIR / "solver_bc_by_defect.csv", defect_rows)


def environment_record() -> dict[str, Any]:
    try:
        import psutil  # type: ignore

        physical_cores = psutil.cpu_count(logical=False)
        logical_cores = psutil.cpu_count(logical=True)
        ram_bytes = psutil.virtual_memory().total
    except Exception:
        physical_cores = None
        logical_cores = os.cpu_count()
        ram_bytes = None
    source_files = [ROOT / "src" / name for name in ("exact_solver.py", "solver_c.py", "acyclic_matching.py")]
    return {
        "experiment_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "operating_system": platform.platform(),
        "processor": platform.processor(),
        "physical_cores": physical_cores,
        "logical_cores": logical_cores,
        "ram_bytes": ram_bytes,
        "python_version": sys.version,
        "python_implementation": platform.python_implementation(),
        "networkx_version": nx.__version__,
        "compiler": platform.python_compiler(),
        "threading": "single-threaded Python solver calls; no concurrent benchmark jobs",
        "timer": "time.perf_counter",
        "nauty_version": "2.9.3",
        "nauty_generator": "geng -c -q -d3 -D3 n (3n/2)",
        "source_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in source_files},
        "census_sha256": {
            path.name: sha256(path) for path in sorted(CENSUS_DIR.glob("*.g6"))
        },
        "expected_census_counts": EXPECTED_COUNTS,
        "total_core_graphs": 4681,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=("all", "correctness", "census"),
        default="all",
        help="Run the correctness gate, the timed census, or both.",
    )
    args = parser.parse_args()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    write_json(RUN_DIR / "environment.json", environment_record())
    if args.phase in ("all", "correctness"):
        print("Running correctness gate...", flush=True)
        gate = run_correctness_gate()
        print(f"Correctness gate passed ({gate['cases']} cases).", flush=True)
        if args.phase == "correctness":
            return
    else:
        gate_path = RUN_DIR / "correctness_check.json"
        if not gate_path.exists() or json.loads(gate_path.read_text(encoding="utf-8"))["status"] != "passed":
            raise RuntimeError("A passed correctness_check.json is required before --phase census")
    census = load_census()
    print(f"Census count verified ({sum(map(len, census.values()))} graphs).", flush=True)

    all_rows: list[dict[str, Any]] = []
    stages: list[dict[str, Any]] = []
    for n in EXPECTED_COUNTS:
        rows, stage = run_timed_layer(n, census[n])
        all_rows.extend(rows)
        stages.append(stage)
    if len(all_rows) != 4681:
        raise AssertionError("Timed census output does not contain 4681 rows")
    write_csv(RUN_DIR / "solver_bc_census_per_graph.csv", all_rows)
    summarize(all_rows, stages)
    write_json(RUN_DIR / "census_stage_raw_times.json", stages)
    mu_counts = Counter((row["n"], row["mu_solver_b"]) for row in all_rows)
    write_json(
        RUN_DIR / "census_completion.json",
        {
            "status": "complete",
            "graphs": len(all_rows),
            "discrepancies": sum(row["mu_solver_b"] != row["mu_solver_c"] for row in all_rows),
            "mu_counts": {f"n{n}_mu{mu}": count for (n, mu), count in sorted(mu_counts.items())},
        },
    )
    print("Core full-census benchmark complete.", flush=True)


if __name__ == "__main__":
    main()
