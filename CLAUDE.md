# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Reconfillion is a Python tool for solving **combinatorial reconfiguration problems**. Given a start state `s` and goal state `t` (each a subset of elements/edges/vertices) drawn from a search space of *all* valid states, it computes a step-by-step *reconfiguration sequence* transforming `s` into `t` where each step is a single legal move.

The entire implementation is one file: `reconfillion/reconf.py`. `reconfillion/__init__.py` is empty, so the public API is accessed as `from reconfillion import reconf`.

## Architecture

The library is built on top of [graphillion](https://github.com/takemaru/graphillion) (`>=1.7`), whose ZDD-based set families (`setset`, `GraphSet`, `VertexSetSet`) compactly represent astronomically large families of subsets. Reconfillion never enumerates states explicitly — it operates on whole set families at once.

The core algorithm in `get_reconf_seq` is a **breadth-first frontier expansion over set families**:

1. Forward pass (`get_reconf_seq`): starting from the singleton family `{s}`, repeatedly expand by one move (`remove_add_some_*`) and intersect with the `search_space` of valid states. This builds `setset_seq`, a list where `setset_seq[i]` is the family of all valid states reachable from `s` in exactly `i` moves. Stop when `t` appears, or when the frontier stops growing (`setset_seq[-2] == setset_seq[-1]`) meaning `t` is unreachable (return `[]`).
2. Backward pass (`_get_seq`): walk back from `t`, at each level intersecting the predecessor family with the move-neighbors of the current state and picking any one (`.choice()`), reconstructing a concrete sequence.

**The state-type dispatch is the key structural pattern.** The same logic runs over three graphillion types, each with its own one-move operator, branched on via `isinstance`:
- `GraphSet` → `remove_add_some_edges()` (edge subsets, e.g. spanning trees)
- `VertexSetSet` → `remove_add_some_vertices()` (vertex subsets)
- `setset` → `remove_add_some_elements()` (generic element subsets)

This `isinstance` branch is duplicated in three places (the forward expansion, the seed construction, and `_get_seq`). Any new state type or move operator must be added consistently to all three.

The `model` parameter currently only supports `'tj'` (token jumping: remove one element and add one, keeping cardinality fixed). The `model != 'tj'` paths and the `k` parameter are placeholders — adding token-sliding/token-addition models means extending these branches.

## Conventions from graphillion

- An edge is a tuple of two vertices; a graph/state is a *list of edges* (or elements/vertices).
- Before building a `GraphSet`/`VertexSetSet`, the universe must be set (`GraphSet.set_universe(graph)`); callers are responsible for this.

## Development

There is no build step or linter configured in this repo. A pytest suite lives in `tests/` and tests the `tj` model against independent set reconfiguration instances bundled in `tests/data/` (a subset of the Core Challenge 2022 benchmark, https://github.com/core-challenge/2022benchmark; see `tests/data/README.md`); run it with `pip install -e ".[test]"` then `pytest -s tests/`. You can also exercise the code by installing graphillion and running the README tutorial flow. The package is published to PyPI; version lives in `pyproject.toml`.

Note: there is a graphillion bug where, after the vertex universe is shrunk then regrown beyond its previously-realized maximum in one process (e.g. `set_universe` 7 → 6 → 14, with operations at each size), `set_universe` updates the Python object table correctly but the C++ ZDD variable table stays out of sync — `remove_add_some_vertices` then omits the top vertex, and `get_reconf_seq` raises `KeyError("'choice' from an empty set")` in its backward pass. This is not a stale-object issue (reconfillion creates all objects after the fresh `set_universe`). The test suite works around it by solving each instance in its own subprocess (`tests/benchmark_loader.py: solve_isolated`).
