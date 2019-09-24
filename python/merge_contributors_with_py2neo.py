#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys

from py2neo import Graph, Node, Relationship

from utils.utils import connect, Row


GRAPHDBPASS = 'GRAPHDBPASS'


def get_graph_password(env_variable_name=GRAPHDBPASS):
    """ Get graph password that is set as ENV variable
    Args:
        env_variable_name (str): the environment variable to get
    Returns:
        the output of os.environ.get(env_variable_name, None)
    """
    pw = os.environ.get(env_variable_name, None)
    return pw


def execute_cypher_match_statement(g, statement, **kwargs):
    """ Return the iterator of query results from `py2neo.Graph.run`
    Args:
        g (py2neo.Graph): the graph object representing DB to interact with
        statement (str): the query to run on `g`
        (kwargs): parameters that are inserted into `statement`
    Returns:
        (py2neo.database.Cursor): query results
    """
    cursor = g.run(statement, **kwargs)
    return cursor


def main(argv=None):
    if argv is None:
        argv = sys.argv

    DB = argv[1]

    g = Graph(password=get_graph_password())

    python_projects_on_pypi_query = \
        """MATCH (:Language {name: 'Python'})
        <-[:IS_WRITTEN_IN]-(p:Project {merged_contributors: %d})
        <-[:HOSTS]-(:Platform {name: 'Pypi'})
        return p"""

    select_contributors_query = \
        """select project_name, contributors from project_names
        where api_has_been_queried=1 and api_query_succeeded=1
        and project_name=?"""

    # Phase 1: get all project_names from Neo4j the contributors of which have
    # not tried to be merged yet; this involves getting the `contributors` field
    # from SQLite

    projects_not_yet_tried_merge_query = python_projects_on_pypi_query % -1
    print("Querying Neo4j for nodes representing Python projects on Pypi\n",
          file=sys.stderr)
    projects_not_yet_tried_merge__cursor = \
        execute_cypher_match_statement(g, projects_not_yet_tried_merge_query)

    print("Converting py2neo Cursor into generator of dicts\n", file=sys.stderr)
    projects_not_yet_tried_merge__nodes = \
        list(map(lambda r: r.get('p'), projects_not_yet_tried_merge__cursor))

    with connect(DB) as conn:
        conn.row_factory = Row
        projects_not_yet_tried_merge__contributors = []
        for node in projects_not_yet_tried_merge__nodes:
            cur = conn.cursor()
            name = node['name']
            print(f"SELECTing contributors from SQLite for project {name}\n",
                  file=sys.stderr)
            cur.execute(select_contributors_query, (name,))
            result = cur.fetchone()
            projects_not_yet_tried_merge__contributors.append(
                json.loads(result['contributors'])
            )
            cur.close()

    # Phase 2: Create a (:Contributor) node for each key in the dict resulting
    # from json.loads().
    for i, cs in enumerate(projects_not_yet_tried_merge__contributors):
        project = projects_not_yet_tried_merge__nodes[i]
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

if __name__ == "__main__":
    main()