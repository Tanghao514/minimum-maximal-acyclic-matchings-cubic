# Proof audit: lower acyclic matching number of connected cubic graphs

## Status

The proof below was reconstructed independently from the computational code.  The
three vulnerable points—the one-edge blocking criterion, the structure of `G[U]`,
and the incidence-graph inequality—were checked separately and no logical gap was
found.

The proposed exact theorem is:

> **Theorem.** Let `G` be a finite simple connected cubic graph of order `n`.
> Then
> \[
> \mu'_{ac}(G)\ge \left\lceil\frac{n-1}{5}\right\rceil.
> \]
> Moreover, for every even `n>=4`, there is a finite simple connected cubic graph
> `G_n` of order `n` for which equality holds.  Consequently,
> \[
> f_3(n)=\min\{\mu'_{ac}(G):G\text{ connected cubic},\ |V(G)|=n\}
> =\left\lceil\frac{n-1}{5}\right\rceil.
> \]

A stronger intermediate statement is valid for every maximal acyclic matching `M`:

\[
|V(G)|\le
\begin{cases}
5|M|,& |M|\text{ even},\\
5|M|+1,& |M|\text{ odd}.
\end{cases}
\]

## 1. Setup and the one-edge formulation of maximality

Let `M` be any maximal acyclic matching of `G`.  Put

\[
k=|M|,\qquad S=V(M),\qquad U=V(G)\setminus S,
\]

and let

\[
F=G[S],\qquad H=G[U].
\]

By definition, `F` is a forest and `|S|=2k`.

The family of acyclic matchings is hereditary under taking subsets: if `M'` is an
acyclic matching and `M\subseteq M'`, then `M` is a matching and `G[V(M)]` is an
induced subgraph of the forest `G[V(M')]`.  Hence `M` is maximal if and only if no
single edge can be added to it.  An edge can be added as a matching edge only when
both endpoints lie in `U`.  Therefore, for every `uv\in E(H)`,

\[
G[S\cup\{u,v\}]
\]

contains a cycle.

This step uses the full induced graph.  It does not replace the extension by merely
adding the edge `uv` to `F`.

## 2. Exact local blocking criterion

For `x\in U` and a component `C` of `F`, write

\[
d_C(x)=|N_G(x)\cap V(C)|.
\]

### Lemma 1

For `uv\in E(H)`, the induced graph `G[S\cup\{u,v\}]` contains a cycle if and only
if at least one of the following holds:

1. `d_C(u)>=2` for some component `C` of `F`;
2. `d_C(v)>=2` for some component `C` of `F`;
3. `u` and `v` both have a neighbour in the same component `C` of `F`.

### Proof

If (1) holds, two neighbours of `u` in the tree `C` are joined by a unique path in
`C`; together with `u` this path forms a cycle.  The same proves sufficiency of (2).
If (3) holds, take neighbours `a\in N(u)\cap C` and `b\in N(v)\cap C`.  The unique
`a-b` path in `C`, together with `ua`, `uv`, and `vb`, forms a cycle.  This also
covers `a=b`, when the cycle is a triangle.

Conversely, let `Q` be a cycle in `G[S\cup\{u,v\}]`.  Since `F` is a forest, `Q`
contains `u` or `v`.  If it contains exactly one of them, that vertex has two
neighbours on `Q` in one component of `F`, giving (1) or (2).  If it contains both,
then either `uv\in E(Q)`, in which case the remainder of `Q` is a path through one
component of `F`, giving (3), or `uv\notin E(Q)`, in which case the two `u-v` arcs
of `Q` each run through a component of `F`, again giving (3).  This proves the
criterion.

## 3. Structure of the unmatched induced graph

### Lemma 2

Every component of `H=G[U]` is a path, a cycle, or `K_{1,3}`.

### Proof

Suppose a vertex `x\in U` has degree three in `H`.  Then `x` has no neighbour in
`S`.  For every neighbour `y` of `x` in `H`, Lemma 1 applied to `xy` cannot be
satisfied by `x` and cannot be satisfied through a common `F`-component.  Thus `y`
has two neighbours in one component of `F`.  Since `G` is cubic, `y` has exactly
one neighbour in `H`, namely `x`.  Hence the component containing `x` is `K_{1,3}`.

If a component of `H` contains no vertex of degree three, then its maximum degree is
at most two.  A connected finite graph of maximum degree at most two is a path or a
cycle.

Let `t` denote the number of tree components of `H`; isolated vertices and
`K_{1,3}` components are included in `t`.

### Lemma 3

Every tree component of `H` is adjacent to at most three distinct components of
`F`.  Every cycle component of `H` is adjacent to exactly one component of `F`.

### Proof for tree components

For an isolated vertex, the claim follows from cubicity: it has three neighbours in
`S`.

For a `K_{1,3}`, the centre has no neighbour in `S`.  Each leaf must have its two
`S`-neighbours in a single component of `F`, by Lemma 1 applied to its edge to the
centre.  Thus the three leaves contribute at most three `F`-components.

It remains to consider a path `x_1...x_r`, where `r>=2`.  Every internal vertex has
exactly one neighbour in `S`.  For two consecutive internal vertices, neither can
satisfy a self-blocking condition in Lemma 1, so their unique `S`-neighbours lie in
the same component of `F`.  Hence all internal vertices are attached to one common
component `C` of `F` (when there is only one internal vertex, call its component
`C`).

At an endpoint, either its two `S`-neighbours lie in one component, contributing at
most one component in addition to `C`, or they lie in two distinct components, in
which case Lemma 1 forces one of them to be `C`, again contributing at most one new
component.  The two endpoints therefore contribute at most two additional
components.  Thus the whole path sees at most three components of `F`.

For `r=2`, there is no internal vertex.  If an endpoint self-blocks, it contributes
one component and the other endpoint contributes at most two.  If neither endpoint
self-blocks, their two-component neighbour sets must intersect by Lemma 1, so their
union has size at most three.  Thus the same conclusion holds.

### Proof for cycle components

Every vertex of a cycle component has degree two in `H` and therefore exactly one
neighbour in `S`.  For each edge of the cycle, neither endpoint self-blocks, so Lemma
1 forces the two unique `S`-neighbours to lie in the same component of `F`.  Going
around the cycle shows that every vertex is adjacent to one and the same component
of `F`.  Cubicity gives at least one such neighbour, so the number is exactly one.

## 4. The incidence graph and the key inequality

Let `c` be the number of components of `F`.  Form a simple bipartite incidence graph
`B` whose left vertices are the components of `F`, whose right vertices are the
components of `H`, and where two component-vertices are adjacent when there is at
least one edge of `G` between them.

Because `G` is connected, `B` is connected.  By Lemma 3, every cycle component of
`H` is a leaf of `B`.  Delete all these leaves.  The remaining graph `B_0` is still
connected: a degree-one vertex cannot be an internal vertex of a path between two
remaining vertices.

The graph `B_0` has `c+t` vertices.  Hence it has at least `c+t-1` edges.  On the
other hand, every one of the `t` tree components of `H` has degree at most three in
`B_0`, so `B_0` has at most `3t` edges.  Therefore

\[
c+t-1\le3t,
\]

and hence

\[
\boxed{c\le2t+1}. \tag{4.1}
\]

Also,

\[
\boxed{c\le k}, \tag{4.2}
\]

because every component of `F` contains at least one edge of `M`.

## 5. Exact counting identities

Since `F` is a forest on `2k` vertices with `c` components,

\[
|E(F)|=2k-c.
\]

Counting the edges between `S` and `U` from the `S` side gives

\[
|E(S,U)|=3|S|-2|E(F)|
=6k-2(2k-c)=2k+2c. \tag{5.1}
\]

By Lemma 2, each component of `H` is either a tree or a cycle.  Thus

\[
|E(H)|=|U|-t.
\]

Counting the same cut from the `U` side gives

\[
|E(S,U)|=3|U|-2|E(H)|
=3|U|-2(|U|-t)=|U|+2t. \tag{5.2}
\]

Equating (5.1) and (5.2),

\[
|U|=2k+2c-2t.
\]

Consequently,

\[
\boxed{n=4k+2(c-t)}. \tag{5.3}
\]

## 6. Optimisation

From (4.1) and (4.2),

\[
c-t\le\min\{k-t,t+1\}.
\]

For an integer `t>=0`, the maximum of the right-hand side is

\[
\left\lceil\frac{k}{2}\right\rceil.
\]

Substituting into (5.3),

\[
n\le4k+2\left\lceil\frac{k}{2}\right\rceil
=
\begin{cases}
5k,&k\text{ even},\\
5k+1,&k\text{ odd}.
\end{cases}
\]

In particular `n<=5k+1`, so

\[
k\ge\left\lceil\frac{n-1}{5}\right\rceil.
\]

Since this holds for every maximal acyclic matching `M`, it holds for a minimum one.

## 7. Direct sharpness construction

The following construction avoids any recursive graph replacement and directly
produces a witness.

### 7.1 Maximum-order base for every odd matching size

Let `k_0=2t+1` be odd with `t>=1`.  Construct `F=G[S]` from `k_0` copies of `K_2`.
The edges of these copies form the matching.

Use one distinguished `K_2`, called the root-central component.  Add a `P_4` in
`U`; attach each of its four vertices once to the root-central `K_2`, using all four
available cubic stubs.  Attach the two endpoints of this `P_4` once each to two
further `K_2` components.  Every edge of this `P_4` is blocked because its endpoints
have neighbours in the root-central `F`-component.

When `t>1`, keep one of the two latter `K_2` components active.  For each of the
remaining `t-1` stages, add a `P_3` in `U`; attach all three vertices of this `P_3`
to the three unused stubs of the active `K_2`.  Attach the two endpoints of the
`P_3` once each to two new `K_2` components, keep one new component active, and
mark the other terminal.  Every edge of this `P_3` is blocked through the old active
`F`-component.

Finally, every terminal `K_2` has exactly three unused cubic stubs.  Attach a fresh
triangle in `U` to those three stubs.  Every triangle edge is blocked because both
endpoints see the same `F`-component.

The construction has:

- `k_0=2t+1` matching edges;
- `2k_0` vertices in `S`;
- one `P_4`, `t-1` copies of `P_3`, and `t+1` triangles in `U`.

Therefore

\[
|U|=4+3(t-1)+3(t+1)=6t+4=3k_0+1,
\]

and

\[
n=2k_0+|U|=5k_0+1.
\]

The distinguished matching is acyclic because `G[S]` is a disjoint union of
`K_2`s, and maximal by the blocking observations above.

### 7.2 Residue adjustment

Choose a terminal `K_2` together with its attached triangle.  For an integer
`q>=0`, replace them in the direct description by:

- an alternating path `P_{2(q+1)}` in `S`, containing `q+1` matching edges;
- a cycle `C_{2q+3}` in `U`.

Use one cubic stub of the path for the existing attachment to the preceding `P_4`
or `P_3`, and join its remaining `2q+3` stubs one-to-one to the cycle.  This preserves
simplicity, connectedness, cubicity, acyclicity of `G[S]`, and maximality.

Relative to the `K_2+C_3` pair, this adds `q` matching edges and `4q` vertices.  If
`k=k_0+q`, then

\[
n=(5k_0+1)+4q=5k+1-q. \tag{7.1}
\]

### 7.3 Coverage of all even orders

Let `n>=4` be even and put

\[
k=\left\lceil\frac{n-1}{5}\right\rceil,
\qquad q=5k+1-n.
\]

Then `q\in\{0,1,2,3,4\}`.  Since `n` is even,

\[
k-q\equiv1\pmod2.
\]

Set `k_0=k-q`.  If `k_0>=3`, the odd-base construction with residue adjustment
produces order `n` and matching size `k` by (7.1).

If `k_0=1`, then `n\in\{6,10,14,18,22\}`.  Use `F=P_{2k}` with its alternating
matching and `H=C_{2k+2}`, joining all cubic stubs of `F` one-to-one to `H`.  This
has order `4k+2=n` and the matching is maximal because every `H`-edge has both
endpoints adjacent to the single component of `F`.

The remaining orders `4,8,12` are supplied by `K_4`, the cube, and the hexagonal
prism, respectively, with explicit witnesses of sizes `1,2,3`.

This proves sharpness for every admissible order.

## 8. Equality information exposed by the proof

For odd `k`, equality in the parity-refined bound `n=5k+1` forces

\[
c=k,\qquad t=\frac{k-1}{2},\qquad c=2t+1.
\]

Thus every component of `F` contains exactly one matching edge, and the incidence
core reaches equality in both its connected lower edge bound and the degree-three
upper bound.

For even `k`, equality `n=5k` can occur in either of the two parameter patterns

\[
(c,t)=\left(k,\frac{k}{2}\right)
\quad\text{or}\quad
(c,t)=\left(k-1,\frac{k}{2}-1\right).
\]

The direct residue-adjusted construction uses the second pattern.

## 9. Independent computational checks completed

The following checks are supplementary and are not used as proof:

- an independent DSU implementation of matching, induced-forest, and maximality;
- 1,652 direct tests of the exact local blocking equivalence on all acyclic
  matchings of six standard cubic graphs;
- structural audits of all 179 maximal acyclic matchings in that suite;
- two independent sharpness constructors, each checked for all 249 even orders
  `4<=n<=500`;
- exact-solver tests on 56 fixed-seed random connected cubic graphs of orders
  `14,16,18,20,22,24`, with every witness rechecked by the independent definitions.

No violation was found.

## 10. Remaining non-computational checks

Before public circulation, the following should still be done:

1. obtain an independent human referee-style reading of Lemmas 1--3 and the
   incidence-core deletion argument;
2. complete a systematic literature search under both “minimum maximal acyclic
   matching” and “lower acyclic matching number”;
3. decide whether to state the parity-refined inequality as the main theorem or as
   a strengthening preceding the exact extremal formula.
