#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import partial
from itertools import starmap, zip_longest
import sys
from typing import Callable, Hashable, Iterable, List
from uuid import uuid4

import matplotlib.pyplot as plt
from matplotlib import rc_context
import networkx as nx
import pandas as pd

PROJECTS_FILE="/home/c/Projects/libraries_io/data/libraries-1.6.0-2020-01-12/projects-1.6.0-2020-01-12.csv"
PYPI_PROJECTS_FILE="pypi-projects.csv"


def subset_projects_file_to_pypi_projects(
    df: pd.DataFrame,
    filename: str = PROJECTS_FILE,
    column_name: str = "Platform",
    column_value: str = "Pypi",
    columns_to_keep: List = None
) -> pd.DataFrame:
    df_subset: pd.DataFrame = df.loc[df.loc[:, column_name] == column_value, ]
    if columns_to_keep is None:
        return df_subset
    else:
        return df_subset.loc[:, columns_to_keep]


def write_pypi_projects_to_csv(
    df: pd.DataFrame,
    filename: str = PYPI_PROJECTS_FILE,
    include_index: bool = False
) -> None:
    df.to_csv(filename, index=include_index)
    return


def add_node_to_graph(
    graph: nx.Graph,
    node: Hashable,
    **kwargs
) -> None:
    graph.add_node(node, **kwargs)
    return


def main(argv=None):
    if argv is None:
        argv: List = sys.argv

    print("Initialize directed graph\n", file=sys.stderr)
    G: nx.DiGraph = nx.DiGraph()
    print("Create nodes for PyPi and Python\n", file=sys.stderr)
    pypi_uuid, python_uuid = (uuid4(), uuid4())
    print("Add nodes for PyPi and Python to directed graph\n", file=sys.stderr)
    G.add_node(pypi_uuid, label="Platform", name="PyPi")
    G.add_node(python_uuid, label="Language", name="Python")
    print("Add 'HAS_DEFAULT_LANGUAGE' edge from PyPi to Python\n", file=sys.stderr)
    G.add_edge(pypi_uuid, python_uuid, label="HAS_DEFAULT_LANGUAGE")

    # Get CSV data into pandas and subset to just PyPi
    print(f"Read CSV '{PROJECTS_FILE}' into pandas DataFrame\n", file=sys.stderr)
    projects: pd.DataFrame = pd.read_csv(PROJECTS_FILE, low_memory=False)
    print(f"Subset DataFrame to just PyPi projects, 'ID' and 'Name' columns\n", file=sys.stderr)
    pypi_projects: pd.DataFrame = subset_projects_file_to_pypi_projects(
        projects,
        columns_to_keep = ["ID", "Name"]
    )
    
    # Now that the graph is initialized, curry functions taking it as an argument
    add_project_nodes_to_graph: Callable = lambda node_id, name, graph=G: \
        add_node_to_graph(graph, node_id, label="Project", name=name)
    
    add_pypi_node_to_project_nodes_edges: Callable= \
        partial(G.add_edge, label="HOSTS")

    print("Prepare values to be added to graph\n", file=sys.stderr)
    pypi_project_nodes_to_add_to_graph: Iterable = pypi_projects.iloc[0:100, ].values
    
    print("Add nodes with label 'Project' to the Directed Graph\n", file=sys.stderr)
    tuple(
        starmap(add_project_nodes_to_graph, pypi_project_nodes_to_add_to_graph)
    )
            
    print("Add edges between node of label 'Platform' and nodes of label "
          "'Project' with attribute 'HOSTS'\n", file=sys.stderr)
    ebunch_to_add: Iterable = zip_longest(
        (pypi_uuid, ),
        pypi_project_nodes_to_add_to_graph.transpose()[0],
        fillvalue=pypi_uuid
    )
    G.add_edges_from(ebunch_to_add=ebunch_to_add, label="HOSTS")
    
    print("Display the graph with matplotlib", file=sys.stderr)
    with rc_context(rc={'interactive': False}):
        pos = nx.spring_layout(G, seed=3068)  # Seed layout for reproducibility
        nx.draw(G, pos=pos, with_labels=True)
        # nx.draw_networkx(G)
        plt.show()
    

if __name__ == "__main__":
    main()
