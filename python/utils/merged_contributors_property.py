#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from traceback import print_tb
from py2neo import Graph
from py2neo.database import Neo4jError

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


def main(argv=None):
    if argv is None:
        argv = sys.argv

    query_file = argv[1]

    pw = get_graph_password()
    if pw is None:
        print(f"Environment variable {GRAPHDBPASS} not set. Cannot access graph DB",
              file=sys.stderr)
        sys.exit(1)
    else:
        g = Graph(password=pw)

    with open(query_file, 'r') as f:
        merged_contributors_property_query = f.read()

    try:
        g.evaluate(merged_contributors_property_query)
    except Neo4jError as ne:
        print_tb(ne, file=sys.stderr)
        sys.exit(1)
    else:
        print(f"Query\n{merged_contributors_property_query}\nexecuted successfully",
              file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
