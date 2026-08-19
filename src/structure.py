"""Machine-checkable structural certificate for the one-fifth theorem."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from math import ceil
from typing import Iterable
import networkx as nx
from .acyclic_matching import is_maximal_acyclic_matching, matching_vertices
Edge=tuple[int,int]

@dataclass(frozen=True)
class MatchingStructureCertificate:
    n:int; k:int; s_size:int; u_size:int; f_components:int; h_tree_components:int
    h_cycle_components:int; h_component_types:tuple[str,...]; e_f:int; e_h:int; e_su:int
    identity_u_rhs:int; identity_n_rhs:int; incidence_edges_distinct:int
    max_tree_component_f_neighbors:int; bound_c_le_2t_plus_1:bool
    parity_upper_bound_n:int; universal_lower_bound:int
    def to_dict(self): return asdict(self)

def _classify(H):
    n=len(H); m=H.number_of_edges(); ds=sorted(dict(H.degree()).values())
    if n==1:return "P1"
    if nx.is_tree(H):
        if ds==[1,1]+[2]*(n-2):return f"P{n}"
        if n==4 and ds==[1,1,1,3]:return "K1,3"
        return "other_tree"
    if m==n and all(d==2 for d in ds):return f"C{n}"
    return "other"

def analyze_maximal_acyclic_matching(G:nx.Graph,M:Iterable[Edge]):
    M=tuple(M)
    if not nx.is_connected(G) or any(d!=3 for _,d in G.degree): raise ValueError("connected cubic required")
    if not is_maximal_acyclic_matching(G,M): raise ValueError("invalid witness")
    S=matching_vertices(M); U=set(G)-S; F=G.subgraph(S).copy(); H=G.subgraph(U).copy()
    FC=[set(C) for C in nx.connected_components(F)]; HC=[set(C) for C in nx.connected_components(H)]
    fi={v:i for i,C in enumerate(FC) for v in C}; incidence=set(); types=[];t=cycles=mx=0
    for j,C in enumerate(HC):
        J=H.subgraph(C); typ=_classify(J);types.append(typ); tree=nx.is_tree(J)
        if tree:t+=1
        elif typ.startswith("C"):cycles+=1
        else:raise AssertionError(f"forbidden H component {typ}")
        adj={fi[s] for u in C for s in G.neighbors(u) if s in S}
        incidence.update((i,j) for i in adj)
        if tree:
            mx=max(mx,len(adj)); assert len(adj)<=3
        else:assert len(adj)==1
    c=len(FC);k=len(M);ef=F.number_of_edges();eh=H.number_of_edges()
    esu=sum((u in S)^(v in S) for u,v in G.edges)
    assert ef==2*k-c and esu==2*k+2*c and esu==len(U)+2*t
    B=nx.Graph();B.add_nodes_from(("F",i) for i in range(c));B.add_nodes_from(("H",j) for j in range(len(HC)))
    B.add_edges_from((("F",i),("H",j)) for i,j in incidence)
    assert len(B)<=1 or nx.is_connected(B)
    cert=MatchingStructureCertificate(len(G),k,len(S),len(U),c,t,cycles,tuple(sorted(types)),ef,eh,esu,
        2*k+2*c-2*t,4*k+2*c-2*t,len(incidence),mx,c<=2*t+1,
        5*k+(1 if k%2 else 0),ceil((len(G)-1)/5))
    assert cert.u_size==cert.identity_u_rhs and cert.n==cert.identity_n_rhs
    assert cert.bound_c_le_2t_plus_1 and cert.n<=cert.parity_upper_bound_n and cert.k>=cert.universal_lower_bound
    return cert
