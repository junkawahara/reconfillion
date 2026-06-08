"""Tests for the token-sliding (ts) model on the 2022benchmark instances.

The 2022benchmark (Core Challenge 2022) encodes *independent set
reconfiguration*. Its YES/NO labels are NOT used here: an independent brute-force
check (below) shows they do not correspond to plain cardinality-fixed token
sliding (e.g. ``hc-toyyes`` is reachable under token *jumping* but not under
token *sliding*). So, like the tj/tar tests, this test does not compare against
the benchmark labels.

Instead, for each instance we cross-check ``get_reconf_seq(model='ts')`` against
a small, self-contained reference solver (`_ref_ts`, a plain-Python BFS over the
reachable component with no graphillion involved):

- reachability must agree with the reference, and
- when reachable, reconfillion's sequence must be *shortest* (its length equals
  the reference BFS distance) and a *valid* token-sliding sequence: it connects
  ``s`` and ``t``, every state keeps ``|s|`` and is independent, and every step
  slides exactly one token along an edge to an adjacent vertex.
"""

from collections import deque

import pytest

from benchmark_loader import (
    INSTANCES,
    instance_paths,
    is_independent,
    load_col,
    load_dat,
    solve_isolated,
)


def _adjacency(n, edges):
    adj = {i: set() for i in range(1, n + 1)}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    return adj


def _ref_ts(n, edges, s, t):
    """Reference token-sliding BFS, independent of graphillion.

    Returns ``(reachable, distance)`` where ``distance`` is the shortest number
    of slides from ``s`` to ``t`` (``None`` if unreachable). A slide moves one
    token from a vertex to an adjacent empty vertex, keeping the set independent
    and its cardinality fixed.
    """
    adj = _adjacency(n, edges)

    def independent(state):
        return all(not (adj[u] & state) for u in state)

    start, goal = frozenset(s), frozenset(t)
    seen = {start: 0}
    queue = deque([start])
    while queue:
        cur = queue.popleft()
        if cur == goal:
            return True, seen[cur]
        for u in cur:
            for w in adj[u]:
                if w in cur:
                    continue
                nxt = (cur - {u}) | {w}
                if nxt not in seen and independent(nxt):
                    seen[nxt] = seen[cur] + 1
                    queue.append(nxt)
    return (goal in seen), seen.get(goal)


@pytest.mark.parametrize(
    "label, col_relpath, dat_relpath",
    INSTANCES,
    ids=[label for label, _, _ in INSTANCES],
)
def test_ts_reconf_sequence(label, col_relpath, dat_relpath, capsys):
    col_path, dat_path = instance_paths(col_relpath, dat_relpath)
    n, edges = load_col(col_path)
    s, t = load_dat(dat_path)

    # Preconditions for token sliding: equal cardinality and both endpoints are
    # independent sets in the graph.
    assert len(s) == len(t), f"{label}: |s| ({len(s)}) != |t| ({len(t)})"
    assert is_independent(edges, s), f"{label}: s is not an independent set"
    assert is_independent(edges, t), f"{label}: t is not an independent set"

    # Reference (graphillion-free) answer, and reconfillion's ts answer. Each
    # instance runs in its own process so graphillion's global universe state
    # cannot leak between instances; see benchmark_loader.solve_isolated.
    ref_reachable, ref_dist = _ref_ts(n, edges, s, t)
    seq = solve_isolated(n, edges, s, t, model="ts")

    reachable = len(seq) > 0
    with capsys.disabled():
        print(f"{label}: |s|={len(s)} reachable={reachable} seqlen={len(seq)} "
              f"ref_reachable={ref_reachable} ref_dist={ref_dist}")

    # Reachability must agree with the independent reference solver.
    assert reachable == ref_reachable, (
        f"{label}: ts reachable={reachable}, reference says {ref_reachable}"
    )

    if not reachable:
        # Unreachable under ts: nothing further to validate (treated as PASS).
        return

    # reconfillion returns a *shortest* sequence: its step count matches the BFS
    # distance.
    assert len(seq) - 1 == ref_dist, (
        f"{label}: sequence has {len(seq) - 1} steps, "
        f"reference shortest distance is {ref_dist}"
    )

    # Endpoints connect s and t (robust to the direction picked by .choice()).
    endpoints = {frozenset(seq[0]), frozenset(seq[-1])}
    assert endpoints == {frozenset(s), frozenset(t)}, (
        f"{label}: endpoints {endpoints} do not match "
        f"{{{frozenset(s)}, {frozenset(t)}}}"
    )

    k = len(s)
    for i, state in enumerate(seq):
        # Same cardinality throughout (token sliding preserves size).
        assert len(set(state)) == k, (
            f"{label}: state #{i} has size {len(set(state))}, expected {k}"
        )
        # Each state is an independent set, recomputed from the edge list.
        assert is_independent(edges, state), (
            f"{label}: state #{i} {sorted(state)} is not an independent set"
        )

    # Each consecutive pair is a legal slide: exactly one token moves, along an
    # edge (the vacated vertex is adjacent to the entered one).
    edge_set = {frozenset(e) for e in edges}
    for i in range(len(seq) - 1):
        a = set(seq[i])
        b = set(seq[i + 1])
        removed = a - b
        added = b - a
        assert len(removed) == 1 and len(added) == 1, (
            f"{label}: step {i}->{i + 1} is not a single token move: "
            f"removed={sorted(removed)}, added={sorted(added)}"
        )
        u = next(iter(removed))
        v = next(iter(added))
        assert frozenset((u, v)) in edge_set, (
            f"{label}: step {i}->{i + 1} slides {u}->{v}, "
            f"but ({u}, {v}) is not an edge"
        )
