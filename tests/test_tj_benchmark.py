"""Tests for the token-jumping (tj) model on the 2022benchmark instances.

The 2022benchmark (Core Challenge 2022) encodes *independent set
reconfiguration*. Its YES/NO labels are for the **Token Sliding** rule, whereas
reconfillion implements **Token Jumping (tj)**. Since the two rules can disagree,
these tests do NOT compare against the benchmark labels. Instead, for each
instance we run ``get_reconf_seq`` under ``model='tj'`` and verify that whatever
sequence it returns is *valid*:

- it connects ``s`` and ``t`` (endpoints match, in either order),
- every state has the same cardinality as ``s`` (token jumping preserves size),
- every consecutive pair is a legal tj move (remove one, add one), and
- every state is an independent set (recomputed from the edge list).

An empty result is treated as "unreachable" and passes without sequence
validation.
"""

import pytest

from benchmark_loader import (
    INSTANCES,
    instance_paths,
    is_independent,
    load_col,
    load_dat,
    solve_isolated,
)


@pytest.mark.parametrize(
    "label, col_relpath, dat_relpath",
    INSTANCES,
    ids=[label for label, _, _ in INSTANCES],
)
def test_tj_reconf_sequence(label, col_relpath, dat_relpath, capsys):
    col_path, dat_path = instance_paths(col_relpath, dat_relpath)
    n, edges = load_col(col_path)
    s, t = load_dat(dat_path)

    # Preconditions for token jumping: equal cardinality and both endpoints are
    # independent sets in the graph.
    assert len(s) == len(t), f"{label}: |s| ({len(s)}) != |t| ({len(t)})"
    assert is_independent(edges, s), f"{label}: s is not an independent set"
    assert is_independent(edges, t), f"{label}: t is not an independent set"

    # Solve under the tj model. Each instance runs in its own process so that
    # graphillion's global universe state cannot leak between instances; see
    # benchmark_loader.solve_isolated for details.
    seq = solve_isolated(n, edges, s, t)

    reachable = len(seq) > 0
    with capsys.disabled():
        print(f"{label}: |s|={len(s)} reachable={reachable} seqlen={len(seq)}")

    if not reachable:
        # Unreachable under tj: nothing to validate (treated as PASS).
        return

    # Endpoints connect s and t (robust to the direction picked by .choice()).
    endpoints = {frozenset(seq[0]), frozenset(seq[-1])}
    assert endpoints == {frozenset(s), frozenset(t)}, (
        f"{label}: endpoints {endpoints} do not match "
        f"{{{frozenset(s)}, {frozenset(t)}}}"
    )

    k = len(s)
    for i, state in enumerate(seq):
        # Same cardinality throughout (token jumping preserves size).
        assert len(set(state)) == k, (
            f"{label}: state #{i} has size {len(set(state))}, expected {k}"
        )
        # Each state is an independent set, recomputed from the edge list.
        assert is_independent(edges, state), (
            f"{label}: state #{i} {sorted(state)} is not an independent set"
        )

    # Each consecutive pair is a legal tj move: exactly one removed + one added.
    for i in range(len(seq) - 1):
        a = set(seq[i])
        b = set(seq[i + 1])
        assert len(a - b) == 1 and len(b - a) == 1, (
            f"{label}: step {i}->{i + 1} is not a single token jump: "
            f"removed={sorted(a - b)}, added={sorted(b - a)}"
        )
