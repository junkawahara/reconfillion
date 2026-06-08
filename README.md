# Reconfillion - Python interface for combinatorial reconfiguration problems

Reconfillion was released as version 1.0.0 on April 22, 2024. The older version of reconfillion before that date exists on https://github.com/junkawahara/reconfillion-kari , but is not compatible with this version.

Reconfillion is a tool for solving combinatorial reconfiguration problems. It works with [graphillion](https://github.com/takemaru/graphillion), which means that combinatorial reconfiguration problems of graph classes that are supported by graphillion can be solved by reconfillion.

## Requirements

* Python 3.9 or higher.
* [Graphillion version v1.7 or higher](https://github.com/takemaru/graphillion/) is needed.

## License

MIT License

## Quick install

You can install reconfillion via pip.

```
pip install reconfillion
```

## Tutorial

A *combinatorial reconfiguration problem* asks, given a start state `s` and a
goal state `t` (each a subset of elements such as edges or vertices) drawn from a
search space of valid states, for a step-by-step *reconfiguration sequence* that
transforms `s` into `t` so that every intermediate state is valid and consecutive
states differ by a single legal *move*. What counts as a move is decided by the
chosen **model**; reconfillion supports token jumping (`tj`), token
addition/removal (`tar`), and token sliding (`ts`).

Let's consider to solve the spanning tree reconfiguration problem.
In reconfillion (and graphillion), an edge is represented by a tuple of two vertices, and a graph is represented by a list of edges.

```
# complete graph with 4 vertices [1, 2, 3, 4]
graph = [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]
```

We import graphillion and reconfillion, and make
GraphSet of all the spanning trees on the graph.

```
from graphillion import GraphSet
from reconfillion import reconf

GraphSet.set_universe(graph) # See the graphillion manual.
spanning_trees = GraphSet.trees(is_spanning = True)
```

### Token jumping (`tj`)

Under the **token jumping** model a single move *removes* one token and *adds*
one token at the same time, so the size of the state stays fixed (`|s|` must
equal `|t|`). Thinking of each element in a state as a token, one move picks up a
token and drops it anywhere else, as long as the resulting state is still valid.

By doing the following method, we can obtain the reconfiguration sequence
between `s` and `t`.

```
s = [(1, 2), (1, 3), (1, 4)] # start spanning tree
t = [(1, 4), (2, 4), (3, 4)] # goal spanning tree

# obtain a reconfiguration sequence between s and t under the token jumping model.
reconf_sequence = reconf.get_reconf_seq(s, t, spanning_trees, model = 'tj')

# obtained [[(1, 4), (2, 4), (3, 4)], [(1, 2), (1, 4), (2, 4)], [(1, 2), (1, 3), (1, 4)]]
```

The returned list is a shortest sequence: consecutive spanning trees differ by
exactly one swapped edge, and the first/last entries are `t`/`s`. If `t` is
unreachable from `s`, `get_reconf_seq` returns `[]`.

### Token addition/removal (`tar`)

Under the **token addition/removal** model a single move *adds* one token or
*removes* one token, so the size of the state changes by one each step (and `s`
and `t` may even have different sizes). To keep states meaningful you bound the
state size with the keyword arguments `lower` and `upper`: every intermediate
state must have size within `[lower, upper]`. Use a lower bound for problems
whose feasible states are downward closed (e.g. independent sets, where you must
keep at least `k` tokens) and an upper bound for upward-closed problems (e.g.
dominating sets). Either bound may be `None`, meaning "no bound in that
direction".

```
from graphillion import VertexSetSet

VertexSetSet.set_universe()
independent_sets = VertexSetSet.independent_sets(graph)

s = [1, 3] # start independent set
t = [2, 4] # goal independent set

# reconfigure under token addition/removal, keeping the size in [1, 2].
reconf_sequence = reconf.get_reconf_seq(
    s, t, independent_sets, model = 'tar', lower = 1, upper = 2)
```

If `s` or `t` has a size outside `[lower, upper]`, `get_reconf_seq` raises
`ValueError`.

### Token sliding (`ts`)

Under the **token sliding** model a single move slides one token along an edge
to an *adjacent* vertex, keeping the state size fixed (so `|s|` must equal
`|t|`). Adjacency cannot be derived from the search space alone, so the `ts`
model requires a `graph` argument: a list of `(a, b)` pairs of adjacent
elements. For independent set reconfiguration this is simply the underlying
graph's edges.

```
from graphillion import GraphSet, VertexSetSet

path = [(1, 2), (2, 3), (3, 4), (4, 5)] # path graph 1-2-3-4-5
GraphSet.set_universe(path)
VertexSetSet.set_universe(list(range(1, 6)))
independent_sets = VertexSetSet.independent_sets(path)

s = [1] # start: a single token on vertex 1
t = [5] # goal:  the token on vertex 5

# slide the token along the path; `graph` defines which moves are legal.
reconf_sequence = reconf.get_reconf_seq(
    s, t, independent_sets, model = 'ts', graph = path)

# obtained [{1}, {2}, {3}, {4}, {5}]
```

The token can only step to a neighbour, so unlike token jumping it walks
`1 -> 2 -> 3 -> 4 -> 5` instead of jumping straight to `5`. Omitting `graph` for
`ts` (or passing it for any other model) raises `ValueError`.

### Farthest state from a single start (`get_longest_shortest_seq`)

Sometimes you have only a start state `s` and want the *hardest* target to reach
from it: a state whose shortest reconfiguration distance from `s` is as large as
possible (the *eccentricity* of `s` in the move graph). `get_longest_shortest_seq`
takes only `s` (no `t`), explores every state reachable from `s`, picks a
farthest one, and returns a shortest sequence to it.

```
# reuse the spanning trees from the tutorial above
s = [(1, 2), (1, 3), (1, 4)] # start spanning tree

# a shortest sequence from s to one of the farthest spanning trees (tj model).
reconf_sequence = reconf.get_longest_shortest_seq(s, spanning_trees, model = 'tj')

# reconf_sequence[0] == s, and its length - 1 is the farthest distance from s.
```

It supports the same `tj`, `tar`, and `ts` models (`tar` takes the same `lower`
/ `upper` bounds; `ts` takes the same required `graph`). If `s` cannot make a
single legal move, `[s]` is returned.

## Tests

A pytest suite under `tests/` exercises the token jumping (`tj`), token
addition/removal (`tar`), and token sliding (`ts`) models on a small set of
independent set reconfiguration instances bundled in `tests/data/`
(a subset of the [Core Challenge 2022 benchmark](https://github.com/core-challenge/2022benchmark);
see `tests/data/README.md`). Install the test dependencies and run pytest:

```
pip install -e ".[test]"
pytest -s tests/
```

The `-s` flag shows a per-instance summary (reachability and sequence length).

## Note

This software (and graphillion) needs a lot of memory to solve problems with large-size instances.

## Authors

Reconfillion has been developed by Jun Kawahara and Hiroki Yamazaki.

## Acknowledgment

This project is/was partially supported by JSPS KAKENHI Grant Numbers JP18H04091, JP20H05794, and JP23H04383.
