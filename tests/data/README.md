# Test data

These files are a small subset of the **Core Challenge 2022** benchmark,
obtained from:

https://github.com/core-challenge/2022benchmark

They encode *independent set reconfiguration* instances. Each instance is a pair
of files: a graph (`<name>.col`, DIMACS-like) and a start/goal pair
(`<name>_<id>.dat`). Only the instances exercised by `tests/test_tj_benchmark.py`
are included here, copied verbatim from the upstream repository:

- `handcrafted/` — `hc-toyyes-01`, `hc-toyno-01`, `hc-square-01`, `hc-square-02`,
  `hc-power-11`, `hc-power-12` (each `.col` + `_01.dat`)
- `grid/` — `grid004x004.col` + `grid004x004_01.dat` … `grid004x004_05.dat`

See the upstream repository for the full benchmark set and any license/usage
terms.
