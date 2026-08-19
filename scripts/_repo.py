"""Small path and graph6 helpers shared by the reviewer-facing scripts."""

from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def decode_graph6(text: str) -> nx.Graph:
    """Decode one graph6 record, accepting an optional graph6 header."""
    value = text.strip()
    if not value:
        raise ValueError("empty graph6 record")
    return nx.from_graph6_bytes(value.encode("ascii"))


def encode_graph6(graph: nx.Graph) -> str:
    """Encode one graph without the optional graph6 header."""
    return nx.to_graph6_bytes(graph, header=False).decode("ascii").strip()


def read_graph6(path: Path, index: int = 0) -> tuple[str, nx.Graph]:
    """Read a zero-based graph6 record from a text file."""
    records = [line.strip() for line in path.read_text(encoding="ascii").splitlines() if line.strip()]
    if not 0 <= index < len(records):
        raise IndexError(f"graph index {index} is outside 0..{len(records) - 1}")
    return records[index], decode_graph6(records[index])

