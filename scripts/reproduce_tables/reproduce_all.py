#!/usr/bin/env python3
"""Reproduce machine-readable counterparts of manuscript Tables 1--8."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PER_GRAPH = ROOT / "results" / "per_graph" / "full_census.csv"
SUMMARY = ROOT / "results" / "benchmarks" / "processed" / "solver_bc_census_summary.csv"
EQUALITY = ROOT / "results" / "benchmarks" / "raw" / "solver_bc_equality_family.csv"
COUNTEREXAMPLES = ROOT / "data" / "counterexamples" / "metadata.json"
ENVIRONMENT = ROOT / "results" / "benchmarks" / "publication_environment.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path.relative_to(ROOT)} ({len(rows)} rows)")


def tables_1_and_2(output: Path) -> None:
    grouped: dict[int, list[int]] = defaultdict(list)
    for row in read_csv(PER_GRAPH):
        b, c = int(row["mu_solver_b"]), int(row["mu_solver_c"])
        if b != c:
            raise AssertionError(f"Solver discrepancy at {row['graph_id']}: {b} != {c}")
        grouped[int(row["n"])].append(b)
    table1: list[dict[str, object]] = []
    table2: list[dict[str, object]] = []
    for n in sorted(grouped):
        values = grouped[n]
        histogram = Counter(values)
        benchmark = n // 4
        table1.append({
            "n": n,
            "classes": len(values),
            "minimum": min(values),
            "maximum": max(values),
            "quarter_benchmark": benchmark,
            "at_minimum": histogram[min(values)],
            "violations": sum(value < benchmark for value in values),
        })
        for optimum, count in sorted(histogram.items()):
            table2.append({"n": n, "optimum": optimum, "classes": count})
    if [row["classes"] for row in table1] != [1, 2, 5, 19, 85, 509, 4060]:
        raise AssertionError("Table 1 census counts do not match the manuscript")
    write_csv(output / "table1_census_summary.csv", table1, list(table1[0]))
    write_csv(output / "table2_optimum_histogram.csv", table2, list(table2[0]))


def tables_3_and_4(output: Path) -> None:
    records = json.loads(COUNTEREXAMPLES.read_text(encoding="utf-8"))["graphs"]
    table3 = [{
        "paper_id": row["paper_id"],
        "optimal_matching": json.dumps(row["optimal_matching"], separators=(",", ":")),
        "diameter": row["diameter"],
        "bridges": row["bridges"],
        "triangles": row["triangles"],
        "c4_count": row["c4_count"],
    } for row in records]
    table4 = [{"paper_id": row["paper_id"], "graph6": row["graph6"]} for row in records]
    write_csv(output / "table3_counterexamples.csv", table3, list(table3[0]))
    write_csv(output / "table4_counterexample_graph6.csv", table4, list(table4[0]))


def table_5(output: Path) -> None:
    rows = read_csv(SUMMARY)
    table: list[dict[str, object]] = []
    totals = {
        "graphs": 0,
        "b_time": 0.0,
        "c_time": 0.0,
        "b_candidates": 0,
        "c_candidates": 0,
        "discrepancies": 0,
    }
    for row in rows:
        record = {
            "n": int(row["n"]),
            "graphs": int(row["graph_count"]),
            "solver_b_time": float(row["total_runtime_solver_b"]),
            "solver_c_time": float(row["total_runtime_solver_c"]),
            "speedup": float(row["total_speedup"]),
            "solver_b_candidates": int(row["total_search_nodes_solver_b"]),
            "solver_c_candidates": int(row["total_search_nodes_solver_c"]),
            "candidate_reduction": float(row["total_node_reduction"]),
            "discrepancies": int(row["discrepancies"]),
        }
        table.append(record)
        totals["graphs"] += record["graphs"]
        totals["b_time"] += record["solver_b_time"]
        totals["c_time"] += record["solver_c_time"]
        totals["b_candidates"] += record["solver_b_candidates"]
        totals["c_candidates"] += record["solver_c_candidates"]
        totals["discrepancies"] += record["discrepancies"]
    table.append({
        "n": "All",
        "graphs": totals["graphs"],
        "solver_b_time": totals["b_time"],
        "solver_c_time": totals["c_time"],
        "speedup": totals["b_time"] / totals["c_time"],
        "solver_b_candidates": totals["b_candidates"],
        "solver_c_candidates": totals["c_candidates"],
        "candidate_reduction": 1 - totals["c_candidates"] / totals["b_candidates"],
        "discrepancies": totals["discrepancies"],
    })
    if totals["graphs"] != 4681 or totals["discrepancies"] != 0:
        raise AssertionError("Table 5 aggregate mismatch")
    write_csv(output / "table5_solver_bc_full_census.csv", table, list(table[0]))


def table_6(output: Path) -> None:
    rows = [
        {"verification_item": "Independent graph generators", "availability": "ORIGINAL_MISSING_NEW_RERUN_COMPLETE", "artifact": "results/post_submission/2026-10-02/generator_audit/; verification/README.md"},
        {"verification_item": "Solver A versus Solver B", "availability": "CODE_AND_TESTS", "artifact": "src/exact_solver.py; tests/"},
        {"verification_item": "Independent endpoint-set optimum audit", "availability": "ORIGINAL_MISSING_NEW_AUDIT_COMPLETE", "artifact": "verification/endpoint_audit.cpp; results/post_submission/2026-10-02/endpoint_audit/"},
        {"verification_item": "Lower-cardinality exclusion", "availability": "NEW_AUDIT_COMPLETE", "artifact": "results/post_submission/2026-10-02/endpoint_audit/n*.jsonl; exhaustive layer counts for 4681 graphs"},
        {"verification_item": "New endpoint auditor independent gate", "availability": "COMPLETE", "artifact": "scripts/run_endpoint_audit.py; 1114 graphs versus Python edge-subset oracle"},
        {"verification_item": "Solver C interaction audit", "availability": "CODE", "artifact": "scripts/publication/audit_solver_c.py"},
        {"verification_item": "Solver B versus Solver C", "availability": "COMPLETE", "artifact": "results/per_graph/full_census.csv"},
        {"verification_item": "Publication package test suite", "availability": "COMPLETE", "artifact": "tests/ (12 tests)"},
    ]
    write_csv(output / "table6_verification_artifact_status.csv", rows, list(rows[0]))


def table_7(output: Path) -> None:
    env = json.loads(ENVIRONMENT.read_text(encoding="utf-8"))
    rows = [
        {"item": "Operating system", "recorded_value": env["operating_system"]},
        {"item": "Processor", "recorded_value": env["processor"]},
        {"item": "Cores", "recorded_value": f"{env['physical_cores']} physical; {env['logical_cores']} logical"},
        {"item": "Memory", "recorded_value": f"{env['ram_gib']} GiB RAM"},
        {"item": "Python", "recorded_value": env["python_version"]},
        {"item": "Graph library", "recorded_value": f"NetworkX {env['networkx_version']}"},
        {"item": "Graph generator", "recorded_value": f"nauty {env['nauty_version']} geng; {env['nauty_generator']}"},
        {"item": "Execution", "recorded_value": f"{env['threading']}; {env['timer']}"},
        {"item": "Benchmark date", "recorded_value": "19 August 2026"},
    ]
    write_csv(output / "table7_publication_environment.csv", rows, list(rows[0]))


def table_8(output: Path) -> None:
    rows = read_csv(EQUALITY)
    table = []
    for row in rows:
        n = int(row["n"])
        optimum = int(row["expected_equality_value"])
        defect = min(optimum - 1, 5 * optimum + 1 - n)
        table.append({
            "n": n,
            "optimum": optimum,
            "defect_budget": defect,
            "solver_b_time": row["runtime_solver_b"] or "timeout",
            "solver_c_time": row["runtime_solver_c"],
            "speedup": row["speedup"] or "censored",
            "status": "B timeout" if row["solver_b_status"] == "timeout" else "both solved",
            "zero_defect": defect == 0,
        })
    if [row["n"] for row in table] != [16, 20, 24, 26, 28, 32, 36, 46, 56]:
        raise AssertionError("Table 8 order list mismatch")
    write_csv(output / "table8_equality_scaling.csv", table, list(table[0]))


def main() -> None:
    output = ROOT / "results" / "tables"
    tables_1_and_2(output)
    tables_3_and_4(output)
    table_5(output)
    table_6(output)
    table_7(output)
    table_8(output)


if __name__ == "__main__":
    main()
