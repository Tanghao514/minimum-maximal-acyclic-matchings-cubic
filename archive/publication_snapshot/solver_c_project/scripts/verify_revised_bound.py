from __future__ import annotations
import csv,json,sys
from pathlib import Path
import networkx as nx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.acyclic_matching import is_maximal_acyclic_matching
from src.constructions import one_fifth_extremal_family
from src.exact_solver import minimum_maximal_acyclic_matching
from src.structure import analyze_maximal_acyclic_matching
rows=[];certs=[]
for r in range(4):
  for q in range(5):
    item=one_fifth_extremal_family(r,leaf_excess=q);G=item.graph;M=item.matching
    assert is_maximal_acyclic_matching(G,M);c=analyze_maximal_acyclic_matching(G,M)
    g6=nx.to_graph6_bytes(G,header=False).decode().strip(); exact="not_run";runtime="not_run"
    if r==0 and q<=2:
      sol=minimum_maximal_acyclic_matching(G);exact=sol.mu;runtime=sol.runtime_seconds;assert exact==len(M)
    row={**item.metadata,"graph6":g6,"matching":repr(M),"exact_mu":exact,"exact_runtime_seconds":runtime,
         "lower_bound":c.universal_lower_bound,"c_F":c.f_components,"t_H":c.h_tree_components,"H_types":repr(c.h_component_types)}
    rows.append(row);certs.append({**item.metadata,"graph6":g6,**c.to_dict()})
out=ROOT/'results';out.mkdir(exist_ok=True)
with (out/'one_fifth_extremal_family.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(out/'one_fifth_structure_certificates.json').write_text(json.dumps(certs,indent=2),encoding='utf-8')
for x in rows: print(x['r'],x['leaf_excess'],x['n'],x['k'],x['exact_mu'],x['lower_bound'])
