#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from functools import reduce
from traceback import print_tb

from py2neo import Graph, Node
from py2neo.database import GraphError

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


def update_Node_and_return(node, **kwargs):
    """ Call `node`.update, inserting {k: v for k, v in kwargs.items()}
    into the `node`'s internal values() dict. Returns `node`, udpated.
    Args:
        (node): py2neo.Node to update
        (kwargs): key, value pairs of properties to add to `node`
    Returns:
        (node): `node` passed in with its internal properties changed
    """
    node.update(**kwargs)
    return node


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
        print(f"Environment variable {GRAPHDBPASS} not set. Cannot access graph DB",
              file=sys.stderr)
        sys.exit(1)
    else:
        g = Graph(password=pw)

    python_projects_on_pypi_query = \
        """MATCH (:Language {name: 'Python'})
        <-[:IS_WRITTEN_IN]-(p:Project)
        <-[:HOSTS]-(:Platform {name: 'Pypi'})
        return p"""

    tx = g.begin(autocommit=False)
    print("Querying Neo4j for nodes representing Python projects on Pypi\n",
          file=sys.stderr)
    python_projects_on_pypi = \
        execute_cypher_match_statement(g, python_projects_on_pypi_query)

    print("Converting py2neo Cursor into generator of dicts\n", file=sys.stderr)
    python_projects_on_pypi_nodes = \
        map(lambda record: record.get('p'), python_projects_on_pypi)

    print("Setting the 'merged_contributors' property to -1 on py2neo.Node "
          "objects representing Python projects\n", file=sys.stderr)
    python_projects_on_pypi_nodes_property_set = \
        map(lambda n: update_Node_and_return(n, merged_contributors=-1),
            python_projects_on_pypi_nodes)

    output_messages = ("\tProject '%s' updated UNSUCCESSFULLY\n",
                       "\tProject '%s' updated SUCCESSFULLY\n")

    num_successful, num_attempted = 0, 0
    print("Attempting to push updates to remote graph\n",
            file=sys.stderr)
    for node in python_projects_on_pypi_nodes_property_set:
        successful = 0
        try:
            tx.merge(node)
        except GraphError as ge:
            successful = 0
            print_tb(ge)
            continue
        except Exception as e:
            successful = 0
            print_tb(e)
            continue
        else:
            successful = 1
            tx.commit()
        finally:
            num_successful += successful
            num_attempted += 1
            print(output_messages[successful] % node['name'], file=sys.stderr)
    else:
        print(f"{round((num_successful / num_attempted) * 100, 2)}% "
                "successfully pushed to remote graph")
        del tx

    # print("Combining the generator of py2neo.Node objects into a py2neo.Subgraph\n",
    #       file=sys.stderr)
    # python_projects_on_pypi_subgraph = \
    #     reduce(lambda node1, node2: node1 | node2,  # union (set operation)
    #            python_projects_on_pypi_nodes_property_set)
    # with g.begin(autocommit=False) as tx:
    #     print("Attempting to push these updates to remote graph\n",
    #           file=sys.stderr)
    #     try:
    #         tx.push(next(python_projects_on_pypi_subgraph))  # is 1 Subgraph obj
    #     except GraphError as ge:
    #         tx.rollback()
    #         print(f"Exception occurred:\n{ge}", file=sys.stderr)
    #         sys.exit(1)
    #     except Exception as e:
    #         tx.rollback()
    #         sys.exit(e)
    #     else:
    #         print("The 'merged_contributors' property of Nodes representing "
    #               "Python projects on Pypi were updated successfully",
    #               file=sys.stderr)
    #         tx.commit()
    # del g


if __name__ == "__main__":
    main()