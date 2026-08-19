from __future__ import annotations
import json,random,sys,time
from pathlib import Path
from collections import Counter
import networkx as nx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.acyclic_matching import is_maximal_acyclic_matching
from src.structure import analyze_maximal_acyclic_matching
from src.exact_solver import minimum_maximal_acyclic_matching
R=random.Random(20260816)

def random_p4(c):
 a=R.randrange(c)
 def endpoint():
  if R.random()<.5:
   b=R.randrange(c);return (b,b)
  b=R.randrange(c);return tuple(sorted((a,b)))
 return (endpoint(),(a,),(a,),endpoint()),((0,1),(1,2),(2,3))
def random_k13(c):
 x=[R.randrange(c) for _ in range(3)]
 return ((),(x[0],x[0]),(x[1],x[1]),(x[2],x[2])),((0,1),(0,2),(0,3))

def sample_patterns(c,t):
 # Here c=6,t=4 and every component has 4 U vertices.
 for _ in range(200):
  pats=[];counts=[0]*c
  ok=True
  for j in range(t):
   # Last component is repeatedly sampled until it fills the remaining vector.
   found=False
   for _ in range(100):
    p=random_p4(c) if R.random()<.75 else random_k13(c)
    add=[sum(xs.count(i) for xs in p[0]) for i in range(c)]
    if all(counts[i]+add[i]<=4 for i in range(c)):
     if j<t-1 or all(counts[i]+add[i]==4 for i in range(c)):
      found=True;break
   if not found:ok=False;break
   pats.append(p);counts=[counts[i]+add[i] for i in range(c)]
  if ok and counts==[4]*c:return pats
 return None

def build(pats,c=6):
 G=nx.Graph();M=[];F={}
 for lab in range(c):
  a,b=2*lab,2*lab+1;G.add_edge(a,b);M.append((a,b));F[lab]=(a,b)
 labels_by_u={};base=2*c
 for labels,edges in pats:
  for i,xs in enumerate(labels):labels_by_u[base+i]=xs
  G.add_edges_from((base+a,base+b) for a,b in edges);base+=4
 # Random simple degree-capacity assignment per label.
 for lab in range(c):
  occ=[]
  for u,xs in labels_by_u.items():occ.extend([u]*xs.count(lab))
  if len(occ)!=4:return None,None
  # Need split 2/2, and duplicate occurrences at one U must split.
  valid=[]
  for side0 in set(__import__('itertools').combinations(range(4),2)):
   sides=[1]*4
   for i in side0:sides[i]=0
   if all(len({sides[i] for i,u in enumerate(occ) if u==v})==sum(u==v for u in occ) for v in set(occ)):
    valid.append(sides)
  if not valid:return None,None
  sides=R.choice(valid)
  for u,s in zip(occ,sides):G.add_edge(u,F[lab][s])
 return G,tuple(M)

def main():
 start=time.time();stats=Counter();best=0;bestg=None
 for trial in range(200000):
  pats=sample_patterns(6,4)
  if pats is None:stats['pattern_fail']+=1;continue
  stats['patterns']+=1
  G,M=build(pats)
  if G is None or not nx.is_connected(G) or any(d!=3 for _,d in G.degree):stats['build_fail']+=1;continue
  stats['valid']+=1
  # Witness validity is guaranteed by pattern generation, but periodically assert it.
  if trial%1000==0 and not is_maximal_acyclic_matching(G,M):raise AssertionError
  ec=nx.edge_connectivity(G);stats[f'ec{ec}']+=1
  if ec>best:
   best=ec;bestg=nx.to_graph6_bytes(G,header=False).decode().strip();print('new best',best,'trial',trial,bestg,flush=True)
  if ec>=3:
   assert is_maximal_acyclic_matching(G,M);sol=minimum_maximal_acyclic_matching(G)
   data={'status':'FOUND','trial':trial,'graph6':bestg,'matching':M,'mu':sol.mu,'edge_connectivity':ec,
         'structure':analyze_maximal_acyclic_matching(G,M).to_dict(),'stats':dict(stats),'runtime':time.time()-start}
   (ROOT/'results'/'three_edge_n28_counterexample.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
   print(json.dumps(data,indent=2));return
 data={'status':'none','best_edge_connectivity':best,'best_graph6':bestg,'stats':dict(stats),'runtime':time.time()-start}
 (ROOT/'results'/'random_three_edge_template_scan.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print(json.dumps(data,indent=2))
if __name__=='__main__':main()
