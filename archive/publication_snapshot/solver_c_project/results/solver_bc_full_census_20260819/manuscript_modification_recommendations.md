# Manuscript modification recommendations

1. Put the full-census table in the main experimental section, emphasizing the n=16 aggregate speedup (2.90x), the n=16 median per-graph speedup (4.58x), and zero discrepancies. Keep these two speedup definitions separate.
2. State explicitly that the 4,681 instances are the complete non-isomorphic connected simple cubic census through order 16, generated with nauty 2.9.3 and verified against the seven expected layer counts.
3. Describe Solver B as the theorem-independent correctness baseline and Solver C as a post-theorem performance algorithm. Do not present agreement as an independent proof of the cubic bound.
4. Put the equality-family table in the supplement or a short scalability subsection. Its very large speedups are structure-specific and must not be described as average census performance.
5. Report that Solver C is not uniformly faster on tiny graphs: it is slower on 127 of 4,681 graphs overall, all of order at most 14, but faster on every n=16 graph.
6. Keep the ablation modest. On the four zero-defect n=16 census graphs, replacing the specialized zero-defect solver by the generic search increased median search time by about 9.7x; disabling the theorem defect budget increased it by about 15.2x. Failed-state memoization had no measurable benefit on this small found-solution sample. Removing near-leaf pruning increased search nodes on the 96 defect-five sample graphs, but did not improve median runtime because the pruning test itself has overhead.
7. Include machine, software, source SHA-256, repetition, warm-up, timer, graph-order, single-thread, and timeout details in the reproducibility appendix.
8. Avoid claims of polynomial running time, a universal exponential base, or a single headline speedup extrapolated from the equality family.
