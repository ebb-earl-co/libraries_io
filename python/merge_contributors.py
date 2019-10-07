#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools as it
import json
import os
import sys
from typing import Iterator, List, Tuple

from py2neo import Graph, Node, Relationship
from py2neo.database import Cursor

from utils.utils import connect, Row

GRAPHDBPASS = 'GRAPHDBPASS'


def get_graph_password(env_variable_name: str = GRAPHDBPASS) -> str:
    """ Get graph password that is set as ENV variable
    Args:
        env_variable_name (str): the environment variable to get
    Returns:
        the output of os.environ.get(env_variable_name, None)
    """
    pw = os.environ.get(env_variable_name, None)
    return pw


def execute_cypher_match_statement(g: Graph, statement: str, **kwargs) -> Cursor:
    """ Return the iterator of query results from `py2neo.Graph.run`
    Args:
        g (py2neo.Graph): the graph object representing DB to interact with
        statement (str): the query to run on `g`
        (kwargs): parameters that are inserted into `statement`
    Returns:
        (py2neo.database.Cursor): query results
    """
    cursor: Cursor = g.run(statement, **kwargs)
    return cursor


def create_contributor_node(label: str = "Contributor", **kwargs) -> Node:

    contributor = Node("Contributor",
                        uuid=int(c['uuid']),
                        name=c['name'],
                        github_id=c['github_id'],
                        login=c['login'],
                        host_type=c['host_type'])

def main(argv=None):
    if argv is None:
        argv: list = sys.argv

    DB, merged_contributors = argv[1:]
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
    # not tried to be merged yet; this involves getting the `contributors` field
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
            ((node, (select_contributors_query, (node.get("name"),))) for node in projects_nodes)
        nodes_and_contributors_cursors: Iterator[Tuple[Node, Cursor]] = \
            # Cursor type is really Iterator[Row]
            map(lambda tup: (tup[0], conn.execute(*tup[1])), nodes_and_execute_args)

        nodes_and_contributors_generators: Iterator[Tuple[Node, Generator[ByteString]]] = \
            map(lambda tup: (tup[0], (row[0] for row in tup[1])), nodes_and_contributors_cursors)

        nodes_and_contributors_dict_iterators: Iterator[Tuple[Node, Iterator[List[Dict]]]] = \
            map(lambda tup: (tup[0], map(json.loads, tup[1])), nodes_and_contributors_generators)

        nodes_and_contributors_iterables: Iterator[Tuple[Node, Iterator[Dict]]] = \
            map(lambda tup: (tup[0], it.chain.from_iterable(tup[1])),
                nodes_and_non_empty_list_iterables)

        node_and_contributor_pairs: Iterator[Iterator[Tuple[Node, Dict]]] = \
            map(lambda tup: zip(it.repeat(tup[0]), tup[1]), nodes_and_contributors_iterables)

        all_nodes_and_contributors: Iterator[Tuple[Node, Dict]] = \
            it.chain.from_iterable(node_and_contributor_pairs)

        project_nodes__contributor_nodes: Iterator[Tuple[Node, Node]] = \
            map(lambda tup: (tup[0], create_contributor_node(tup[1])),
                all_nodes_and_contributors)

        grouped_pnodes_cnodes: Iterator[Node, Iterator[Node]] = \
            it.groupby(project_nodes__contributor_nodes, lambda tup: tup[0])

        batches = partition(grouped_pnodes_cnodes, 1000)
        for batch in batches:
            tx = g.begin(autocommit=False)
            merge_contributor = partial(merge_contributor, tx)
            for groupby in batch:
                all_merged = []
                for pnode, cnodes in groupby:
                    print(f"MERGEing contributors to Neo4j for project {pnode['name']}",
                          file=sys.stderr)
                    for cnode in enumerate(cnodes, 1):
                        tx.merge(cnode, "Contributor", "uuid")
                        rel = Relationship(cnode, "CONTRIBUTES_TO", pnode)
                        tx.merge(rel)
                        all_merged.append(True if g.exists(rel) else False)
                    else:
                        mc = 1 if all(all_merged) else 0
                        print(f"{'NOT ALL' if mc == 0 else 'ALL'} "
                              f"contributors to {project['name']} MERGEd successfully",
                              file=sys.stderr)
                        project.update(merged_contributors=mc)
                        g.push(project)
            else:
                tx.commit()
        else:
            del g






















        projects_contributors = []
        for node in projects_nodes:
            cur = conn.cursor()
            name = node['name']
            print(f"SELECTing contributors from SQLite for project {name}\n",
                  file=sys.stderr)
            cur.execute(select_contributors_query, (name,))
            result = cur.fetchall()
            projects_contributors.append(json.loads(result['contributors']))
            cur.close()

    # Phase 2: Create a (:Contributor) node for each dict in the list resulting
    # from json.loads().
    for i, cs in enumerate(projects_contributors):
        project = projects_nodes[i]
        print(f"MERGEing contributors to Neo4j for project {project['name']}",
              file=sys.stderr)
        all_merged = (True,) if len(cs) == 0 else []
        # If there are no contributors for a project, the below `for` loop will
        # be passed over, but the `else` clause will run; in that case, have
        # all_merged be an iterable that is truthy for all() so as to demarcate
        # correctly having merged all (zero) contributors
        for j, c in enumerate(cs, 1):
            contributor = Node("Contributor",
                               uuid=int(c['uuid']),
                               name=c['name'],
                               github_id=c['github_id'],
                               login=c['login'],
                               host_type=c['host_type'])
            print(f"\tAttempting to MERGE contributor {j}: {contributor}",
                  file=sys.stderr)
            g.merge(contributor, "Contributor", "uuid")
        # Phase 3: Create a relationship between (:Project) and (:Contributor) for
        # each contributor that is in the SQLite record according to `project_name`
            cp = Relationship(contributor, "CONTRIBUTES_TO", project)
            print(f"\tAttempting to CREATE relationship to contributor {j}: {cp}",
                  file=sys.stderr)
            g.create(cp)
            all_merged.append(True if g.exists(cp) else False)
        else:
            mc = 1 if all(all_merged) else 0
            print(f"{'NOT ALL' if mc == 0 else 'ALL'} "
                  f"contributors to {project['name']} MERGEd successfully",
                  file=sys.stderr)
            project.update(merged_contributors=mc)
            g.push(project)
    else:
        del g


# if __name__ == "__main__":
#     main()