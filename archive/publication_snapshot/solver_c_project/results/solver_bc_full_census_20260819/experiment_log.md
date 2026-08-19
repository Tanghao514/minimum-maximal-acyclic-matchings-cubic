# Experiment log

## 2026-08-19: baseline audit

- Located Solver B and Solver C entry points and inspected their result fields.
- Confirmed no packaged cubic census file is present.
- Ran the project test suite: 12 tests passed.
- Located WSL2 and GCC; built nauty 2.9.3 `geng` from the official source distribution in a temporary WSL directory.
- Decision: generate a fresh graph6 census and require exact agreement with the protocol's seven expected layer counts before timing.

## 2026-08-19: census generation and load-control decision

- Generated all seven graph6 layers with nauty 2.9.3 `geng`.
- Verified exact layer counts 1, 2, 5, 19, 85, 509, and 4060 (total 4681).
- Detected two pre-existing CPU-intensive `day5_stress.py 300 40` processes before the timed census.
- Stopped only the newly launched benchmark process before it produced paper-facing timing results; left the pre-existing jobs untouched.
- Decision: run correctness-only checks while the machine is loaded, then start the timed census only after the background CPU load is gone.

## 2026-08-19: correctness and formal runs

- With user authorization, stopped the two pre-existing `day5_stress.py 300 40` jobs before formal timing.
- Passed 64 correctness cases: 10 standard/prism graphs, 4 supplied n=16 counterexamples, and 50 fixed-seed random connected cubic graphs. Both witnesses were checked by the definition-level checker in every case.
- Completed all 4681 census graphs with five repetitions through n=12 and three repetitions at n=14,16. No optimum discrepancies or timeouts occurred.
- Completed the equality family at n=16,20,24,26,28,32,36,46,56 with a common 300-second limit. Solver B timed out at n=46 and n=56; Solver C solved all cases.
- Completed five Solver C variants on a deterministic 100-graph n=16 stratified sample, three repetitions per graph (500 output rows).
