"""Tests for the token-addition/removal (tar) model on the 2022benchmark instances.

The 2022benchmark (Core Challenge 2022) encodes *independent set
reconfiguration*. Under the **tar** rule a single move adds one vertex *or*
removes one vertex, and every intermediate state must keep its size within a
range ``[lower, upper]``. For each instance (with ``k = |s| = |t|``) we run two
configurations:

1. ``lower=k-1, upper=k`` -- the classic result that two size-``k`` independent
   sets are tar-reachable in this range iff they are **token-jumping** reachable.
   We cross-check tar reachability against the tj solution and validate the
   returned sequence (each state independent, size in ``{k-1, k}``, each move a
   single add/remove).

2. ``lower=k, upper=None`` -- the standard TAR(k) model with no upper bound. tar
   reachability here differs from tj, so we only validate that whatever sequence
   is returned is itself valid (endpoints, independence, size ``>= k``, single
   add/remove per step).

An empty result is treated as "unreachable" and passes without sequence
validation. As with the tj tests, each instance is solved in its own subprocess
to keep graphillion's global universe state from leaking between instances.
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


def _validate_sequence(label, seq, s, t, edges, lower, upper):
    """Assert ``seq`` is a valid tar sequence between ``s`` and ``t``."""
    # Endpoints connect s and t (robust to the direction picked by .choice()).
    endpoints = {frozenset(seq[0]), frozenset(seq[-1])}
    assert endpoints == {frozenset(s), frozenset(t)}, (
        f"{label}: endpoints {endpoints} do not match "
        f"{{{frozenset(s)}, {frozenset(t)}}}"
    )

    for i, state in enumerate(seq):
        size = len(set(state))
        if lower is not None:
            assert size >= lower, (
                f"{label}: state #{i} has size {size} < lower {lower}"
            )
        if upper is not None:
            assert size <= upper, (
                f"{label}: state #{i} has size {size} > upper {upper}"
            )
        # Each state is an independent set, recomputed from the edge list.
        assert is_independent(edges, state), (
            f"{label}: state #{i} {sorted(state)} is not an independent set"
        )

    # Each consecutive pair is a legal tar move: a single add or remove, i.e. the
    # symmetric difference of the two states has exactly one element.
    for i in range(len(seq) - 1):
        a = set(seq[i])
        b = set(seq[i + 1])
        assert len(a ^ b) == 1, (
            f"{label}: step {i}->{i + 1} is not a single add/remove: "
            f"removed={sorted(a - b)}, added={sorted(b - a)}"
        )


@pytest.mark.parametrize(
    "label, col_relpath, dat_relpath",
    INSTANCES,
    ids=[label for label, _, _ in INSTANCES],
)
def test_tar_equivalent_to_tj(label, col_relpath, dat_relpath, capsys):
    """tar with size range [k-1, k] reaches t iff tj does, and the seq is valid."""
    col_path, dat_path = instance_paths(col_relpath, dat_relpath)
    n, edges = load_col(col_path)
    s, t = load_dat(dat_path)

    assert len(s) == len(t), f"{label}: |s| ({len(s)}) != |t| ({len(t)})"
    assert is_independent(edges, s), f"{label}: s is not an independent set"
    assert is_independent(edges, t), f"{label}: t is not an independent set"

    k = len(s)
    lower, upper = k - 1, k

    tj_seq = solve_isolated(n, edges, s, t, model="tj")
    tar_seq = solve_isolated(n, edges, s, t, model="tar", lower=lower, upper=upper)

    tj_reachable = len(tj_seq) > 0
    tar_reachable = len(tar_seq) > 0
    with capsys.disabled():
        print(
            f"{label}: tj_reachable={tj_reachable} "
            f"tar[{lower},{upper}]_reachable={tar_reachable}"
        )

    # The equivalence: size-k independent sets are tar-reachable within [k-1, k]
    # iff they are token-jumping reachable.
    assert tar_reachable == tj_reachable, (
        f"{label}: tar[{lower},{upper}] reachability ({tar_reachable}) "
        f"disagrees with tj ({tj_reachable})"
    )

    if not tar_reachable:
        return

    _validate_sequence(label, tar_seq, s, t, edges, lower, upper)


@pytest.mark.parametrize(
    "label, col_relpath, dat_relpath",
    INSTANCES,
    ids=[label for label, _, _ in INSTANCES],
)
def test_tar_standard_threshold(label, col_relpath, dat_relpath, capsys):
    """Standard TAR(k): size >= k, no upper bound; validate any returned seq."""
    col_path, dat_path = instance_paths(col_relpath, dat_relpath)
    n, edges = load_col(col_path)
    s, t = load_dat(dat_path)

    assert is_independent(edges, s), f"{label}: s is not an independent set"
    assert is_independent(edges, t), f"{label}: t is not an independent set"

    k = min(len(s), len(t))
    lower, upper = k, None

    seq = solve_isolated(n, edges, s, t, model="tar", lower=lower, upper=upper)

    reachable = len(seq) > 0
    with capsys.disabled():
        print(f"{label}: tar[{lower},inf] reachable={reachable} seqlen={len(seq)}")

    if not reachable:
        return

    _validate_sequence(label, seq, s, t, edges, lower, upper)
