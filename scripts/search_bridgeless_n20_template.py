from __future__ import annotations
import itertools,json,sys
from collections import Counter
from pathlib import Path
import networkx as nx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.acyclic_matching import is_maximal_acyclic_matching
from src.exact_solver import minimum_maximal_acyclic_matching


def path_patterns():
    # P6 cross capacities 2,1,1,1,1,2. Labels 0=unique,1/2=shared.
    endpoint_multisets=list(itertools.combinations_with_replacement(range(3),2))
    out=[]
    for a in endpoint_multisets:
      for mids in itertools.product(range(3),repeat=4):
       for z in endpoint_multisets:
        labels=(a,(mids[0],),(mids[1],),(mids[2],),(mids[3],),z)
        counts=Counter(x for xs in labels for x in xs)
        if counts != Counter({0:4,1:2,2:2}):continue
        ok=True
        for i in range(5):
          L,R=labels[i],labels[i+1]
          selfL=len(L)==2 and L[0]==L[1]
          selfR=len(R)==2 and R[0]==R[1]
          if not (selfL or selfR or set(L)&set(R)):
            ok=False;break
        if ok:out.append(labels)
    return out


def assign_ports(labels_by_vertex, occurrences_by_label):
    # Each F component has two S vertices, each residual capacity 2.
    # Return all assignments occurrence (u,label,occindex)->side 0/1.
    labels=sorted(occurrences_by_label)
    choices=[]
    for lab in labels:
      occ=occurrences_by_label[lab]
      assert len(occ)==4
      valid=[]
      for sides in itertools.product((0,1),repeat=4):
       if sum(s==0 for s in sides)!=2:continue
       # A U vertex cannot have two edges to the same S vertex.
       if any(len({sides[i] for i,(u,_) in enumerate(occ) if u==v}) < sum(1 for u,_ in occ if u==v)
              for v in {u for u,_ in occ}):
        continue
       valid.append(sides)
      choices.append((lab,occ,valid))
    for selected in itertools.product(*(x[2] for x in choices)):
      mapping=[]
      for (lab,occ,_),sides in zip(choices,selected,strict=True):
       mapping.extend((u,lab,side) for (u,_),side in zip(occ,sides,strict=True))
      yield mapping


def build(pattern1,pattern2,mapping):
    G=nx.Graph(); F={lab:(2*lab,2*lab+1) for lab in range(4)}
    M=tuple(F.values());G.add_edges_from(M)
    paths=[];base=8
    for _ in range(2):
      P=list(range(base,base+6));base+=6;paths.append(P);G.add_edges_from((P[i],P[i+1]) for i in range(5))
    for u,lab,side in mapping:G.add_edge(u,F[lab][side])
    return G,M


def main():
 pats=path_patterns();print('patterns',len(pats))
 checked=0;valid_cubic=0;maximal=0
 # T1 local labels 0,1,2 -> global A=0,B=1,C=2.
 # T2 local labels 0,1,2 -> global D=3,B=1,C=2.
 for p1 in pats:
  for p2 in pats:
   global_sets=[]
   for i,xs in enumerate(p1):global_sets.append((8+i,tuple({0:0,1:1,2:2}[x] for x in xs)))
   for i,xs in enumerate(p2):global_sets.append((14+i,tuple({0:3,1:1,2:2}[x] for x in xs)))
   occ={lab:[] for lab in range(4)}
   for u,xs in global_sets:
    for j,lab in enumerate(xs):occ[lab].append((u,j))
   if any(len(x)!=4 for x in occ.values()):raise AssertionError
   for mapping in assign_ports(global_sets,occ):
    checked+=1;G,M=build(p1,p2,mapping)
    if len(G)!=20 or G.number_of_edges()!=30 or not nx.is_connected(G) or any(d!=3 for _,d in G.degree):continue
    valid_cubic+=1
    if not is_maximal_acyclic_matching(G,M):continue
    maximal+=1
    bridges=list(nx.bridges(G))
    if not bridges:
      sol=minimum_maximal_acyclic_matching(G)
      data={'status':'FOUND','graph6':nx.to_graph6_bytes(G,header=False).decode().strip(),'matching':M,
            'mu':sol.mu,'solver_matching':sol.matching,'pattern1':p1,'pattern2':p2,'checked':checked}
      out=ROOT/'results'/'bridgeless_n20_counterexample.json';out.write_text(json.dumps(data,indent=2),encoding='utf-8')
      print(json.dumps(data,indent=2));return
 print(json.dumps({'status':'none','patterns':len(pats),'checked':checked,'valid_cubic':valid_cubic,'maximal':maximal},indent=2))

if __name__=='__main__':main()
