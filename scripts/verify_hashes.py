#!/usr/bin/env python3
"""Verify SHA-256 manifests without modifying the repository."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from _repo import ROOT


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def verify(manifest_path: Path) -> int:
    checked = 0
    for line_number, line in enumerate(manifest_path.read_text(encoding="ascii").splitlines(), 1):
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        target = ROOT / Path(relative)
        if not target.is_file():
            raise AssertionError(f"{manifest_path.name}:{line_number}: missing {relative}")
        actual = digest(target)
        if actual != expected:
            raise AssertionError(
                f"{manifest_path.name}:{line_number}: {relative}: expected {expected}, found {actual}"
            )
        checked += 1
    print(f"{manifest_path.name}: {checked} files PASS")
    return checked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifests", nargs="*", type=Path,
        default=[ROOT / "PUBLICATION_SHA256SUMS.txt", ROOT / "SHA256SUMS.txt"],
    )
    args = parser.parse_args()
    for path in args.manifests:
        verify(path if path.is_absolute() else ROOT / path)


if __name__ == "__main__":
    main()

