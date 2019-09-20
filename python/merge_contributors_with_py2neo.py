#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from py2neo import Graph

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
    return


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
    python_projects_on_pypi = execute_cypher_match_statement(g, python_projects_on_pypi_query)


if __name__ == "__main__":
    main()