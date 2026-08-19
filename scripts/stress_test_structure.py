from __future__ import annotations
import json,random,sys
from collections import Counter
from pathlib import Path
import networkx as nx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.acyclic_matching import is_acyclic_matching,is_maximal_acyclic_matching
from src.structure import analyze_maximal_acyclic_matching

def all_matchings(G):
    E=tuple(G.edges());chosen=[]
    def rec(i,used):
        if i==len(E):yield tuple(chosen);return
        yield from rec(i+1,used)
        u,v=E[i]
        if u not in used and v not in used:
            chosen.append((u,v));used.update((u,v));yield from rec(i+1,used);used.remove(u);used.remove(v);chosen.pop()
    yield from rec(0,set())

def graph_suite():
    out=[('K4',nx.complete_graph(4)),('K33',nx.complete_bipartite_graph(3,3)),
         ('triangular_prism',nx.circular_ladder_graph(3)),('cube',nx.cubical_graph()),
         ('petersen',nx.petersen_graph()),('pentagonal_prism',nx.circular_ladder_graph(5))]
    rng=random.Random(20260816)
    for n in (8,10,12):
      for j in range(4):
       while True:
        G=nx.random_regular_graph(3,n,seed=rng.randrange(2**32))
        if nx.is_connected(G):break
       out.append((f'random_cubic_{n}_{j}',nx.convert_node_labels_to_integers(G)))
    return out

def main():
 rows=[];tot=acy=maxi=0;types=Counter()
 for name,G in graph_suite():
  gm=ga=gx=0;ks=[]
  for M in all_matchings(G):
   gm+=1
   if not is_acyclic_matching(G,M):continue
   ga+=1
   if not is_maximal_acyclic_matching(G,M):continue
   gx+=1;c=analyze_maximal_acyclic_matching(G,M);types.update(c.h_component_types);ks.append(len(M))
  tot+=gm;acy+=ga;maxi+=gx;rows.append({'name':name,'n':len(G),'matchings_checked':gm,'acyclic':ga,'maximal':gx,'min_k':min(ks),'max_k':max(ks)})
 data={'graphs':rows,'total_matchings_checked':tot,'total_acyclic_matchings':acy,'total_maximal_acyclic_matchings':maxi,
       'H_component_type_counts':dict(sorted(types.items())),'status':'all structural certificates passed'}
 out=ROOT/'results'/'structure_stress_test.json';out.write_text(json.dumps(data,indent=2),encoding='utf-8')
 print(json.dumps(data,indent=2))
if __name__=='__main__':main()
