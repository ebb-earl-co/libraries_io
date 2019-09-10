#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from sqlite3 import connect, OperationalError, IntegrityError

from libraries_io_project_contributors_endpoint import \
    build_GET_request, execute_GET_request, URL
from get_pypi_python_projects_from_neo4j import \
    getpass, get_neo4j_driver, execute_cypher_query, URI


def populate_sqlite_project_names(db, table, names):
    """ Given a sqlite database, table name, and iterable of project names,
    insert into `db`.`table` the `names`. This is a single-use utility to
    populate DB for the first time.
    """
    to_insert = [(name, 0, None, None, None, None) for name in names]
    try:
        with connect(db) as conn:
            conn.executemany("insert into project_names(project_name, "
                             "api_has_been_queried, api_query_succeeded, "
                             "execution_error, contributors, ts) "
                             "values (?, ?, ?, ?, ?, ?)", to_insert)
    except (IntegrityError, OperationalError):
        raise
    else:
        return


def return_parser():
    parser = ArgumentParser(
        description='Send GET requests to Libraries.io API, respecting rate '
        'limit.\nIf list of package names to query is not specified, Neo4j '
        'running\nat address specified in first argument will be queried for '
        'said list.\n',
        formatter_class=RawTextHelpFormatter,
        epilog='N.b. to avoid being prompted for Graph DB password and '
        'Libraries.io API key, set the ENV variables `GRAPHDBPASS` and `APIKEY`'
        ', respectively'
    )
    # parser.add_argument('project_names_file', type=FileType('r'),
    #                     help='The file containing the names of projects to the '
    #                     'project contributors endpoint of the Libraries.io API')
    parser.add_argument('DB', type=str,
                        help='The sqlite DB containing project_names that have '
                        'been queried and those yet to be sent to Libraries.io '
                        'API.')
    parser.add_argument('table', type=str,
                        help='The name of the table in the sqlite DB specified '
                        'in the `project_names_DB` argument')
    parser.add_argument('neo4j_URI', type=str, default=URI,
                        help='The address at which Neo4j service is running')
    parser.add_argument('neo4j_user', type=str, default='neo4j',
                        help='The user of the DB running at above address')

    return parser


def main():
    # Parse args and set up values
    args = return_parser().parse_args()
    args.graphdbpassword = os.environ.get("GRAPHDBPASSWORD") \
        or getpass("Graph DB password:")

    # Query Neo4j for all Python projects
    driver = get_neo4j_driver(args.neo4j_URI,
                              (args.neo4j_user, args.graphdbpassword))
    print(f"Driver for Neo4j graph running at {args.neo4j_URI} "
          "instantiated to execute queries as user {args.neo4j_user}\n",
          file=sys.stderr)

    cypher_query = ("MATCH (p:Project)-[:IS_WRITTEN_IN]->"
                    "(:Language {name: 'Python'}) return p order by p.name")
    print(f"Executing Cypher query:\n{cypher_query}\n", file=sys.stderr)

    cypher_result = execute_cypher_query(driver, cypher_query)
    project_names = [record.get('p').get('name')
                     for record in cypher_result.records()]
    print(f"Cypher query resulted in {len(project_names)} records\n",
          file=sys.stderr)
    return json.dump(str(project_names), sys.stdout)

    # Connect to sqlite
    # conn = connect(args.DB)

if __name__ == "__main__":
    main()
