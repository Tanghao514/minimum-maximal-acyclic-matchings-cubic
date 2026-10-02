#!/usr/bin/env python3
"""Check the archived NEW verification records (does not rerun exhaustive search)."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path

from run_endpoint_audit import COUNTS, ROOT, sha256, validate_record
from run_generator_audit import parse_genreg_ascii


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path,
                        default=ROOT / "results" / "post_submission" / "2026-10-02")
    args = parser.parse_args()
    endpoint = args.results_dir / "endpoint_audit"
    summary = json.loads((endpoint / "summary.json").read_text(encoding="utf-8"))
    if summary["kind"] != "new_post_submission_verification" or summary["status"] != "pass":
        raise AssertionError("endpoint audit did not complete")
    if summary["theorem_pruning"] or summary["search_starts_at_k"] != 0:
        raise AssertionError("endpoint audit independence metadata")
    if summary["source_sha256"] != sha256(ROOT / summary["source"]):
        raise AssertionError("endpoint audit source changed since run")
    if summary["runner_sha256"] != sha256(ROOT / "scripts" / "run_endpoint_audit.py"):
        raise AssertionError("endpoint runner changed since run")
    if summary["gate"]["status"] != "pass" or summary["gate"]["graphs"] != 1114:
        raise AssertionError("independent gate")
    if [r["n"] for r in summary["orders"]] != list(COUNTS):
        raise AssertionError("incomplete endpoint audit orders")
    with (ROOT / "results" / "per_graph" / "full_census.csv").open(encoding="utf-8-sig", newline="") as stream:
        reference = {row["graph6"]: int(row["mu_solver_b"]) for row in csv.DictReader(stream)}
    for layer in summary["orders"]:
        n = layer["n"]
        source = ROOT / "data" / "census" / "canonical" / f"connected_cubic_n{n}.g6"
        output = endpoint / f"n{n}.jsonl"
        if sha256(source) != layer["input_sha256"] or sha256(output) != layer["output_sha256"]:
            raise AssertionError(f"endpoint input/output hash mismatch at n={n}")
        codes = source.read_text(encoding="ascii").splitlines()
        records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
        if len(records) != COUNTS[n] or layer["graphs"] != COUNTS[n]:
            raise AssertionError("endpoint graph count")
        for i, (record, code) in enumerate(zip(records, codes)):
            validate_record(record, code, i)
            if record["mu"] != reference[code]:
                raise AssertionError("endpoint optimum mismatch")
        observed = {str(k): v for k, v in Counter(r["mu"] for r in records).items()}
        if observed != layer["histogram"] or layer["discrepancies"] != 0:
            raise AssertionError("endpoint histogram/summary mismatch")
        count = sum(l["tested"] for r in records for l in r["layers"])
        if count != layer["tested_endpoint_sets"]:
            raise AssertionError("endpoint enumeration count")
    print("Archived endpoint audit: 4681 witnesses, lower-layer counts, optima and hashes PASS")

    generators = args.results_dir / "generator_audit"
    summary = json.loads((generators / "summary.json").read_text(encoding="utf-8"))
    if summary["kind"] != "new_post_submission_verification" or summary["status"] != "pass":
        raise AssertionError("generator audit did not complete")
    if summary["runner_sha256"] != sha256(ROOT / "scripts" / "run_generator_audit.py"):
        raise AssertionError("generator runner changed since run")
    toolchain = json.loads((generators / "toolchain.json").read_text(encoding="utf-8"))
    if sha256(generators / "toolchain.json") != summary["toolchain_manifest_sha256"]:
        raise AssertionError("toolchain manifest hash mismatch")
    if toolchain["executables_sha256"] != summary["executables_sha256"]:
        raise AssertionError("generator binaries differ from recorded builds")
    if [r["n"] for r in summary["orders"]] != list(COUNTS):
        raise AssertionError("incomplete generator audit orders")
    for layer in summary["orders"]:
        n = layer["n"]
        for name, digest in layer["artifacts_sha256"].items():
            if sha256(generators / name) != digest:
                raise AssertionError(f"generator artifact hash mismatch: {name}")
        raw = (generators / f"n{n}.genreg.asc").read_text(encoding="ascii")
        converted = (generators / f"n{n}.genreg.g6").read_text(encoding="ascii").splitlines()
        if parse_genreg_ascii(raw, n) != converted:
            raise AssertionError("GENREG ASCII conversion changed")
        canonical = {name: (generators / f"n{n}.{name}.canonical.g6").read_text(encoding="ascii").splitlines()
                     for name in ("genreg", "geng", "publication")}
        if any(len(lines) != COUNTS[n] or len(set(lines)) != COUNTS[n] for lines in canonical.values()):
            raise AssertionError("generator count/duplicate")
        if not Counter(canonical["genreg"]) == Counter(canonical["geng"]) == Counter(canonical["publication"]):
            raise AssertionError("canonical multiset mismatch")
        with (generators / f"n{n}.bijection.csv").open(encoding="ascii", newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != COUNTS[n] or len({r["canonical_graph6"] for r in rows}) != COUNTS[n]:
            raise AssertionError("bijection row count")
        for row in rows:
            for name in canonical:
                if canonical[name][int(row[f"{name}_index"]) ] != row["canonical_graph6"]:
                    raise AssertionError("incorrect generator bijection")
    print("Archived dual-generator audit: all seven orders and 4681 class bijections PASS")
    print("POST-SUBMISSION RECORD CHECKS PASSED (rerun commands are in verification/README.md)")


if __name__ == "__main__":
    main()
