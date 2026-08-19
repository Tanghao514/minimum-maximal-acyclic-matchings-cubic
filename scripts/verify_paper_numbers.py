#!/usr/bin/env python3
"""Cross-check the paper's numerical claims against preserved artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from _repo import ROOT


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    value.update(path.read_bytes())
    return value.hexdigest()


def main() -> None:
    failures: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    per_graph = rows(ROOT / "results" / "per_graph" / "full_census.csv")
    check(len(per_graph) == 4681, f"per-graph rows: expected 4681, found {len(per_graph)}")
    grouped: dict[int, list[int]] = defaultdict(list)
    discrepancies = 0
    for row in per_graph:
        b, c = int(row["mu_solver_b"]), int(row["mu_solver_c"])
        grouped[int(row["n"])].append(b)
        discrepancies += b != c
    check([len(grouped[n]) for n in sorted(grouped)] == [1, 2, 5, 19, 85, 509, 4060], "census counts")
    check(Counter(grouped[14]) == Counter({3: 418, 4: 91}), "order-14 histogram")
    check(Counter(grouped[16]) == Counter({3: 4, 4: 4056}), "order-16 histogram")
    check(discrepancies == 0, f"Solver B/C discrepancies: {discrepancies}")

    summary = rows(ROOT / "results" / "benchmarks" / "processed" / "solver_bc_census_summary.csv")
    expected = {
        4: (0.0008, 0.0010, 2, 1),
        6: (0.0053, 0.0040, 5, 2),
        8: (0.0127, 0.0126, 70, 5),
        10: (0.0839, 0.0896, 989, 358),
        12: (0.4467, 0.3775, 11151, 179),
        14: (5.9727, 4.8901, 224027, 43691),
        16: (94.1762, 32.4600, 4832310, 40158),
    }
    for row in summary:
        n = int(row["n"])
        b_time, c_time, b_nodes, c_nodes = expected[n]
        check(abs(float(row["total_runtime_solver_b"]) - b_time) < 0.000051, f"Table 5 B time n={n}")
        check(abs(float(row["total_runtime_solver_c"]) - c_time) < 0.000051, f"Table 5 C time n={n}")
        check(int(row["total_search_nodes_solver_b"]) == b_nodes, f"Table 5 B candidates n={n}")
        check(int(row["total_search_nodes_solver_c"]) == c_nodes, f"Table 5 C candidates n={n}")
    total_b = sum(float(row["total_runtime_solver_b"]) for row in summary)
    total_c = sum(float(row["total_runtime_solver_c"]) for row in summary)
    check(abs(total_b - 100.6984) < 0.000051, "Table 5 all-orders Solver B time")
    check(abs(total_c - 37.8348) < 0.000051, "Table 5 all-orders Solver C time")
    check(sum(int(row["total_search_nodes_solver_b"]) for row in summary) == 5068554, "Table 5 all B candidates")
    check(sum(int(row["total_search_nodes_solver_c"]) for row in summary) == 84394, "Table 5 all C candidates")

    equality = rows(ROOT / "results" / "benchmarks" / "raw" / "solver_bc_equality_family.csv")
    check([int(row["n"]) for row in equality] == [16, 20, 24, 26, 28, 32, 36, 46, 56], "Table 8 orders")
    check([row["solver_b_status"] for row in equality[-2:]] == ["timeout", "timeout"], "Table 8 B timeouts")
    check(all(row["solver_c_status"] == "solved" for row in equality), "Table 8 Solver C statuses")

    ablation = rows(ROOT / "results" / "ablations" / "solver_c_ablation_complete.csv")
    check(len(ablation) == 500, f"ablation rows: expected 500, found {len(ablation)}")
    zero = [row for row in ablation if int(row["defect_budget"]) == 0]
    defect_five = [row for row in ablation if int(row["defect_budget"]) == 5]
    by_variant_zero: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in zero:
        by_variant_zero[row["variant"]].append(row)
    full_time = statistics.median(float(row["runtime_seconds"]) for row in by_variant_zero["c_full"])
    generic_time = statistics.median(float(row["runtime_seconds"]) for row in by_variant_zero["c_without_zero_defect_special_solver"])
    no_budget_time = statistics.median(float(row["runtime_seconds"]) for row in by_variant_zero["c_without_defect_budget"])
    check(math.isclose(generic_time / full_time, 9.7, rel_tol=0.06), "ablation ~9.7x")
    check(math.isclose(no_budget_time / full_time, 15.2, rel_tol=0.06), "ablation ~15.2x")
    full_nodes = sum(int(row["search_nodes"]) for row in defect_five if row["variant"] == "c_full")
    no_leaf_nodes = sum(int(row["search_nodes"]) for row in defect_five if row["variant"] == "c_without_near_leaf_maximality_pruning")
    check((full_nodes, no_leaf_nodes) == (1853, 3268), f"ablation nodes: {(full_nodes, no_leaf_nodes)}")

    env = json.loads((ROOT / "results" / "benchmarks" / "publication_environment.json").read_text(encoding="utf-8"))
    for relative, expected_hash in env["source_sha256"].items():
        normalized = relative.replace("\\", "/")
        check(sha256(ROOT / normalized) == expected_hash, f"publication source hash {normalized}")
    for name, expected_hash in env["census_sha256"].items():
        check(sha256(ROOT / "data" / "census" / "canonical" / name) == expected_hash, f"census hash {name}")
    check(
        sha256(ROOT / "paper" / "Minimum_Maximal_Acyclic_Matchings_JCO_smallextended_source.pdf")
        == "80d26c7699bc75c7d26a5dce7b6c835fe120d13c9a60d0e030bdb250fd03d48a",
        "final manuscript PDF hash",
    )

    mismatch = ROOT / "RESULT_MISMATCH_REPORT.md"
    if failures:
        mismatch.write_text(
            "# Result mismatch report\n\n" + "".join(f"- {failure}\n" for failure in failures),
            encoding="utf-8",
        )
        raise SystemExit(f"{len(failures)} mismatch(es); see {mismatch.name}")
    if mismatch.exists():
        mismatch.unlink()
    print("PAPER NUMBERS VERIFIED")


if __name__ == "__main__":
    main()

