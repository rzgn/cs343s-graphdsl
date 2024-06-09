"""
Classes representing graphs and FSMs, for creating and displaying diagrams.
"""

from dataclasses import dataclass
import os
from typing import NamedTuple, Optional, Union

import dot2tex as d2t
from numpy import cos, sin, pi


class Edge(NamedTuple):
    """An edge in a Diagram from src to dst with an optional label."""
    src: Union[int, str]
    dst: Union[int, str]
    label: Optional[str]


class FSMShape:
    """A layout of nodes in an FSM."""
    pass


@dataclass
class FSMCircle(FSMShape):
    """A circular layout.

    If the radius isn't provided, it is determined by the number of nodes."""
    radius: int = 0

    def __post_init__(self):
        if self.radius < 0:
            raise ValueError(f"FSMCircle radius must be at least 0, not {self.radius}")


@dataclass
class FSMRect(FSMShape):
    """A rectangular layout.

    The number of rows is determined by the total number of nodes and the provided number of columns.
    """
    cols: int
    spacing: int = 100 # in bp

    def __post_init__(self):
        if self.cols < 1:
            raise ValueError(f"FSMRect columns must be at least 1, not {self.cols}")
        if self.spacing < 1:
            raise ValueError(f"FSMRect spacing must be at least 1, not {self.spacing}")


class Diagram:
    """Base class for a diagram, providing shared methods."""

    TEX_PREAMBLE = r"""
    \documentclass{standalone}
    \usepackage[utf8]{inputenc}
    \usepackage{tikz}
    \usetikzlibrary{snakes,arrows,shapes,automata,positioning}
    \usepackage{amsmath}
    \tikzset{double distance=2pt}
    \usepackage[active,tightpage]{preview}
    \PreviewEnvironment{tikzpicture}
    \setlength\PreviewBorder{0pt}
    \begin{document}
    """

    TEX_POSTSCRIPT = r"""
    \end{document}
    """

    edges: set[Edge]

    def __post_init__(self) -> None:
        """Convert provided edges into Edges."""
        new_edges = set()
        for e in self.edges:
            if len(e) == 2:   # no label
                new_edges.add(Edge(e[0], e[1], None))
            elif len(e) == 3: # has label
                new_edges.add(Edge(e[0], e[1], e[2]))
            else:
                raise ValueError("Diagram edges should have length 2 or 3")
        self.edges = new_edges

    def to_tex(self, shape: Optional[FSMShape]=None) -> str:
        r"""Return this graph as a `standalone` LaTeX document."""
        pass

    def output_tex(self, filename: str, preview: bool=False, shape: Optional[FSMShape]=None) -> None:
        """Write this graph in LaTeX form to [filename].tex.

        Arguments:
        filename: Write the result to [filename].tex.
        preview: If true, also convert the result to a PDF [filename].pdf and open it.
        """
        with open(f"{filename}.tex", "w") as f:
            f.write(self.to_tex(shape))
        if preview:
            os.system(f"pdflatex {filename}.tex; open {filename}.pdf")

    def __rshift__(self, other: str):
        other = other.lower()
        with open(other, "w") as f:
            if other.endswith(".tex") and hasattr(self, "to_tex"):
                f.write(self.to_tex())
            elif other.endswith(".dot") or other.endswith(".gv") and hasattr(self, "to_dot"):
                f.write(self.to_dot())
            else:
                raise NotImplementedError(f"Don't know how to write to file {other}")


