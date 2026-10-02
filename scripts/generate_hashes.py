#!/usr/bin/env python3
"""Refresh the repository manifest after verifying the unchanged publication core."""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

from _repo import ROOT

EXCLUDED_NAMES = {"SHA256SUMS.txt", "PUBLICATION_SHA256SUMS.txt"}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def manifest(paths: list[Path]) -> str:
    return "".join(f"{digest(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in paths)


def main() -> None:
    frozen = ROOT / "PUBLICATION_SHA256SUMS.txt"
    for line in frozen.read_text(encoding="ascii").splitlines():
        expected, relative = line.split("  ", 1)
        if digest(ROOT / relative) != expected:
            raise AssertionError(f"Frozen publication file changed: {relative}")
    # Respect .gitignore, including fresh reruns, toolchains, caches and virtualenvs.
    names = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout.decode("utf-8").split("\0")
    all_files = sorted({ROOT / name for name in names if name and (ROOT / name).is_file()
                        and Path(name).name not in EXCLUDED_NAMES})
    (ROOT / "SHA256SUMS.txt").write_text(manifest(all_files), encoding="ascii", newline="\n")
    print(f"wrote {len(all_files)} repository hashes; publication manifest verified and unchanged")


if __name__ == "__main__":
    main()
