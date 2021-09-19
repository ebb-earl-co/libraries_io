#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
import traceback
from argparse import ArgumentParser, RawTextHelpFormatter
from sqlite3 import connect, OperationalError, IntegrityError

from .get_pypi_python_projects_from_neo4j import \
    getpass, get_neo4j_driver, execute_cypher_query, URI


def populate_sqlite_project_names(conn, table, names):
    """ Given a sqlite connection, database, table name, and iterable of
    project names, insert into `table` the `names`. This is a single-use
    utility to populate DB for the first time.
    """
    to_insert = [(name, 1, 0, None, None, None, None) for name in names]
    try:
        cur = conn.cursor()
        cur.executemany(f"insert into {table}(project_name, page, "
                        "api_has_been_queried, api_query_succeeded, "
                        "execution_error, contributors, ts) "
                        "values (?, ?, ?, ?, ?, ?, ?)", to_insert)
    except (IntegrityError, OperationalError) as e:
        traceback.print_tb(e, file=sys.stderr)
        sys.exit(1)
    else:
        return cur.rowcount
    finally:
        cur.close()


def return_parser():
    parser = ArgumentParser(
        description='Query local Neo4j database and insert into local sqlite',
        formatter_class=RawTextHelpFormatter,
        epilog='N.b. to avoid being prompted for Graph DB password, '
        'set the ENV variable `GRAPHDBPASS`'
    )
    parser.add_argument('DB', type=str,
                        help='The sqlite DB containing project_names that have '
                        'been queried and those yet to be sent to Libraries.io '
                        'API.')
    parser.add_argument('table', type=str,
                        help='The name of the table in the sqlite DB specified '
                        'in the `project_names_DB` argument')
    parser.add_argument('--neo4j_URI', type=str, default=URI, required=False,
                        help='The address at which Neo4j service is running')
    parser.add_argument('--neo4j_user', type=str, default='neo4j', required=False,
                        help='The user of the DB running at above address')

    return parser


def main():
    # Parse args and set up values
    args = return_parser().parse_args()
    args.graphdbpassword = os.environ.get("GRAPHDBPASS") \
        or getpass("Graph DB password:")

    # Query Neo4j for all Python projects
    driver = get_neo4j_driver(args.neo4j_URI,
                              (args.neo4j_user, args.graphdbpassword))
    print(f"Driver for Neo4j graph running at {args.neo4j_URI} "
          f"instantiated to execute queries as user {args.neo4j_user}\n",
          file=sys.stderr)

    cypher_query = ("MATCH (:Platform{name:'Pypi'})-[:HOSTS]->"
                    "(p:Project)-[:IS_WRITTEN_IN]->"
                    "(:Language{name:'Python'}) return p.name order by p.name")
    print(f"Executing Cypher query:\n{cypher_query}\n", file=sys.stderr)

    cypher_result = execute_cypher_query(driver, cypher_query)
    project_names = [record.get('p.name') for record in cypher_result.records()]
    print(f"Cypher query resulted in {len(project_names)} records\n",
          file=sys.stderr)

    # Connect to sqlite
    print(f"Inserting these {len(project_names)} records into "
          f"{args.DB}.{args.table}", file=sys.stderr)
    with connect(args.DB) as conn:
        names_inserted = populate_sqlite_project_names(conn,
                                                       args.table,
                                                       project_names)
    print(f"{names_inserted} records inserted into {args.DB}.{args.table}",
          file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
