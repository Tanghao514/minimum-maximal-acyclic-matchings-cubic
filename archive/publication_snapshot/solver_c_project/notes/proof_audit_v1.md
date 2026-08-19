# Proof audit v1: lower acyclic matching number of connected cubic graphs

## Audited theorem

Let \(G\) be a finite simple connected cubic graph of order \(n\). Then

\[
\mu'_{ac}(G)\ge \left\lceil\frac{n-1}{5}\right\rceil.
\]

Moreover, for every even \(n\ge4\), there is a finite simple connected cubic graph \(G_n\) with

\[
\mu'_{ac}(G_n)=\left\lceil\frac{n-1}{5}\right\rceil.
\]

Thus the proposed extremal function is

\[
f_3(n)=\left\lceil\frac{n-1}{5}\right\rceil
\qquad(n\ge4\text{ even}).
\]

This document is a hostile proof audit, not a polished manuscript.

## 1. Setup

Fix an arbitrary maximal acyclic matching \(M\) of \(G\). Put

\[
k=|M|,\qquad S=V(M),\qquad U=V(G)\setminus S,
\]

and let

\[
F=G[S],\qquad H=G[U].
\]

By definition, \(F\) is a forest on \(2k\) vertices. Let \(c\) be the number of components of \(F\), and let \(t\) be the number of tree components of \(H\). Since every component of \(F\) contains at least one edge of \(M\),

\[
c\le k. \tag{1}
\]

## 2. Exact local blocking criterion

For \(x\in U\), let \(\mathcal C(x)\) be the multiset of components of \(F\) containing the neighbors of \(x\) in \(S\).

For every edge \(xy\in E(H)\), the graph \(G[S\cup\{x,y\}]\) contains a cycle if and only if at least one of the following holds:

1. \(x\) has two neighbors in one component of \(F\);
2. \(y\) has two neighbors in one component of \(F\);
3. \(x\) and \(y\) have neighbors in a common component of \(F\).

**Audit.** The graph added to the forest \(F\) consists only of \(x,y\), the edge \(xy\), and their edges into \(F\). A cycle using only one of \(x,y\) exists exactly when that vertex has two neighbors in one tree component. If neither such cycle exists, a cycle must use \(xy\); deleting \(xy\) leaves an \(x\)-to-\(y\) path exactly when both vertices attach to one common tree component. No fourth case is possible.

Because \(M\) is maximal, this criterion must hold for every edge of \(H\).

## 3. Classification of the components of \(H\)

### Lemma 1
Every component of \(H\) is a path, a cycle, or \(K_{1,3}\).

**Proof.** If a vertex \(x\in U\) has degree three in \(H\), it has no neighbor in \(S\). For each neighbor \(y\) of \(x\), the edge \(xy\) cannot be blocked by condition 1 at \(x\), nor by condition 3. Hence \(y\) has two neighbors in one component of \(F\), so \(d_H(y)=1\). The component is therefore \(K_{1,3}\). If a component has no degree-three vertex, its maximum degree is at most two, hence it is a path or a cycle. \(\square\)

### Lemma 2
Every tree component of \(H\) is adjacent to at most three distinct components of \(F\).

**Proof.**

- For \(P_1\), its unique vertex has three neighbors in \(S\), hence reaches at most three components.
- For \(K_{1,3}\), the center has no neighbor in \(S\). Each leaf must self-block the incident edge, so its two \(S\)-neighbors lie in one component of \(F\). The three leaves therefore reach at most three components.
- For \(P_2=xy\), if one endpoint self-blocks, that endpoint reaches one component and the other endpoint reaches at most two; otherwise the endpoints share a component and each can introduce at most one further component. Thus at most three components occur.
- For \(P_r=x_1\ldots x_r\) with \(r\ge3\), each internal vertex has exactly one neighbor in \(S\). Consecutive internal vertices must attach to the same component of \(F\), so all internal vertices attach to one component \(C\). At each end, either the endpoint self-blocks and reaches one component, or it shares \(C\) with the adjacent internal vertex and has at most one additional component. Hence the whole path reaches at most \(C\) plus one component at each end.

Thus every tree component reaches at most three components of \(F\). \(\square\)

### Lemma 3
Every cycle component of \(H\) is adjacent to exactly one component of \(F\).

**Proof.** Every vertex on such a cycle has exactly one neighbor in \(S\), so no vertex can self-block. The two endpoints of every cycle edge must therefore attach to a common component of \(F\). Propagating around the cycle shows that all vertices attach to the same component. Connectivity of \(G\) gives at least one attachment. \(\square\)

The independent script `scripts/adversarial_proof_audit.py` exhaustively checked these three conclusions for every connected subcubic graph in the NetworkX graph atlas (all such graphs of order at most seven) and every abstract partition of all available \(S\)-neighbor slots into possible \(F\)-components.

## 4. Incidence inequality

Form a simple bipartite incidence graph \(B\): its left vertices are the \(c\) components of \(F\), its right vertices are the components of \(H\), and adjacency means that at least one edge of \(G\) joins the two components.

Since \(G\) is connected, \(B\) is connected. By Lemma 3, every cycle component of \(H\) is a leaf of \(B\). Delete those leaves. The remaining graph \(B_0\), whose vertices are the \(c\) components of \(F\) and the \(t\) tree components of \(H\), is still connected. (Deleting leaves cannot destroy connectivity among the remaining vertices; if no tree component remains, connectedness forces \(c=1\).)

