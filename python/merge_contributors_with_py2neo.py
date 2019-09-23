#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from py2neo import Graph, Node

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
    cursor = g.run(statement, **kwargs)
    return cursor


def return_Node_from_record(label, record):
    """ Given a Neo4j node label, `label`, and a record,
    `record`, return py2neo.Node instance of type `label` instantiated with
    the `record`. E.g.
    >>> # query = "MATCH (p:Person) RETURN p.name as name, p.age as age LIMIT 1"
    >>> cursor = g.run(query)
    >>> return_Node_from_record("Person", next(cursor))
    (:Person {age: 42, name: 'John Doe'})
    """
    properties = dict(record)
    n = Node(label, **properties)
    return n


def main():
    pw = get_graph_password()
    if pw is None:
        # print(f"Environment variable {GRAPHDBPASS} not set. Cannot access graph DB",
        #       file=sys.stderr)
        sys.exit(1)
    else:
        g = Graph(password=pw)

    python_projects_on_pypi_query = \
        """MATCH (:Language {name: 'Python'})
        <-[:IS_WRITTEN_IN]-(p:Project)
        <-[:HOSTS]-(:Platform {name: 'Pypi'})
        return p"""
    python_projects_on_pypi = \
        execute_cypher_match_statement(g, python_projects_on_pypi_query)

    python_projects_on_pypi_dicts = \
        (dict(record) for record in python_projects_on_pypi)

    python_projects_on_pypi_nodes = \
        (return_Node_from_record("Project", **d)
         for d in python_projects_on_pypi_dicts)

    python_projects_on_pypi_nodes_property_set = \
        map(lambda n: n.setattr('merged_contributors', -1),
            python_projects_on_pypi_nodes)


if __name__ == "__main__":
    main()