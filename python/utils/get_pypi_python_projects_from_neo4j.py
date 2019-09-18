#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script requests the Libraries.io API Project Contributors endpoint. Pass
the name of the project the contributors of which to be requested as the only
positional argument; e.g.

>>> python %s 'MATCH (p:Project) return p;'

If the request is successful, the JSON response is returned to STDOUT. Otherwise
the error that occurred during the request is returned in JSON format to STDOUT.
"""

from neo4j import DirectDriver
from neo4j.exceptions import CypherError

from contextlib import closing
from getpass import getpass
import json
import sys


URI = "bolt://localhost:7687"


def get_neo4j_driver(uri, auth, **kwargs):
    """ Given URI to connect to, `uri`, and authentication info,
    `auth`, (as well as optional kwargs passed to neo4j.GraphDatabase.Driver)
    return a neo4j.Driver object to interact with the graph hosted at `uri`

    Args:
        uri (str): address at which Neo4j graph is accessed
        auth (tuple): (username, password) for graph at `uri`
    Returns:
        (neo4j.Driver): driver object to interact with graph at `uri`
    """
    return DirectDriver(uri, auth=auth)


def execute_cypher_query(driver, query, params=None):
    """ Given `neo4j.Driver` instance and `query` str, execute `query` via
    the `driver` in a session, returning the `neo4j.BoltStatementResult` object
    that results.

    Args:
        driver (neo4j.Driver): instance of database driver
        query (str): Cypher query to execute
        params (dict): Neo4j parameters that are substituted into `query`
    Returns:
        (neo4j.BoltStatementResult): the result object
    """
    with driver.session() as session:
        result = session.run(query, parameters=params)
        return result


def main(argv=None):
    if argv is None:
        argv = sys.argv

    if '-h' in argv or '--help' in argv:
        print(__doc__ % argv[0], file=sys.stderr)
        return 0

    try:
        query = argv[1]
    except IndexError:
        sys.exit("No Cypher query passed")

    authentication = ('neo4j', getpass('Graph DB password:'))
    with closing(get_neo4j_driver(URI, authentication)) as driver:
        try:
            result = execute_cypher_query(driver, query)
        except CypherError as c:
            to_return = json.dumps({"CypherError": str(c)})
            print("Cypher error occurred", file=sys.stderr)
            return to_return
        except Exception as e:
            to_return = json.dumps({"Exception": str(e)})
            print("Exception occurred", file=sys.stderr)
            return to_return
        else:
            names = (record.get('p').get('name') for record in result.records())
            return json.dumps(names)

        return json.dumps(list(to_return))

if __name__ == "__main__":
    sys.stdout.write(main())
