# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Reconfillion is a Python tool for solving **combinatorial reconfiguration problems**. Given a start state `s` and goal state `t` (each a subset of elements/edges/vertices) drawn from a search space of *all* valid states, it computes a step-by-step *reconfiguration sequence* transforming `s` into `t` where each step is a single legal move.

The entire implementation is one file: `reconfillion/reconf.py`. `reconfillion/__init__.py` is empty, so the public API is accessed as `from reconfillion import reconf`.

## Architecture

The library is built on top of [graphillion](https://github.com/takemaru/graphillion) (`>=1.7`), whose ZDD-based set families (`setset`, `GraphSet`, `VertexSetSet`) compactly represent astronomically large families of subsets. Reconfillion never enumerates states explicitly — it operates on whole set families at once.

The core algorithm in `get_reconf_seq` is a **breadth-first frontier expansion over set families**:

1. Forward pass (`get_reconf_seq`): starting from the singleton family `{s}`, repeatedly expand by one move (`_one_move`) and intersect with the effective search space of valid states. This builds `setset_seq`, a list where `setset_seq[i]` is the family of all valid states reachable from `s` in exactly `i` moves. Stop when `t` appears, or when the frontier stops growing (`setset_seq[-2] == setset_seq[-1]`) meaning `t` is unreachable (return `[]`).
2. Backward pass (`_get_seq`): walk back from `t`, at each level intersecting the predecessor family with the move-neighbors of the current state and picking any one (`.choice()`), reconstructing a concrete sequence.

The forward pass itself lives in the shared helper `_forward_bfs(s, search_space, effective_space, model, stop)`, which expands the frontier one move at a time and returns `(setset_seq, stopped)` — stopping either when the `stop` callback fires (early stop) or when a new frontier adds no unseen state (saturation). `get_reconf_seq` drives it with `stop = lambda ss: t in ss`.

**Single-start "farthest state" query.** `get_longest_shortest_seq(s, search_space, model='tj', lower=None, upper=None)` takes only a start `s` (no `t`, no `k`) and returns a shortest sequence to a state whose shortest-move distance from `s` is maximal — the *eccentricity* of `s`. It shares `_forward_bfs` but never stops early: it expands to saturation, then scans the cumulative reached set to find the last level at which a genuinely new state appears (for `tar`, earlier states reappear by size parity, so a plain "last non-empty frontier" is wrong), picks any state at that level as `t` (`.choice()`), and reconstructs with `_get_seq`. Emptiness of the per-level "new" family is tested with truthiness (`if new:`), not `len()`, because `len()` overflows on astronomically large ZDD families. If `s` cannot move at all it returns `[s]`. Both `tj` and `tar` (with `lower`/`upper`) are supported; the `tar` size validation and effective-space construction are factored into `_effective_space`, shared with `get_reconf_seq`.

**The state-type / model dispatch is centralized in two helpers** so the forward pass, the seed construction, and `_get_seq` all share it:
- `_singleton(state, search_space)` builds the singleton family `{state}` of the right graphillion type.
- `_one_move(family, search_space, model)` returns the one-move neighborhood, branching on both the type (`GraphSet` / `VertexSetSet` / `setset`) and the model.

The supported models are:
- `'tj'` (token jumping): remove one element and add one, keeping cardinality fixed. Uses `remove_add_some_edges()` / `remove_add_some_vertices()` / `remove_add_some_elements()`.
- `'tar'` (token addition/removal): add one element **or** remove one (cardinality changes by ±1). Uses `add_some_*() | remove_some_*()`.

Any new state type or move operator only needs to be added to these two helpers.

**The `tar` size bounds.** `tar` takes keyword args `lower`/`upper` (each may be `None`). Because the direction of the size constraint is problem-dependent (independent sets need a *lower* bound, dominating sets an *upper* bound), reconfillion does not hardcode a direction: it intersects the search space with the size range `[lower, upper]` via `_restrict_size` (using `larger`/`smaller`, which exist on all three types) to form the *effective* search space, and the move-and-intersect step naturally discards any state that leaves the range. `s` and `t` must lie within the range or `get_reconf_seq` raises `ValueError`; unlike `tj`, `|s|` and `|t|` may differ. The `k` parameter remains a placeholder (unused by both models).

## Conventions from graphillion

- An edge is a tuple of two vertices; a graph/state is a *list of edges* (or elements/vertices).
- Before building a `GraphSet`/`VertexSetSet`, the universe must be set (`GraphSet.set_universe(graph)`); callers are responsible for this.

## Development

There is no build step or linter configured in this repo. A pytest suite lives in `tests/` and tests the `tj` model (`test_tj_benchmark.py`), the `tar` model (`test_tar_benchmark.py`), and the single-start `get_longest_shortest_seq` query (`test_longest_shortest_benchmark.py`) against independent set reconfiguration instances bundled in `tests/data/` (a subset of the Core Challenge 2022 benchmark, https://github.com/core-challenge/2022benchmark; see `tests/data/README.md`); run it with `pip install -e ".[test]"` then `pytest -s tests/`. The `tar` tests reuse the same instances two ways: with size range `[k-1, k]` (where reachability must match `tj`, since a `tj` move is a `tar` drop-then-add within that range) and with `[k, ∞)` (standard TAR(k), validity only). The `test_longest_shortest_benchmark.py` tests run `tj` and `tar` `[k, ∞)`, checking sequence validity, that the returned tail is reached optimally (matching `get_reconf_seq`'s length), and that the farthest distance found is at least the distance to the benchmark's own goal. You can also exercise the code by installing graphillion and running the README tutorial flow. The package is published to PyPI; version lives in `pyproject.toml`.

Note: there is a graphillion bug where, after the vertex universe is shrunk then regrown beyond its previously-realized maximum in one process (e.g. `set_universe` 7 → 6 → 14, with operations at each size), `set_universe` updates the Python object table correctly but the C++ ZDD variable table stays out of sync — `remove_add_some_vertices` then omits the top vertex, and `get_reconf_seq` raises `KeyError("'choice' from an empty set")` in its backward pass. This is not a stale-object issue (reconfillion creates all objects after the fresh `set_universe`). The test suite works around it by solving each instance in its own subprocess (`tests/benchmark_loader.py: solve_isolated`).
