#!/usr/bin/env python3
"""Regenerate release-cleanup and frozen-publication SHA-256 manifests."""

from __future__ import annotations

import hashlib
from pathlib import Path

from _repo import ROOT

EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache"}
EXCLUDED_NAMES = {"SHA256SUMS.txt", "PUBLICATION_SHA256SUMS.txt"}
PUBLICATION_FILES = [
    "src/acyclic_matching.py",
    "src/exact_solver.py",
    "src/solver_c.py",
    "data/census/canonical/connected_cubic_n4.g6",
    "data/census/canonical/connected_cubic_n6.g6",
    "data/census/canonical/connected_cubic_n8.g6",
    "data/census/canonical/connected_cubic_n10.g6",
    "data/census/canonical/connected_cubic_n12.g6",
    "data/census/canonical/connected_cubic_n14.g6",
    "data/census/canonical/connected_cubic_n16.g6",
    "paper/Minimum_Maximal_Acyclic_Matchings_JCO_smallextended_source.pdf",
    "paper/main_jco.tex",
    "results/per_graph/full_census.csv",
]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def manifest(paths: list[Path]) -> str:
    return "".join(f"{digest(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in paths)


def main() -> None:
    all_files = sorted(
        path for path in ROOT.rglob("*")
        if path.is_file()
        and path.name not in EXCLUDED_NAMES
        and not EXCLUDED_PARTS.intersection(path.relative_to(ROOT).parts)
    )
    (ROOT / "SHA256SUMS.txt").write_text(manifest(all_files), encoding="ascii", newline="\n")
    publication_paths = [ROOT / relative for relative in PUBLICATION_FILES]
    (ROOT / "PUBLICATION_SHA256SUMS.txt").write_text(
        manifest(publication_paths), encoding="ascii", newline="\n"
    )
    print(f"wrote {len(all_files)} release hashes and {len(publication_paths)} publication hashes")


if __name__ == "__main__":
    main()

