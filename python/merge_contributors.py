#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools as it
import json
import os
import sys
from collections import defaultdict
from typing import ByteString, Dict, Generator, Iterator, List, Optional, Text, Tuple

from py2neo import Graph, Node, Relationship
from py2neo.database import Cursor

from .utils.utils import chunk, connect, Row

GRAPHDBPASS = 'GRAPHDBPASS'


def get_graph_password(env_variable_name: str = GRAPHDBPASS) -> Optional[str]:
    """ Get graph password that is set as ENV variable
    Args:
        env_variable_name (str): the environment variable to get
    Returns:
        the output of os.environ.get(env_variable_name, None)
    """
    pw = os.environ.get(env_variable_name, None)
    return pw


def execute_cypher_match_statement(g: Graph, statement: str, **kw) -> Cursor:
    """ Return the iterator of query results from `py2neo.Graph.run`
    Args:
        g (py2neo.Graph): the graph object representing DB to interact with
        statement (str): the query to run on `g`
        (kwargs): parameters that are inserted into `statement`
    Returns:
        (py2neo.database.Cursor): query results
    """
    cursor: Cursor = g.run(statement, **kw)
    return cursor


def create_contributor_node(d: Dict, label: str = "Contributor") -> Node:
    """ Using the k, v pairs in `d`, create a Node object with those properties.
    Takes k, as-is except for 'uuid', which is cast to int.
    Args:
        d (dict): property k, v pairs
        label (str): The py2neo.Node.__primarylabel__ to assign
    Returns:
        (Node): py2neo.Node instance of type `label`
    """
    uuid = int(d.get('uuid', -1))
    contributor = Node("Contributor",
                       uuid=uuid,
                       name=d.get('name'),
                       github_id=d.get('github_id'),
                       login=d.get('login'),
                       host_type=d.get('host_type'))
    return contributor


def main(argv=None):
    if argv is None:
        argv: List = sys.argv

    DB, merged_contributors, batch_size = argv[1:]
    g: Graph = Graph(password=get_graph_password())
    python_projects_on_pypi_query: str = \
        """MATCH (:Language {name: 'Python'})
        <-[:IS_WRITTEN_IN]-(p:Project {merged_contributors: %d})
        <-[:HOSTS]-(:Platform {name: 'Pypi'})
        return p order by p.name"""
    select_contributors_query: str = \
        """select contributors from project_names
        where api_has_been_queried=1 and api_query_succeeded=1
        and project_name=?"""

    # Phase 1: get all project_names from Neo4j the contributors of which have
    # not tried to be merged yet; this means getting the `contributors` field
    # from SQLite
    print("Querying Neo4j for nodes representing Python projects on Pypi\n",
          file=sys.stderr)
    projects_cursor: Cursor = execute_cypher_match_statement(
        g, python_projects_on_pypi_query % int(merged_contributors)
    )

    print("Converting py2neo Cursor into iterable of dicts\n", file=sys.stderr)
    projects_nodes: Iterator[Node] = map(lambda r: r.get('p'), projects_cursor)

    with connect(DB) as conn:
        conn.row_factory = Row
        nodes_and_execute_args: Generator[Tuple[Node, Tuple[Text, Tuple[Text]]]] = \
            ((node, (select_contributors_query, (node.get("name"),)))
             for node in projects_nodes)

        nodes_and_contributors_cursors: Iterator[Tuple[Node, Cursor]] = \
            map(lambda tup: (tup[0], conn.execute(*tup[1])), nodes_and_execute_args)

        nodes_and_contributors_generators: Iterator[Tuple[Node, Generator[ByteString]]] = \
            map(lambda tup: (tup[0], (row[0] for row in tup[1])), nodes_and_contributors_cursors)

        nodes_and_contributors_dict_iterators: Iterator[Tuple[Node, Iterator[List[Dict]]]] = \
            map(lambda tup: (tup[0], map(json.loads, tup[1])), nodes_and_contributors_generators)

        nodes_and_contributors_iterables: Iterator[Tuple[Node, Iterator[Dict]]] = \
            map(lambda tup: (tup[0], it.chain.from_iterable(tup[1])),
                nodes_and_contributors_dict_iterators)

        node_and_contributor_pairs: Iterator[Iterator[Tuple[Node, Dict]]] = \
            map(lambda tup: zip(it.repeat(tup[0]), tup[1]), nodes_and_contributors_iterables)

        all_nodes_and_contributors: Iterator[Tuple[Node, Dict]] = \
            it.chain.from_iterable(node_and_contributor_pairs)

        project_nodes__contributor_nodes: Iterator[Tuple[Node, Node]] = \
            map(lambda tup: (tup[0], create_contributor_node(tup[1])),
                all_nodes_and_contributors)

        batches = chunk(project_nodes__contributor_nodes, int(batch_size))
        projects = defaultdict(int)
        for batch in batches:
            tx = g.begin()
            for pnode_cnode in batch:
                pnode, cnode = pnode_cnode
                projects[pnode] += 1
                if projects[pnode] == 1:
                    print("MERGEing contributors to Neo4j for project "
                          f"{pnode['name']}", file=sys.stderr)
                print(f"\tMERGEing contributor {projects[pnode]}: "
                      "{cnode.get('name')}", file=sys.stderr)
                tx.merge(cnode, "Contributor", "uuid")
                print("\t\tMERGEing relationship to contributor "
                      f"{projects[pnode]}: {cnode.get('name')}",
                      file=sys.stderr)
                rel = Relationship(cnode, "CONTRIBUTES_TO", pnode)
                tx.merge(rel)
            else:
                tx.commit()

        for project, count in projects.items():
            tx = g.begin()
            print("Upating 'merged_contributors' property for Project node "
                  f"{project} with value {count}", file=sys.stderr)
            project.update(merged_contributors=count)
            tx.push(project)
            tx.commit()
        else:
            del g
        print("\nFinished.", file=sys.stderr)


if __name__ == "__main__":
    main()
