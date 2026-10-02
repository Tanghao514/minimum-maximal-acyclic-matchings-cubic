#!/usr/bin/env python3
"""Run a NEW, theorem-independent endpoint-set audit; never overwrite paper results.

Uses only the Python standard library and a C++17 compiler. The C++ process sees
only graph6 inputs. Publication optima are loaded AFTER its output is complete.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
from itertools import combinations
import json
from math import comb
from pathlib import Path
import platform
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "verification" / "endpoint_audit.cpp"
COUNTS = {4: 1, 6: 2, 8: 5, 10: 19, 12: 85, 14: 509, 16: 4060}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def encode(n: int, edges: list[tuple[int, int]]) -> str:
    edge_set = {frozenset(e) for e in edges}
    bits = [int(frozenset((u, v)) in edge_set) for v in range(n) for u in range(v)]
    bits += [0] * ((-len(bits)) % 6)
    return chr(63 + n) + "".join(
        chr(63 + sum(bits[i + j] << (5 - j) for j in range(6)))
        for i in range(0, len(bits), 6)
    )


def decode(code: str) -> tuple[int, list[tuple[int, int]]]:
    # Independent Python parser, used for comparison/witness checks, not search.
    n = ord(code[0]) - 63
    bits = [(ord(ch) - 63) >> shift & 1 for ch in code[1:] for shift in range(5, -1, -1)]
    pairs = [(u, v) for v in range(n) for u in range(v)]
    return n, [e for e, bit in zip(pairs, bits) if bit]


def forest(vertices: set[int], edges: list[tuple[int, int]]) -> bool:
    # BFS component edge counts, deliberately distinct from the C++ union-find.
    adj = {v: set() for v in vertices}
    for u, v in edges:
        if u in vertices and v in vertices:
            adj[u].add(v)
            adj[v].add(u)
    unseen = set(vertices)
    while unseen:
        todo = [unseen.pop()]
        degree_sum = 0
        count = 0
        while todo:
            u = todo.pop()
            count += 1
            degree_sum += len(adj[u])
            for v in adj[u]:
                if v in unseen:
                    unseen.remove(v)
                    todo.append(v)
        if degree_sum != 2 * (count - 1):
            return False
    return True


def valid_witness(n: int, edges: list[tuple[int, int]], matching: list[list[int]]) -> bool:
    vertices = {v for e in matching for v in e}
    if len(vertices) != 2 * len(matching) or not vertices <= set(range(n)):
        return False
    edge_set = {frozenset(e) for e in edges}
    if any(frozenset(e) not in edge_set for e in matching) or not forest(vertices, edges):
        return False
    return all(not forest(vertices | {u, v}, edges)
               for u, v in edges if u not in vertices and v not in vertices)


def brute_optimum(n: int, edges: list[tuple[int, int]]) -> int:
    # Edge-subset enumeration for the small test gate. No project solver imports.
    for k in range(n // 2 + 1):
        for chosen in combinations(edges, k):
            if valid_witness(n, edges, list(chosen)):
                return k
    raise AssertionError("no solution")


def validate_record(record: dict, code: str, index: int) -> None:
    n, edges = decode(code)
    if record["graph6"] != code or record["index"] != index or record["n"] != n:
        raise AssertionError("record/input alignment mismatch")
    k = record["mu"]
    if len(record["matching"]) != k or not valid_witness(n, edges, record["matching"]):
        raise AssertionError(f"invalid witness at input {index}")
    mask = sum(1 << v for e in record["matching"] for v in e)
    if mask != record["endpoint_mask"]:
        raise AssertionError("endpoint mask mismatch")
    if [layer["k"] for layer in record["layers"]] != list(range(k + 1)):
        raise AssertionError("missing cardinality layer")
    for layer in record["layers"]:
        count = comb(n, 2 * layer["k"])
        if layer["k"] < k and layer["tested"] != count:
            raise AssertionError("smaller endpoint cardinality not exhausted")
        if not 0 <= layer["perfect"] <= layer["forests"] <= layer["tested"] <= count:
            raise AssertionError("inconsistent search counts")
    if record["layers"][-1]["perfect"] < 1:
        raise AssertionError("no accepted perfect matching")


def gate(executable: Path, folder: Path) -> dict:
    start = time.perf_counter()
    cases = []
    # All 1,100 LABELED simple graphs of orders 0..5 (includes disconnected graphs).
    for n in range(6):
        possible = list(combinations(range(n), 2))
        for mask in range(1 << len(possible)):
            edges = [e for j, e in enumerate(possible) if mask >> j & 1]
            cases.append((n, edges))
    # Larger cycles exercise cycle detection beyond pairwise conflicts.
    for n in (6, 7, 8, 9, 10):
        cases.append((n, [(i, (i + 1) % n) for i in range(n)]))
        cases.append((n, [(i, i + 1) for i in range(n - 1)]))
    # Cubic and dense graphs, plus a 6-cycle whose alternating edges form a cycle.
    cases.extend([
        (6, [(u, v) for u in range(3) for v in range(3, 6)]),
        (6, list(combinations(range(6), 2))),
        (8, [(u, u ^ (1 << b)) for u in range(8) for b in range(3) if u < (u ^ (1 << b))]),
        (10, [(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)]
         + [(5 + i, 5 + (i + 2) % 5) for i in range(5)]),
    ])
    codes = [encode(n, edges) for n, edges in cases]
    inputs = folder / "gate.g6"
    inputs.write_text("\n".join(codes) + "\n", encoding="ascii")
    output = subprocess.run([str(executable), str(inputs)], text=True, capture_output=True, check=True)
    records = [json.loads(line) for line in output.stdout.splitlines()]
    if len(records) != len(cases):
        raise AssertionError("gate record count")
    for i, ((n, edges), code, record) in enumerate(zip(cases, codes, records)):
        validate_record(record, code, i)
        expected = brute_optimum(n, edges)
        if record["mu"] != expected:
            raise AssertionError(f"gate optimum mismatch at {i}: {record['mu']} != {expected}")
    # Corrupt encodings must fail instead of silently changing the graph.
    for bad in ("", "C", "C~?", "A@", "!", "~???"):
        inputs.write_text(bad + "\n", encoding="ascii")
        result = subprocess.run([str(executable), str(inputs)], capture_output=True)
        if result.returncode == 0:
            raise AssertionError(f"malformed graph6 accepted: {bad!r}")
    # Both allowed header forms and CRLF parsing.
    for encoded in (">>graph6<<\nC~\n", ">>graph6<<C~\r\n"):
        inputs.write_bytes(encoded.encode("ascii"))
        result = subprocess.run([str(executable), str(inputs)], capture_output=True, text=True, check=True)
        if json.loads(result.stdout)["mu"] != 1:
            raise AssertionError("header parsing")
    return {"status": "pass", "graphs": len(cases), "all_labeled_orders_0_to_5": 1100,
            "additional_graphs": len(cases) - 1100, "malformed_inputs_rejected": 6,
            "reference": "independent Python edge-subset enumeration and BFS forest check",
            "seconds": time.perf_counter() - start}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reproduced" / "endpoint_audit")
    parser.add_argument("--orders", type=int, nargs="+", default=list(COUNTS))
    parser.add_argument("--compiler", default="g++")
    parser.add_argument("--gate-only", action="store_true")
    args = parser.parse_args()
    if any(n not in COUNTS for n in args.orders) or len(set(args.orders)) != len(args.orders):
        parser.error("choose distinct orders from 4,6,8,10,12,14,16")
    # Existing results are immutable by default. Choose a fresh directory for each run.
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"kind": "new_post_submission_verification", "started_utc": utc(),
              "status": "running", "source": "verification/endpoint_audit.cpp",
              "source_sha256": sha256(SOURCE), "runner_sha256": sha256(Path(__file__)),
              "theorem_pruning": False, "search_starts_at_k": 0,
              "platform": platform.platform(), "python": platform.python_version(), "orders": []}
    summary = args.output / "summary.json"
    try:
        with tempfile.TemporaryDirectory(prefix="endpoint_audit_") as temporary:
            folder = Path(temporary)
            executable = folder / ("endpoint_audit.exe" if platform.system() == "Windows" else "endpoint_audit")
            options = ["-std=c++17", "-O2", "-Wall", "-Wextra", "-pedantic"]
            report["compiler"] = subprocess.run([args.compiler, "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
            report["build_command"] = [args.compiler, *options, "verification/endpoint_audit.cpp", "-o", "<temporary>/endpoint_audit"]
            built = subprocess.run([args.compiler, *options, str(SOURCE), "-o", str(executable)], capture_output=True, text=True)
            (args.output / "build.txt").write_text(built.stdout + built.stderr, encoding="utf-8")
            built.check_returncode()
            report["executable_sha256"] = sha256(executable)
            report["gate"] = gate(executable, folder)
            print(f"Independent gate: {report['gate']['graphs']} graphs PASS", flush=True)
            if not args.gate_only:
                for n in args.orders:
                    source = ROOT / "data" / "census" / "canonical" / f"connected_cubic_n{n}.g6"
                    output = args.output / f"n{n}.jsonl"
                    start = time.perf_counter()
                    with output.open("wb") as stream:
                        completed = subprocess.run([str(executable), str(source)], stdout=stream, stderr=subprocess.PIPE)
                    (args.output / f"n{n}.stderr.txt").write_bytes(completed.stderr)
                    completed.check_returncode()
                    wall_seconds = time.perf_counter() - start
                    codes = source.read_text(encoding="ascii").splitlines()
                    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
                    if len(records) != COUNTS[n] or len(codes) != len(records):
                        raise AssertionError(f"wrong graph count at n={n}")
                    # Load publication answers only after the independent process has exited.
                    with (ROOT / "results" / "per_graph" / "full_census.csv").open(encoding="utf-8-sig", newline="") as stream:
                        reference = {row["graph6"]: int(row["mu_solver_b"]) for row in csv.DictReader(stream) if int(row["n"]) == n}
                    if set(reference) != set(codes):
                        raise AssertionError("publication input alignment")
                    for i, (code, record) in enumerate(zip(codes, records)):
                        validate_record(record, code, i)
                        if record["mu"] != reference[code]:
                            raise AssertionError(f"optimum differs from publication at n={n}, index={i}")
                    result = {"n": n, "graphs": len(records), "histogram": dict(sorted(Counter(r["mu"] for r in records).items())),
                              "input_sha256": sha256(source), "output_sha256": sha256(output),
                              "discrepancies": 0, "all_smaller_cardinalities_exhausted": True,
                              "wall_seconds": wall_seconds,
                              "tested_endpoint_sets": sum(l["tested"] for r in records for l in r["layers"])}
                    report["orders"].append(result)
                    print(f"n={n}: {len(records)} optima agree; histogram={result['histogram']}; {wall_seconds:.2f}s", flush=True)
                    summary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            report["status"] = "pass"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)
        raise
    finally:
        report["finished_utc"] = utc()
        summary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("ENDPOINT AUDIT PASSED", flush=True)


if __name__ == "__main__":
    main()
