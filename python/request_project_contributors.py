#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser, RawDescriptionHelpFormatter

from libraries_io_project_contributors_endpoint import \
    build_GET_request, execute_GET_request
from get_pypi_python_projects_from_neo4j.py import \
    get_neo4j_driver, execute_cypher_query


def return_parser():
    parser = ArgumentParser(
        description='Send GET requests to Libraries.io API, respecting rate limit',
        formatter_class=RawDescriptionHelpFormatter,
        epilog='N.b. to avoid being prompted for Graph DB password and '
        'Libraries.io API key, set the ENV variables `GRAPHDBPASS` and `APIKEY`'
        ', respectively'
    )
    parser.add_argument('graph_db_URI', type=str,
                        help='The address at which Neo4j will be accessed')

    # parser.add_argument('cypher_query', type=argparse.FileType('r'),
    #                     help='')


def main():
    args = return_parser().parse_args()
    return args

if __name__ == "__main__":
    main()
