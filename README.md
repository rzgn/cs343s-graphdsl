# GraphDSL

GraphDSL provides a simple interface to _represent_ and _output diagrams of_ directed graph-like structures within Python. Currently supported are digraphs and FSMs.

## Using GraphDSL to represent a digraph

[The dot2tex package](https://dot2tex.readthedocs.io/en/latest/) is required.

To create a new digraph, instantiate a `Digraph` object. The `edges` constructor argument can be a set of tuples. A 2-tuple represents an edge in the graph: (source node, destination node). Nodes can be designated as integers or as strings which can serve as identifiers in DOT. Node designations must be unique.

```
unlabeled_edges = {(0, 0), (0, 1), (1, 1)}
d = Digraph(unlabeled_edges)
```

The optional third element represents a label for the edge:
```
labeled_edges = {(0, 0, "one self-loop"), (0, 1, "an edge"), (1, 1, "another self-loop")}
d = Digraph(unlabeled_edges)
```

After creating the digraph, it can be output to the `dot` or `tex` file formats with the >> operator:
```
d >> "filename.dv"
# equivalent to:
# with open("filename.dv", "w") as f:
#     f.write(d.to_dot())
```

Or to a .tex file. The layout is generated via dot2tex, so it cannot be customized from code.
```
d >> "filename.tex"
# equivalent to:
# d.output_tex("filename")
```

For rapid iteration, passing in the `preview` parameter will convert a .tex file to pdf and also open it.
```
d.output_tex("filename", preview=True)
```


## Using GraphDSL to represent a FSM

To create a new FSM, instantiate the `FSM` class. The required arguments are: 
- edges, which are as described in the digraph section, but are restricted to numeric identifiers for nodes;
- state_labels, 
- q_0, the numeric identifier for the starting state;
- q_accept, a set of numeric identifiers for accepting states

For example:
```
edges = {(0, 0), (0, 1), (1, 1)}
state_labels = ["first", "second"]
q_0 = 0
q_accept = {0, 1}
f = FSM(edges, state_labels, q_0, q_accept)
```

After creating the FSM, it can be output to .tex format with more customization options than the digraph. A FSMShape parameter, which represents the layout of the nodes, is required. Currently they can be laid out in a regular n-gon (placed counterclockwise by identifier, starting at 12 o'clock on a circle) or in a rectangle (placed row-wise then column-wise, with the specified number of columns).
```
f.output_tex("filename", shape=FSMCircle())
f.output_tex("filename", shape=FSMCircle(radius=100), preview=True)
f.output_tex("filename", shape=FSMRect(cols=3))
```


## More advanced examples

Any Python constructs can be used to create the set of edges, state labels, etc. This allows for the creation of digraphs and FSMs that would be difficult to lay out manually.

Drawing a graph with all possible edges on 100 nodes:
```
edges = { (i, j) for i in range(100) for j in range(100) }
d = Digraph(edges)
d >> "complete.gv"
```

Drawing an FSM with 50 labeled states:
```
edges = { (i, i + 1) for i in range(49) }
state_labels = [f"q_{{{n}}}" for n in range(50)]
q_accept = { n for n in range(50) if n % 2 == 1}
f = FSM(edges, state_labels, 0, q_accept)
f.output_tex("big_circle", preview=False, shape=FSMCircle())
```