@dataclass
class FSM(Diagram):
    """A Finite State Machine."""
    edges: set[Edge]
    state_labels: list[str]
    q_0: int
    q_accept: set[int]

    def __post_init__(self):
        """Check that all references to states are valid."""
        super().__post_init__()
        num_nodes = len(self.state_labels)
        if self.q_0 >= num_nodes:
            raise ValueError(f"Got {num_nodes} labels, but start state is {self.q_0}.")
        for q in self.q_accept:
            if q >= num_nodes:
                raise ValueError(f"Got {num_nodes} labels, but an accept state is {q}.")
        for e in self.edges:
            if e[0] >= num_nodes or e[1] >= num_nodes:
                raise ValueError(f"Got {num_nodes} labels, but an edge contains {q}.")

    def to_tex(self, shape: Optional[FSMShape]=None):
        result = self.TEX_PREAMBLE + r"\begin{tikzpicture}[>=stealth']" + "\n"

        # Add the nodes
        num_nodes = len(self.state_labels)

        # Ideally this code could be a method on the FSMShape object
        if isinstance(shape, FSMCircle):
            radius = shape.radius or 10 * num_nodes
            for i, label in enumerate(self.state_labels):
                # Calculate the position in polar coordinates, then convert to cartesian
                angle = i * 2 * pi / num_nodes
                x = radius * sin(angle)
                x_rounded = "{:0.2f}bp".format(x)
                y = radius * cos(angle)
                y_rounded = "{:0.2f}bp".format(y)

                options = "draw,circle,double" if i in self.q_accept else "draw,circle"
                result += fr"\node ({i}) at ({x_rounded},{y_rounded}) [{options}] {{${label}$}};" + "\n"

                # Add an arrow pointing to the start state
                if i == self.q_0:
                    start_y_rounded = "{:0.2f}bp".format(y + radius // 2)
                    result += fr"\node (start) at ({x_rounded}, {start_y_rounded}) {{start}};" + "\n"
                    result += f"\draw [->] (start) -- ({i});\n"
        elif isinstance(shape, FSMRect):
            cols = shape.cols
            for i, label in enumerate(self.state_labels):
                x = (i % cols) * shape.spacing
                y = -((i // cols) * shape.spacing)
                options = "draw,circle,double" if i in self.q_accept else "draw,circle"
                result += fr"\node ({i}) at ({x}bp,{y}bp) [{options}] {{${label}$}};" + "\n"

                # Add an arrow pointing to the start state
                if i == self.q_0:
                    start_y_rounded = "{:0.2f}bp".format(y + shape.spacing // 2)
                    result += fr"\node (start) at ({x}bp, {start_y_rounded}) {{start}};" + "\n"
                    result += f"\draw [->] (start) -- ({i});\n"
        else:
            raise NotImplementedError(f"Unimplemented FSMShape: {type(shape)}")

        # Add the edges and labels
        for src, dst, label in self.edges:
            label = label or ""
            if src != dst:
                # if different nodes, use a straight line
                edge = f"\draw [->] ({src}) -- ({dst})"
                edge += " node[midway] {" + label + "}"
            else:
                # if same node, use a self-loop
                edge = f"\draw ({src}) edge[loop above] node {{{label}}} ({src})"
            result += edge + ";\n"

        result += "\end{tikzpicture}\n" + self.TEX_POSTSCRIPT

        return result

@dataclass
class Digraph(Diagram):
    """A digraph."""
    edges: set[Edge]

    def edge_to_dot(self, edge):
        output = f"{edge[0]} -> {edge[1]}"  # For an undirected graph, use --
        if len(edge) == 3:
            output += f' [label="{edge[2]}"]'
        return output

    def to_dot(self):
        """Return this graph formatted as a DOT string."""
        if not self.edges:
            return ""

        output = "digraph {\n"
        output += '    node [texmode="math"];\n'
        for edge in self.edges:
            output += "    " + self.edge_to_dot(edge) + ";\n"
        output += "}"

        return output

    def to_tex(self, shape: Optional[FSMShape]=None) -> str:
        r"""Return this graph as a `standalone` LaTeX document."""
        if shape:
            raise ValueError("Cannot display a digraph using a FSMShape.")
        dot = self.to_dot()
        tex = d2t.dot2tex(dot, format='tikz', crop=True)
        return tex
