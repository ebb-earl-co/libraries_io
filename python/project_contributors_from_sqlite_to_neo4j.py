#!/usr/bin/env python
# -*- coding: utf-8 -*-

from json import loads as json_loads, JSONDecodeError

from logger import return_logger
from utils.get_pypi_python_projects_from_neo4j import \
    (closing, get_neo4j_driver, execute_cypher_query, CypherError,
     ServiceUnavailable, URI)
from utils.utils import connect, os, return_parser, Row
from merge_contributors_query import get_contributor_keys_from_dict, merge_contributors
import merge_contributors.query as merge_contributors_query


def main(args, logger):

    select_query = """select contributors from {args.table}
    where api_has_been_queried=1 and api_query_succeeded=1
    and project_name='{args.project_name}'"""

    with connect(args.DB) as conn:
        conn.row_factory = Row
        cur = conn.cursor()
        cur.execute(select_query)
        project_names_query_result = cur.fetchone()
        if project_names_query_result is None:
            logger.warning(f"The query\n{select_query}\nreturned no result")
            return

    try:
        contributors = json.loads(project_names_query_result['contributors'])
    except JSONDecodeError:
        logger.error("Could not load JSON in SQLite record corresponding to"
                     f" {project_name}", exc_info=True)
        return
    except TypeError:  # project_names_query_result has no such key
        logger.error("Check the SQL query that returned this record; "
                     f"{select_query}", exc_info=True)
        return
    else:
        num_contributors = len(contributors)
        if num_contributors == 0:
            logger.warning(f"Project '{project_name}' has no contributors")
            return
        else:
            logger.debug(f"There are {num_contributors} contributors to "
                         f"{project_name}")

    logger.info("Instantiating Neo4j driver connected to instance running on "
                f"{URI}...")
    authentication = ('neo4j', os.environ.get('GRAPHDBPASS'))
    try:
        neo4j_driver = get_neo4j_driver(URI, authentication)
    except ServiceUnavailable:
        logger.critical(f"No Neo4j instance running on {URI}; cannot proceed")
        return
    else:
        merge_results = merge_contributors(neo4j_driver, project_name,
                                           merge_contributors_query, contributors)


if __name__ == "__main__":
    args = return_parser().parse_args()
    logger = return_logger(__name__, args.log_level,
                           args.logfile, args.logfile_level)
