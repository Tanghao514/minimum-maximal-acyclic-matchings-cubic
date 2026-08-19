from __future__ import annotations
import itertools,json,sys,time
from collections import Counter
from pathlib import Path
import networkx as nx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.acyclic_matching import is_maximal_acyclic_matching
from src.exact_solver import minimum_maximal_acyclic_matching


def integer_partitions_cycles(total,minimum=3):
    def rec(rem,last,prefix):
        if rem==0:
            yield tuple(prefix);return
        for x in range(last,rem+1):
            if x<minimum:continue
            if rem-x and rem-x<x:break
            prefix.append(x);yield from rec(rem-x,x,prefix);prefix.pop()
    yield from rec(total,minimum,[])


def multisets(labels,size):return list(itertools.combinations_with_replacement(range(labels),size))

def tree_patterns(kind,size,c):
    """Yield (vertex-label-tuples, H_edges), local vertices 0..size-1."""
    if kind=='P':
        if size==1:
            for x in multisets(c,3):yield (x,),()
        elif size==2:
            for a in multisets(c,2):
             for b in multisets(c,2):
              if (a[0]==a[1]) or (b[0]==b[1]) or (set(a)&set(b)):
               yield (a,b),((0,1),)
        else:
            for mid in range(c):
                opts=[x for x in multisets(c,2) if x[0]==x[1] or mid in x]
                for a in opts:
                 for b in opts:
                  labels=(a,)+tuple((mid,) for _ in range(size-2))+(b,)
                  yield labels,tuple((i,i+1) for i in range(size-1))
    elif kind=='K13':
        assert size==4
        # local 0 center; 1,2,3 leaves. Each leaf self-blocks.
        for labs in itertools.product(range(c),repeat=3):
            yield ((),(labs[0],labs[0]),(labs[1],labs[1]),(labs[2],labs[2])),((0,1),(0,2),(0,3))
    else:raise ValueError


def cycle_patterns(size,c):
    for lab in range(c):
        yield tuple((lab,) for _ in range(size)),tuple((i,(i+1)%size) for i in range(size))


def component_options(kind,size,c):
    raw=cycle_patterns(size,c) if kind=='C' else tree_patterns(kind,size,c)
    out=[]
    for labels,edges in raw:
        counts=tuple(sum(xs.count(i) for xs in labels) for i in range(c))
        incidence=frozenset(i for i,x in enumerate(counts) if x)
        out.append((labels,edges,counts,incidence))
    return out


def f_case(c):
    G=nx.Graph();M=[];components=[];nextv=0
    if c==3:
        V=list(range(4));nextv=4;G.add_edges_from([(0,1),(1,2),(2,3)]);M.extend([(0,1),(2,3)]);components.append(V)
        for _ in range(2):
            a,b=nextv,nextv+1;nextv+=2;G.add_edge(a,b);M.append((a,b));components.append([a,b])
    elif c==4:
        for _ in range(4):
            a,b=nextv,nextv+1;nextv+=2;G.add_edge(a,b);M.append((a,b));components.append([a,b])
    else:raise ValueError
    caps=[]
    for C in components:caps.append({v:3-G.degree(v) for v in C})
    return G,tuple(M),components,caps


def port_assignments(labels_by_u,caps_by_label):
    """Yield lists of cross edges satisfying all S capacities and simplicity."""
    req={lab:[] for lab in range(len(caps_by_label))}
    for u,xs in labels_by_u.items():
        for lab in set(xs):req[lab].append((u,xs.count(lab)))
    per=[]
    for lab,caps0 in enumerate(caps_by_label):
        items=sorted(req[lab],key=lambda z:-z[1]);solutions=[]
        caps=dict(caps0);chosen=[]
        def rec(i):
            if i==len(items):
                if all(v==0 for v in caps.values()):solutions.append(tuple(chosen))
                return
            u,need=items[i]
            avail=[s for s,x in caps.items() if x>0]
            for subset in itertools.combinations(avail,need):
                for s in subset:caps[s]-=1;chosen.append((u,s))
                rec(i+1)
                for _ in subset:chosen.pop()
                for s in subset:caps[s]+=1
        rec(0)
        if not solutions:return
        per.append(solutions)
    for combo in itertools.product(*per):yield tuple(e for part in combo for e in part)


