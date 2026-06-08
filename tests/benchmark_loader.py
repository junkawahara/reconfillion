"""Loader for the Core Challenge 2022 benchmark instances used by the tests.

The instance files live under ``tests/data/`` and are a small subset copied from
the Core Challenge 2022 benchmark repository:
https://github.com/core-challenge/2022benchmark (see ``tests/data/README.md``).

Each instance is given by a pair of files:

- ``<name>.col``: the graph in DIMACS-like format.
  - ``p <n> <m>``  : declares ``n`` vertices (numbered 1..n) and ``m`` edges.
  - ``e <u> <v>``  : an undirected edge.
  - ``c ...``      : a comment line (ignored).
- ``<name>_<id>.dat``: a reconfiguration instance.
  - ``s <v> <v> ...`` : the start independent set.
  - ``t <v> <v> ...`` : the goal independent set.

These benchmarks encode the *independent set reconfiguration* problem.
"""

import multiprocessing
from pathlib import Path

# Instance files copied into the test tree (see tests/data/README.md).
BENCHMARK_ROOT = Path(__file__).resolve().parent / "data"


def load_col(path):
    """Load a ``.col`` graph file.

    Returns a tuple ``(n, edges)`` where ``n`` is the number of vertices
    (vertices are numbered ``1..n``) and ``edges`` is a list of ``(int, int)``
    tuples.
    """
    n = None
    edges = []
    with open(path) as f:
        for line in f:
            tokens = line.split()
            if not tokens:
                continue
            if tokens[0] == "p":
                n = int(tokens[1])
            elif tokens[0] == "e":
                edges.append((int(tokens[1]), int(tokens[2])))
            # 'c' and any other lines are ignored.
    return n, edges


def load_dat(path):
    """Load a ``.dat`` reconfiguration instance.

    Returns a tuple ``(s, t)`` of integer vertex lists for the start and goal
    independent sets.
    """
    s = None
    t = None
    with open(path) as f:
        for line in f:
            tokens = line.split()
            if not tokens:
                continue
            if tokens[0] == "s":
                s = [int(v) for v in tokens[1:]]
            elif tokens[0] == "t":
                t = [int(v) for v in tokens[1:]]
    return s, t


# The instances under test: small handcrafted instances plus the smallest grid.
# Each entry is (label, col_relpath, dat_relpath) relative to BENCHMARK_ROOT.
_HANDCRAFTED = [
    "hc-toyyes-01",
    "hc-toyno-01",
    "hc-square-01",
    "hc-square-02",
    "hc-power-11",
    "hc-power-12",
]

INSTANCES = [
    (f"{name}_01", f"handcrafted/{name}.col", f"handcrafted/{name}_01.dat")
    for name in _HANDCRAFTED
] + [
    (
        f"grid004x004_{i:02d}",
        "grid/grid004x004.col",
        f"grid/grid004x004_{i:02d}.dat",
    )
    for i in range(1, 6)
]


def instance_paths(col_relpath, dat_relpath):
    """Resolve an instance's ``.col`` / ``.dat`` paths against BENCHMARK_ROOT."""
    return BENCHMARK_ROOT / col_relpath, BENCHMARK_ROOT / dat_relpath


def _solve_worker(n, edges, s, t, model, lower, upper):
    """Solve one instance and return the reconfiguration sequence.

    Runs in a fresh subprocess (see ``solve_isolated``). ``model`` is ``"tj"``,
    ``"tar"``, or ``"ts"``; ``lower``/``upper`` are the tar size bounds (ignored
    otherwise). For the ts (token sliding) model the underlying graph's ``edges``
    double as the adjacency passed to ``get_reconf_seq`` as ``graph``. The
    returned value is a list of sorted integer vertex lists, picklable across the
    process boundary.
    """
    from graphillion import VertexSetSet
    from reconfillion import reconf

    VertexSetSet.set_universe(list(range(1, n + 1)))
    independent_sets = VertexSetSet.independent_sets(edges)
    graph = edges if model == "ts" else None
    seq = reconf.get_reconf_seq(
        s, t, independent_sets, model=model, lower=lower, upper=upper, graph=graph
    )
    return [sorted(state) for state in seq]


def solve_isolated(n, edges, s, t, model="tj", lower=None, upper=None):
    """Run ``_solve_worker`` in a fresh ('spawn') subprocess and return its result.

    graphillion keeps its ZDD universe in *global* mutable state. Repeatedly
    calling ``VertexSetSet.set_universe`` with different universes in one process
    (i.e. solving several instances back-to-back) can corrupt that state and make
    ``get_reconf_seq`` raise ``KeyError("'choice' from an empty set")`` -- a
    graphillion-level bug, not a reconfillion one. Solving each instance in its
    own process gives every instance a clean universe, so the tests stay
    reliable regardless of run order.

    ``model`` selects ``"tj"`` (token jumping), ``"tar"`` (token
    addition/removal), or ``"ts"`` (token sliding, using ``edges`` as the
    adjacency); ``lower``/``upper`` bound the tar state size.
    """
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(1) as pool:
        return pool.apply(_solve_worker, (n, edges, s, t, model, lower, upper))


def _longest_worker(n, edges, s, model, lower, upper):
    """Solve ``get_longest_shortest_seq`` for one instance from start ``s`` only.

    The mirror of ``_solve_worker`` for the single-start "farthest state" query.
    Runs in a fresh subprocess (see ``solve_longest_isolated``) and returns a
    list of sorted integer vertex lists, picklable across the process boundary.
    """
    from graphillion import VertexSetSet
    from reconfillion import reconf

    VertexSetSet.set_universe(list(range(1, n + 1)))
    independent_sets = VertexSetSet.independent_sets(edges)
    graph = edges if model == "ts" else None
    seq = reconf.get_longest_shortest_seq(
        s, independent_sets, model=model, lower=lower, upper=upper, graph=graph
    )
    return [sorted(state) for state in seq]


def solve_longest_isolated(n, edges, s, model="tj", lower=None, upper=None):
    """Run ``_longest_worker`` in a fresh ('spawn') subprocess and return its result.

    Same per-instance process isolation as ``solve_isolated`` (graphillion keeps
    its ZDD universe in global mutable state); see ``solve_isolated`` for the
    rationale.
    """
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(1) as pool:
        return pool.apply(_longest_worker, (n, edges, s, model, lower, upper))


def is_independent(edges, vertices):
    """Return True iff ``vertices`` is an independent set under ``edges``.

    Recomputed directly from the edge list (independent of graphillion), so it
    can validate the search space as well as each reconfiguration step.
    """
    vset = set(vertices)
    for u, v in edges:
        if u in vset and v in vset:
            return False
    return True
