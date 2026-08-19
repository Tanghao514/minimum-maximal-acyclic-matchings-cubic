from __future__ import annotations
import csv,json,sys
from pathlib import Path
import networkx as nx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.acyclic_matching import is_maximal_acyclic_matching
from src.constructions import extremal_graph_for_order
from src.exact_solver import minimum_maximal_acyclic_matching
from src.structure import analyze_maximal_acyclic_matching
rows=[];certs=[]
for n in range(4,102,2):
    item=extremal_graph_for_order(n);G=item.graph;M=item.matching
    assert len(G)==n and nx.is_connected(G) and all(d==3 for _,d in G.degree)
    assert is_maximal_acyclic_matching(G,M)
    cert=analyze_maximal_acyclic_matching(G,M)
    exact='not_run';runtime='not_run'
    if n<=26:
        sol=minimum_maximal_acyclic_matching(G);exact=sol.mu;runtime=sol.runtime_seconds
        assert exact==len(M)
    rows.append({'n':n,'k':len(M),'lower_bound':cert.universal_lower_bound,'exact_mu':exact,
                 'exact_runtime_seconds':runtime,'family':item.metadata.get('family'),
                 'graph6':nx.to_graph6_bytes(G,header=False).decode().strip(),'matching':repr(M),
                 'c_F':cert.f_components,'t_H':cert.h_tree_components,'H_types':repr(cert.h_component_types)})
    certs.append({'n':n,'metadata':item.metadata,'graph6':rows[-1]['graph6'],**cert.to_dict()})
out=ROOT/'results'
with (out/'all_even_extremal_constructions.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(out/'all_even_extremal_certificates.json').write_text(json.dumps(certs,indent=2),encoding='utf-8')
print('verified',len(rows),'orders, n=4..100')
for x in rows[:12]:print(x['n'],x['k'],x['exact_mu'],x['family'])
print('last',rows[-1]['n'],rows[-1]['k'],rows[-1]['family'])
