#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from utils.get_pypi_python_projects_from_neo4j import \
    get_neo4j_driver, getpass, CypherError, URI
from utils.utils import ArgumentParser, RawTextHelpFormatter

logger = logging.getLogger(__name__)


def merge_contributors(driver, merge_query, merge_query_params,
                       match_query, match_query_params):
    """ Using `neo4j.DirectDriver` object, attempt executing `merge_query`,
    followed by `match_query`, that is formatted using `project_name` and
    Returns:
        (dict): {`project_name`: [{contributor, successful, query, params}]}
    """
    with driver.session() as s:
        with s.begin_transaction() as tx:  # Execute the merge_query
            successful = [None, None]
            try:
                merge_query_result = tx.run(merge_query, merge_query_params)
            except CypherError:
                logger.error("COULD NOT MERGE", exc_info=True)
                tx.rollback()
                return
            except Exception:
                logger.error("Exception occurred while executing\n"
                             f"{merge_query}", exc_info=True)
                tx.rollback()
                return
            else:
                logger.debug("MERGE query successful for statement "
                             f"\n{merge_query_result.summary().metadata['statement']}\n"
                             "and parameters: "
                             f"{merge_query_result.summary().metadata['parameters']}")
                tx.commit()

        with s.begin_transaction() as tx2:  # Execute match-match-merge query
            try:
                match_query_result = tx2.run(match_query, match_query_params)
            except CypherError:
                logger.error("COULD NOT MATCH-MATCH-MERGE", exc_info=True)
                tx2.rollback()
                return
            except Exception:
                logger.error("Exception occurred while execution\n"
                             f"{match_query}", exc_info=True)
                tx2.rollback()
                return
            else:
                logger.debug("MATCH-MERGE query successful for statement "
                             f"\n{match_query_result.summary().metadata['statement']}\n"
                             "and parameters: "
                             f"{merge_query_result.summary().metadata['parameters']}")
                tx2.commit()

        return 0


def return_parser():
    p = ArgumentParser(
        description='This script loads data from Libraries.io API, stored in '
        'SQLite in JSON format, to Neo4j by querying with the Python driver.',
        formatter_class=RawTextHelpFormatter,
        epilog='N.b. to avoid being prompted for Graph DB password, set the '
        'ENV variable `GRAPHDBPASS`'
    )
    p.add_argument('DB', type=str,
                   help='The sqlite DB containing project_names that have '
                   'been queried and the API response')
    p.add_argument('table', type=str,
                   help='The name of the table in the sqlite DB specified '
                   'in the `DB` argument')
    p.add_argument("-l", "--log", dest="log_level", default='INFO',
                   choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                   help="Set the logging level; default: %(default)s")
    p.add_argument('--logfile', type=str, required=False,
                   help='The log file to which to write logging')
    p.add_argument('--logfile_level', type=str, required=False, default='DEBUG',
                   help='The level of logging to write to `logfile`')
    p.add_argument('--neo4j_URI', type=str, default=URI, required=False,
                   help='The address at which Neo4j service is running')
    p.add_argument('--neo4j_user', type=str, default='neo4j', required=False,
                   help='The user of the DB running at above address')
    return p
