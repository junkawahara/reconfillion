# Test data

These files are a small subset of the **Core Challenge 2022** benchmark,
obtained from:

https://github.com/core-challenge/2022benchmark

They encode *independent set reconfiguration* instances. Each instance is a pair
of files: a graph (`<name>.col`, DIMACS-like) and a start/goal pair
(`<name>_<id>.dat`). The instances are exercised by both
`tests/test_tj_benchmark.py` (token jumping) and `tests/test_tar_benchmark.py`
(token addition/removal). The `tar` tests reuse each instance with two size
ranges: `[k-1, k]` (where `k = |s| = |t|`), whose reachability must agree with
the `tj` result, and `[k, ∞)`, the standard TAR(k) model. The files are copied
verbatim from the upstream repository:

- `handcrafted/` — `hc-toyyes-01`, `hc-toyno-01`, `hc-square-01`, `hc-square-02`,
  `hc-power-11`, `hc-power-12` (each `.col` + `_01.dat`)
- `grid/` — `grid004x004.col` + `grid004x004_01.dat` … `grid004x004_05.dat`

See the upstream repository for the full benchmark set and any license/usage
terms.
