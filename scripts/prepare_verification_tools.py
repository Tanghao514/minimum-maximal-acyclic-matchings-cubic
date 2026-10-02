#!/usr/bin/env python3
"""Download hash-pinned external generators and build locally on Linux/WSL.

External source/binaries are not committed to this repository. Default operation
downloads and builds; --download-only and --build-only support Windows + WSL.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tarfile
import urllib.request

GENREG = {
    "gendef.h": "8cf36cf5d0d0a550c1c2c749945036705b850a4213e56b52a04fb3e2ce6fc893",
    "genreg.c": "5831e836d010ceef51ef8e3ae69c2476dfde838b89e66b2a509ec692739a06fd",
    "main.c": "45ab087ef5be42055353d0f0e552313f46f143f5b87e7b208c44025ec53d5516",
    "makefile": "0360d71e48c0bc6bc15cc414fad8380e5699e3964828108d70286a1077b70e88",
    "optmid.c": "5671e82f319d9c398e94460297c20570ab3f302b81631766b1e7b25c5048efbb",
    "readscd.c": "01b2edb6f8a6bc6cc83c961e6082fe58efc2fe2219c08ee90e5a6ff154049631",
    "manual.eng.tex": "e75a7109328f7ee240998786f9cf38e7e592bf7c667f901bd9f1996b37c6c105",
}
NAUTY_URL = "https://users.cecs.anu.edu.au/~bdm/nauty/nauty2_9_3.tar.gz"
NAUTY_SHA256 = "9fc4edae04f88a0f5883985be3b39cf7f898fd6cc96e96b9ee25452743cc1b5b"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def obtain(url: str, path: Path, expected: str, build_only: bool) -> dict:
    if not path.exists():
        if build_only:
            raise FileNotFoundError(path)
        request = urllib.request.Request(url, headers={"User-Agent": "MMAM-reproducibility/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"download hash mismatch: {url}")
        path.write_bytes(data)
    if digest(path) != expected:
        raise ValueError(f"existing source hash mismatch: {path.name}")
    return {"name": path.name, "url": url, "sha256": expected}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--download-only", action="store_true")
    mode.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    genreg = root / "genreg"
    genreg.mkdir(exist_ok=True)
    sources = []
    for name, expected in GENREG.items():
        url = f"https://svn.code.sf.net/p/genreg/code/trunk/{name}?p=1"
        sources.append(obtain(url, genreg / name, expected, args.build_only))
    archive = root / "nauty2_9_3.tar.gz"
    sources.append(obtain(NAUTY_URL, archive, NAUTY_SHA256, args.build_only))
    manifest = {"kind": "post_submission_external_toolchain", "recorded_utc": datetime.now(timezone.utc).isoformat(),
                "genreg": "hash-pinned GENREG original trunk files (upstream last file change r1, 2015-06-21)",
                "nauty": "2.9.3", "sources": sources,
                "note": "These are new downloads/builds, not recovered publication tools."}
    if not args.download_only:
        nauty = root / "nauty2_9_3"
        if nauty.exists():
            raise FileExistsError("choose a fresh build directory; nauty source directory already exists")
        with tarfile.open(archive, "r:gz") as stream:
            members = stream.getmembers()
            for member in members:
                path = (root / member.name).resolve()
                if not path.is_relative_to(root) or member.issym() or member.islnk():
                    raise ValueError("unexpected archive path or link")
            stream.extractall(root)
        commands = [(genreg, ["make"]),
                    (nauty, ["./configure", "CFLAGS=-O2"]),
                    (nauty, ["make", "geng", "labelg"])]
        manifest["platform"] = platform.platform()
        manifest["compiler"] = subprocess.run(["cc", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
        manifest["build_commands"] = []
        for index, (cwd, command) in enumerate(commands):
            log = root / f"build_{index + 1}.txt"
            with log.open("wb") as stream:
                result = subprocess.run(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT)
            result.check_returncode()
            manifest["build_commands"].append({"cwd": cwd.name, "argv": command,
                                                "output_file": log.name, "output_sha256": digest(log)})
        manifest["executables_sha256"] = {
            "genreg": digest(genreg / "genreg"), "geng": digest(nauty / "geng"), "labelg": digest(nauty / "labelg")}
        print("GENREG, geng, labelg built successfully.")
    (root / "toolchain.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Toolchain manifest: {root / 'toolchain.json'}")


if __name__ == "__main__":
    main()