def layouts():
    # c=3,t=1 and c=4,t=2; total U vertices 12.
    for c in (3,4):
      t=c-2
      shapes=[('P',i) for i in range(1,13)]+[('K13',4)]
      if t==1:
       for sh in shapes:
        left=12-sh[1]
        for cyc in integer_partitions_cycles(left):
         yield c,(sh,)+tuple(('C',x) for x in cyc)
      else:
       for i,a in enumerate(shapes):
        for b in shapes[i:]:
         left=12-a[1]-b[1]
         if left<0:continue
         for cyc in integer_partitions_cycles(left):
          yield c,(a,b)+tuple(('C',x) for x in cyc)


def main():
    start=time.time();stats=Counter();max_ec=0;best=None;layout_count=0
    option_cache={}
    for c,layout in layouts():
      layout_count+=1;stats['layouts']+=1
      base,M,Fcomps,caps=f_case(c); capacities=tuple(sum(d.values()) for d in caps)
      options=[]
      for kind,size in layout:
       key=(kind,size,c);option_cache.setdefault(key,component_options(kind,size,c));options.append(option_cache[key])
      picked=[]
      def choose(j,remaining):
       nonlocal max_ec,best
       if j==len(options):
        if any(remaining):return
        # Tree components are the first c-2 items; their incidence hypergraph must connect F labels.
        B=nx.Graph();B.add_nodes_from(('F',i) for i in range(c))
        for z,opt in enumerate(picked[:c-2]):
          B.add_node(('T',z));B.add_edges_from((('F',i),('T',z)) for i in opt[3])
        if len(B)>1 and not nx.is_connected(B):return
        stats['label_combinations']+=1
        G=base.copy();labels_by_u={};offset=8
        for opt in picked:
          labels,edges,_,_=opt
          for i,xs in enumerate(labels):labels_by_u[offset+i]=xs
          G.add_nodes_from(range(offset,offset+len(labels)))
          G.add_edges_from((offset+a,offset+b) for a,b in edges)
          offset+=len(labels)
        assert offset==20
        for cross in port_assignments(labels_by_u,caps):
          stats['port_assignments']+=1;H=G.copy();H.add_edges_from(cross)
          if not nx.is_connected(H) or any(d!=3 for _,d in H.degree):continue
          stats['cubic_connected']+=1
          if not is_maximal_acyclic_matching(H,M):raise AssertionError('label blocking mismatch')
          ec=nx.edge_connectivity(H);stats[f'edgeconn_{ec}']+=1
          if ec>max_ec:
            max_ec=ec;best=(H.copy(),M,c,layout,picked.copy());print('NEW MAX',max_ec,'layout',c,layout,'g6',nx.to_graph6_bytes(H,header=False).decode().strip())
          if ec>=3:
            sol=minimum_maximal_acyclic_matching(H)
            data={'status':'FOUND','graph6':nx.to_graph6_bytes(H,header=False).decode().strip(),'matching':M,'mu':sol.mu,
                  'c':c,'layout':layout,'stats':dict(stats),'runtime':time.time()-start}
            (ROOT/'results'/'three_edge_n20_counterexample.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
            print(json.dumps(data,indent=2));raise SystemExit
        return
       for opt in options[j]:
        counts=opt[2]
        if any(counts[i]>remaining[i] for i in range(c)):continue
        # Cycles must meet exactly one F component (already true); each tree must meet <=3.
        if j<c-2 and not (1<=len(opt[3])<=3):continue
        picked.append(opt);choose(j+1,tuple(remaining[i]-counts[i] for i in range(c)));picked.pop()
      choose(0,capacities)
    data={'status':'none','max_edge_connectivity':max_ec,'stats':dict(stats),'runtime':time.time()-start}
    if best:data['best_graph6']=nx.to_graph6_bytes(best[0],header=False).decode().strip();data['best_matching']=best[1];data['best_layout']=best[3]
    (ROOT/'results'/'three_edge_n20_template_scan.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps(data,indent=2))
if __name__=='__main__':main()
