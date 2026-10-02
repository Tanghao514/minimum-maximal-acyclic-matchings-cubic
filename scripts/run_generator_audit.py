#!/usr/bin/env python3
"""NEW dual-generator rerun with raw outputs and exact canonical-multiset checks.

External tools must be supplied explicitly. No publication files are overwritten.
GENREG ASCII adjacency lists are decoded here; labelg canonicalizes GENREG,
fresh geng output, and the preserved publication census using identical options.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
COUNTS = {4: 1, 6: 2, 8: 5, 10: 19, 12: 85, 14: 509, 16: 4060}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def encode(adjacency: list[set[int]]) -> str:
    n = len(adjacency)
    bits = [int(u in adjacency[v]) for v in range(n) for u in range(v)]
    bits += [0] * ((-len(bits)) % 6)
    return chr(n + 63) + "".join(chr(63 + int("".join(map(str, bits[i:i + 6])), 2))
                                for i in range(0, len(bits), 6))


def parse_genreg_ascii(text: str, n: int) -> list[str]:
    # Only the n adjacency rows immediately following each Graph header are read.
    # Automorphism rows also contain colons, so a global colon-line parser is unsafe.
    blocks = re.split(r"(?m)^Graph\s+(\d+):\s*$", text)
    if len(blocks) < 3 or blocks[0].strip():
        raise ValueError("unexpected GENREG ASCII header")
    graphs = []
    for index in range(1, len(blocks), 2):
        number = int(blocks[index])
        if number != len(graphs) + 1:
            raise ValueError("GENREG graph numbering is not consecutive")
        lines = [line.strip() for line in blocks[index + 1].splitlines() if line.strip()]
        adjacency = []
        for u, line in enumerate(lines[:n]):
            match = re.fullmatch(r"(\d+)\s*:\s*([\d\s]+)", line)
            if match is None or int(match[1]) != u + 1:
                raise ValueError(f"bad adjacency row in GENREG graph {number}")
            neighbors = [int(v) - 1 for v in match[2].split()]
            if len(neighbors) != 3 or len(set(neighbors)) != 3 or u in neighbors:
                raise ValueError("GENREG output is not simple cubic")
            if any(v < 0 or v >= n for v in neighbors):
                raise ValueError("neighbor out of range")
            adjacency.append(set(neighbors))
        if len(adjacency) != n or any(u not in adjacency[v] for u in range(n) for v in adjacency[u]):
            raise ValueError("nonreciprocal adjacency")
        seen = {0}
        todo = [0]
        while todo:
            for v in adjacency[todo.pop()]:
                if v not in seen:
                    seen.add(v)
                    todo.append(v)
        if len(seen) != n:
            raise ValueError("disconnected GENREG output")
        graphs.append(encode(adjacency))
    return graphs


def execute(command: list[str], stdout: Path, stderr: Path, cwd: Path) -> float:
    start = time.perf_counter()
    with stdout.open("wb") as out, stderr.open("wb") as err:
        result = subprocess.run(command, stdout=out, stderr=err, cwd=cwd)
    result.check_returncode()
    return time.perf_counter() - start


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--genreg", type=Path, required=True)
    parser.add_argument("--geng", type=Path, required=True)
    parser.add_argument("--labelg", type=Path, required=True)
    parser.add_argument("--toolchain-manifest", type=Path, required=True,
                        help="JSON with actual external source URLs/hashes and build commands")
    parser.add_argument("--output", type=Path, default=ROOT / "reproduced" / "generator_audit")
    args = parser.parse_args()
    for name in ("genreg", "geng", "labelg", "toolchain_manifest"):
        path = getattr(args, name).resolve()
        if not path.is_file():
            parser.error(f"missing {name}: {path}")
        setattr(args, name, path)
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    toolchain = json.loads(args.toolchain_manifest.read_text(encoding="utf-8"))
    (args.output / "toolchain.json").write_text(json.dumps(toolchain, indent=2) + "\n", encoding="utf-8")
    report = {"kind": "new_post_submission_verification", "status": "running",
              "started_utc": utc(), "platform": platform.platform(),
              "python": platform.python_version(), "runner_sha256": sha256(Path(__file__)),
              "toolchain_manifest_sha256": sha256(args.toolchain_manifest),
              "executables_sha256": {name: sha256(getattr(args, name)) for name in ("genreg", "geng", "labelg")},
              "canonicalizer_shared_between_generators": True, "orders": []}
    try:
        for n, expected in COUNTS.items():
            prefix = args.output / f"n{n}"
            raw = prefix.with_suffix(".genreg.asc")
            genreg_seconds = execute([str(args.genreg), str(n), "3", "-a", "stdout"], raw,
                                     prefix.with_suffix(".genreg.stderr.txt"), args.output)
            codes = parse_genreg_ascii(raw.read_text(encoding="ascii"), n)
            genreg_g6 = prefix.with_suffix(".genreg.g6")
            genreg_g6.write_text("\n".join(codes) + "\n", encoding="ascii", newline="\n")
            geng_g6 = prefix.with_suffix(".geng.g6")
            geng_seconds = execute([str(args.geng), "-c", "-q", "-d3", "-D3", str(n), str(3 * n // 2)],
                                   geng_g6, prefix.with_suffix(".geng.stderr.txt"), args.output)
            publication = ROOT / "data" / "census" / "canonical" / f"connected_cubic_n{n}.g6"
            canonical = {}
            for name, source in (("genreg", genreg_g6), ("geng", geng_g6), ("publication", publication)):
                output = prefix.with_suffix(f".{name}.canonical.g6")
                execute([str(args.labelg), "-q", "-g", str(source)], output,
                        prefix.with_suffix(f".{name}.labelg.stderr.txt"), args.output)
                canonical[name] = output.read_text(encoding="ascii").splitlines()
                if len(canonical[name]) != expected or len(set(canonical[name])) != expected:
                    raise AssertionError(f"{name} count or isomorphism duplication at n={n}")
            if not Counter(canonical["genreg"]) == Counter(canonical["geng"]) == Counter(canonical["publication"]):
                raise AssertionError(f"canonical multisets differ at n={n}")
            # Keep the bijection as well as a set comparison, with original row indices.
            indices = {name: {code: i for i, code in enumerate(lines)} for name, lines in canonical.items()}
            mapping = prefix.with_suffix(".bijection.csv")
            with mapping.open("w", encoding="ascii", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["canonical_graph6", "genreg_index", "geng_index", "publication_index"])
                writer.writerows([code, *(indices[name][code] for name in ("genreg", "geng", "publication"))]
                                 for code in sorted(canonical["genreg"]))
            result = {"n": n, "graphs": expected, "all_three_canonical_multisets_equal": True,
                      "duplicates": 0, "genreg_seconds": genreg_seconds, "geng_seconds": geng_seconds,
                      "publication_input_sha256": sha256(publication),
                      "commands": [["genreg", str(n), "3", "-a", "stdout"],
                                   ["geng", "-c", "-q", "-d3", "-D3", str(n), str(3 * n // 2)],
                                   ["labelg", "-q", "-g", "<each of the three inputs>"]],
                      "artifacts_sha256": {p.name: sha256(p) for p in sorted(args.output.glob(f"n{n}.*"))}}
            report["orders"].append(result)
            print(f"n={n}: GENREG = fresh geng = publication census; {expected} classes PASS", flush=True)
        report["status"] = "pass"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)
        raise
    finally:
        report["finished_utc"] = utc()
        (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("DUAL-GENERATOR AUDIT PASSED", flush=True)


if __name__ == "__main__":
    main()
