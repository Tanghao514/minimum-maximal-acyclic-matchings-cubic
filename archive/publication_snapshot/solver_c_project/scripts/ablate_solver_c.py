from __future__ import annotations

import csv
import json
from pathlib import Path
from time import perf_counter

import networkx as nx

from scripts.benchmark_solver_c import shuffled_graph
from src.constructions import extremal_graph_for_order_direct
from src.exact_solver import minimum_maximal_acyclic_matching
from src.solver_c import _CubicInteractionSolver

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "solver_c_ablation.csv"


def run_variant(G, k, budget, rigid):
    s = _CubicInteractionSolver(G)
    if not rigid:
        s._rigid_maximality_filter = lambda infos, selected_mask, need: infos  # type: ignore[method-assign]
    t0 = perf_counter()
    witness = s._find_size_k(k, budget)
    dt = perf_counter() - t0
    return {
        "found": witness is not None,
        "seconds": dt,
        "nodes": s.recursion_nodes,
        "complete": s.complete_candidates,
        "rigid_prunes": s.prune_rigid_maximality,
    }


def main():
    cases = []
    for n in (22, 24, 26, 28):
        cases.append(("equality", f"eq{n}", shuffled_graph(extremal_graph_for_order_direct(n).graph, 17000+n)))
    for n in (22, 24):
        G = nx.random_regular_graph(3, n, seed=19000+n)
        if nx.is_connected(G):
            cases.append(("random", f"rnd{n}", G))

    rows=[]
    for fam,name,G in cases:
        k=minimum_maximal_acyclic_matching(G).mu
        structural=min(k-1,5*k+1-len(G))
        variants={
            "full": run_variant(G,k,structural,True),
            "no_rigid": run_variant(G,k,structural,False),
            "no_defect_budget": run_variant(G,k,k-1,True),
            "interaction_only": run_variant(G,k,k-1,False),
        }
        for variant,data in variants.items():
            rows.append({"family":fam,"case":name,"n":len(G),"mu":k,"variant":variant,"defect_budget": structural if 'defect' not in variant and variant!='interaction_only' else k-1,**data})
        print(name,json.dumps(variants),flush=True)
    with OUT.open('w',newline='',encoding='utf-8') as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

if __name__=='__main__':main()