Hence \(B_0\) has at least \(c+t-1\) edges. By Lemma 2, every one of its \(t\) right-side vertices has degree at most three, so it has at most \(3t\) edges. Therefore

\[
c+t-1\le3t,
\]

or

\[
c\le2t+1. \tag{2}
\]

## 5. Exact cubic counting

Since \(F\) is a forest on \(2k\) vertices with \(c\) components,

\[
|E(F)|=2k-c.
\]

Counting the cut \(E(S,U)\) from the \(S\)-side gives

\[
|E(S,U)|=3|S|-2|E(F)|=6k-2(2k-c)=2k+2c. \tag{3}
\]

By Lemma 1, every component of \(H\) is a tree or a cycle. If \(t\) of them are trees, then

\[
|E(H)|=|U|-t.
\]

Counting the same cut from the \(U\)-side gives

\[
|E(S,U)|=3|U|-2|E(H)|=|U|+2t. \tag{4}
\]

Equating (3) and (4),

\[
|U|=2k+2c-2t,
\]

and consequently

\[
n=2k+|U|=4k+2(c-t). \tag{5}
\]

## 6. Optimization

From (1) and (2),

\[
c-t\le \min\{k-t,t+1\}.
\]

For integral \(t\ge0\), the maximum of the right-hand side is \(\lceil k/2\rceil\). Therefore

\[
n\le4k+2\left\lceil\frac{k}{2}\right\rceil
=
\begin{cases}
5k,&k\text{ even},\\
5k+1,&k\text{ odd}.
\end{cases} \tag{6}
\]

In particular, \(n\le5k+1\), whence

\[
k\ge\left\lceil\frac{n-1}{5}\right\rceil.
\]

The argument applies to every maximal acyclic matching \(M\), proving the lower bound for \(\mu'_{ac}(G)\).

## 7. Sharpness construction: audited blueprint

The construction is most cleanly described with a marked leaf gadget.

### Base graph at \(n=16,k=3\)

Take three disjoint matching edges as the components of \(F\). Let \(H\) consist of one \(P_4\) and two triangles. Attach every vertex of the \(P_4\) to the same central \(F\)-component, attach its two endpoints once more to the two leaf \(F\)-components, and attach each leaf component's remaining three cubic stubs to one of the triangles. The distinguished three edges form a maximal acyclic matching: every path edge is blocked through the central \(F\)-component, and every triangle edge through its leaf component. Either leaf \(K_2\) together with its attached triangle is marked.

### Branch expansion

Remove the triangle of a marked leaf, exposing three stubs of its \(F\)-component. Add a \(P_3\), joining its three vertices to those stubs. Add two new matching edges, join the two ends of the \(P_3\) once to the two new matching-edge components, and attach each new component's remaining three stubs to a new triangle. This adds ten vertices and two matching edges, preserves connected cubic simplicity and maximal acyclicity, and leaves a new marked leaf. Repeating gives, for every odd \(k_0\ge3\), an equality graph of order \(5k_0+1\).

### Leaf enlargement

For \(q\in\{0,1,2,3,4\}\), replace a marked \(K_2\)-plus-\(C_3\) leaf by an alternating \(F\)-path \(P_{2(q+1)}\) containing \(q+1\) matching edges and an \(H\)-cycle \(C_{2q+3}\). Use one residual path stub for the old external edge and join the remaining \(2q+3\) stubs bijectively to the cycle. This adds \(4q\) vertices and \(q\) matching edges. Every new cycle edge is blocked by the single enlarged \(F\)-component.

For an even target order \(n\), put

\[
k=\left\lceil\frac{n-1}{5}\right\rceil,
\qquad q=5k+1-n,
\qquad k_0=k-q.
\]

Then \(0\le q\le4\), and because \(n\) is even, \(k_0\) is odd. If \(k_0\ge3\), use the odd base with \(k_0\) matching edges and then enlarge by \(q\). The result has

\[
|M|=k_0+q=k,
\qquad |V|=5k_0+1+4q=5k+1-q=n.
\]

If \(k_0=1\), then \(n=4k+2\) and \(1\le k\le5\). Use \(F=P_{2k}\), \(H=C_{2k+2}\), and join the cycle vertices bijectively to the residual cubic stubs of the path. All cycle edges are blocked through the single component \(F\).

The three remaining orders are handled directly:

- \(n=4\): \(K_4\) with one matching edge;
- \(n=8\): the cube with matching \(\{000\!-001,110\!-111\}\);
- \(n=12\): the hexagonal prism with an alternating matching on an induced six-vertex path.

The independent audit script directly reconstructs \(G[V(M)\cup\{u,v\}]\) for every edge \(uv\in E(G[U])\) for every even order through 300, rather than using the structural certificate code.

## 8. Audit verdict

As of this audit:

- no logical failure has been found in the lower-bound proof;
- all path boundary cases \(P_1,P_2,P_3\) were checked separately;
- the incidence-graph deletion step is valid;
- the integer optimization is exact;
- every even order is covered by the construction arithmetic;
- direct computational checks independently validate all constructed witnesses through order 300;
- exact solvers already validate optimality of the construction examples through order 26.

Remaining work before public claim:

1. have an external graph theorist independently referee Lemmas 1--3 and the incidence argument;
2. replace the recursive construction description by a clean figure and formal operation notation;
3. complete a systematic literature search through 2026 databases and citation chains;
4. remove all computational language from the theorem proof except for the historical discovery/verification section.
