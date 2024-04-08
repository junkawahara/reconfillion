# Reconfillion - Python interface for combinatorial reconfiguration problems

Reconfillion was released as version 1.0.0 on April 8, 2024. The older version of reconfillion prior to that date exist on https://github.com/junkawahara/reconfillion-kari , but are not compatible with this version.

Reconfillion is a tool for solving combinatorial reconfiguration problems. It works with [graphillion](https://github.com/takemaru/graphillion), which means that combinatorial reconfiguration problems of graph classes that are supported by graphillion can be solved by reconfillion.

## Requirements

* Graphillion version [v1.7rc](https://github.com/takemaru/graphillion/tree/v1.7rc) is needed. Since v1.7rc is the latest version and has not been registered into PyPI yet, you need to build it manually.

## License

MIT License

## Install

First, clone and install Graphillion version [v1.7rc](https://github.com/takemaru/graphillion/tree/v1.7rc),

```
git clone -b v1.7rc https://github.com/takemaru/graphillion.git
```

and build it according to the [instruction](https://github.com/takemaru/graphillion/tree/v1.7rc?tab=readme-ov-file#installing-from-source).

Then, clone and install reconfillion:

```
git clone https://github.com/junkawahara/reconfillion.git
cd reconfillion
pip install .
```

## Tutorial

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

Then, by doing the following method, we can obtain the reconfiguration sequence between s and t.

```
s = [(1, 2), (1, 3), (1, 4)] # start spanning tree
t = [(1, 4), (2, 4), (3, 4)] # goal spanning tree

# obtain a reconfiguration sequence between s and t under the token jumping model.
reconf_sequence = reconf.get_reconf_seq(s, t, spanning_trees, model = 'tj')

# obtained [[(1, 4), (2, 4), (3, 4)], [(1, 2), (1, 4), (2, 4)], [(1, 2), (1, 3), (1, 4)]]
```

## Note

This software (and graphillion) needs a lot of memory to solve problems with large size instances.
