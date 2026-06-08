"""Tests for ``get_longest_shortest_seq`` on the 2022benchmark instances.

``get_longest_shortest_seq`` takes only a start state ``s`` and returns a
shortest reconfiguration sequence to a *farthest* reachable state (a state whose
shortest-move distance from ``s`` is maximal). We exercise it on the bundled
independent-set instances under both models -- ``tj`` and standard ``tar`` with
the size range ``[k, infinity)`` (``k = |s|``) -- and check:

- **Validity**: the sequence starts at ``s``, every consecutive pair is a legal
  move for the model (tj: remove one + add one; tar: symmetric difference 1),
  every state is an independent set, and (for tar) every state has size >= k.
- **Shortestness**: the returned tail ``t`` is reached optimally, i.e.
  ``get_reconf_seq(s, t)`` has the same length as the returned sequence.
- **Lower bound on the distance**: if the benchmark's own goal ``t_bench`` is
  reachable from ``s`` under the same model, the farthest distance found is at
  least the distance to ``t_bench`` (``len(ecc_seq) >= len(dist-to-t_bench)``).

Each instance is solved in its own subprocess (see ``benchmark_loader``) so that
graphillion's global ZDD universe cannot leak between instances.
"""

import pytest

from benchmark_loader import (
    INSTANCES,
    instance_paths,
    is_independent,
    load_col,
    load_dat,
    solve_isolated,
    solve_longest_isolated,
)

# (label suffix, model, lower, upper) for each model variant under test.
_MODELS = [
    ("tj", "tj", None, None),
    ("tar-k-inf", "tar", "k", None),  # lower="k" is resolved to len(s) per instance
]


def _step_is_legal(a, b, model):
    """Return True iff going from state ``a`` to ``b`` is a single legal move."""
    a, b = set(a), set(b)
    if model == "tj":
        # token jumping: remove exactly one, add exactly one.
        return len(a - b) == 1 and len(b - a) == 1
    # tar: add one OR remove one -> symmetric difference of size exactly one.
    return len(a ^ b) == 1


@pytest.mark.parametrize(
    "label, col_relpath, dat_relpath",
    INSTANCES,
    ids=[label for label, _, _ in INSTANCES],
)
@pytest.mark.parametrize(
    "model_label, model, lower_spec, upper",
    _MODELS,
    ids=[m[0] for m in _MODELS],
)
def test_longest_shortest_sequence(
    label, col_relpath, dat_relpath, model_label, model, lower_spec, upper, capsys
):
    col_path, dat_path = instance_paths(col_relpath, dat_relpath)
    n, edges = load_col(col_path)
    s, t_bench = load_dat(dat_path)

    assert is_independent(edges, s), f"{label}: s is not an independent set"
    k = len(s)
    lower = k if lower_spec == "k" else lower_spec

    # Farthest-state sequence from s only.
    seq = solve_longest_isolated(n, edges, s, model=model, lower=lower, upper=upper)

    assert len(seq) >= 1, f"{label}/{model_label}: empty result"
    distance = len(seq) - 1
    with capsys.disabled():
        print(f"{label}/{model_label}: |s|={k} distance={distance} seqlen={len(seq)}")

    # --- Validity -----------------------------------------------------------
    assert set(seq[0]) == set(s), (
        f"{label}/{model_label}: sequence does not start at s "
        f"(got {sorted(seq[0])}, expected {sorted(s)})"
    )
    for i, state in enumerate(seq):
        assert is_independent(edges, state), (
            f"{label}/{model_label}: state #{i} {sorted(state)} is not independent"
        )
        if model == "tar":
            assert len(set(state)) >= lower, (
                f"{label}/{model_label}: state #{i} size {len(set(state))} < lower {lower}"
            )
        else:  # tj preserves cardinality
            assert len(set(state)) == k, (
                f"{label}/{model_label}: state #{i} size {len(set(state))} != k {k}"
            )
    for i in range(len(seq) - 1):
        assert _step_is_legal(seq[i], seq[i + 1], model), (
            f"{label}/{model_label}: step {i}->{i + 1} is not a legal {model} move: "
            f"{sorted(seq[i])} -> {sorted(seq[i + 1])}"
        )

    # --- Shortestness: the tail t is reached optimally ----------------------
    t = seq[-1]
    to_t = solve_isolated(n, edges, s, list(t), model=model, lower=lower, upper=upper)
    assert len(to_t) == len(seq), (
        f"{label}/{model_label}: tail not reached optimally "
        f"(get_reconf_seq len {len(to_t)} != {len(seq)})"
    )

    # --- Lower bound: farthest distance >= distance to the benchmark goal ----
    to_bench = solve_isolated(
        n, edges, s, t_bench, model=model, lower=lower, upper=upper
    )
    if to_bench:  # t_bench reachable under this model
        assert len(seq) >= len(to_bench), (
            f"{label}/{model_label}: farthest distance {distance} is smaller than "
            f"distance to benchmark goal {len(to_bench) - 1}"
        )
