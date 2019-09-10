#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser, FileType, RawTextHelpFormatter
import sqlite3

from libraries_io_project_contributors_endpoint import \
    build_GET_request, execute_GET_request
from get_pypi_python_projects_from_neo4j import \
    get_neo4j_driver, execute_cypher_query


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

    return parser


def main():
    args = return_parser().parse_args()
    return args

if __name__ == "__main__":
    main()
