#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from argparse import ArgumentParser, RawTextHelpFormatter
from sqlite3 import connect, IntegrityError, OperationalError, Binary, Row

from get_pypi_python_projects_from_neo4j import URI

logger = logging.getLogger(__name__)


def return_parser():
    p = ArgumentParser(
        description='',
        formatter_class=RawTextHelpFormatter,
        epilog='N.b. to avoid being prompted for Graph DB password and '
        'Libraries.io API key, set the ENV variables `GRAPHDBPASS` and `APIKEY`'
        ', respectively'
    )
    p.add_argument('DB', type=str,
                   help='The sqlite DB containing project_names that have '
                   'been queried and those yet to be sent to Libraries.io '
                   'API.')
    p.add_argument('table', type=str,
                   help='The name of the table in the sqlite DB specified '
                   'in the `project_names_DB` argument')
    p.add_argument('batch_size', type=int,
                   help='The amount of API calls to execute before sleeping; '
                   'n.b. the API has a rate limit of 60 per minute')
    p.add_argument('time_to_sleep', type=int,
                   help='Time (s) for script to pause between API batches')
    p.add_argument("-l", "--log", dest="log_level", default='INFO',
                   choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                   help="Set the logging level; default: %(default)s")
    p.add_argument('--logfile', type=str, required=False,
                   help='The log file to which to write logging')
    p.add_argument('--logfile_level', type=str, required=False, default='DEBUG',
                   help='The level of logging to write to `logfile`')
    return p


def craft_sqlite_project_names_update(project_name,
                                      api_has_been_queried,
                                      api_query_succeeded):
    """ Given values for each field of the `project_names` table,
    return a tuple of the parameterized insert statement and the record
    to pass to sqlite3.Connection.cursor.execute()
    """
    update_query = f"""UPDATE project_names SET
                    api_has_been_queried={api_has_been_queried},
                    api_query_succeeded={api_query_succeeded},
                    execution_error=?,
                    contributors=?,
                    ts=current_timestamp WHERE project_name='{project_name}'"""
    return update_query


def execute_sqlite_query(conn, query, params=None):
    execute_args = (query, params) if params is not None else (query,)
    try:
        cur = conn.cursor()
        cur.execute(*execute_args)
    except (IntegrityError, OperationalError):
        logger.error('SQLite error occurred; rolling back', exc_info=True)
        conn.rollback()
        return
    except:
        logger.error('Exception occurred; rolling back', exc_info=True)
        conn.rollback()
        return
    else:
        conn.commit()
        logger.info(f'{cur.rowcount} records changed')
        return 0
    finally:
        cur.close()


def select_from_sqlite(conn, query, params=None, num_retries=3):
    execute_args = (query, params) if params is not None else (query,)
    for i in range(num_retries + 1):
        try:
            cur = conn.cursor()
            cur.execute(*execute_args)
        except (IntegrityError, OperationalError):
            logger.error(f'SQLite error occurred (retry {i}):', exc_info=True)
            continue
        except:
            logger.error(f'Exception occurred (retry {i}):', exc_info=True)
            continue
        else:
            result = cur.fetchall()
            logger.info(f"Fetched {len(result)} records")
            return result
        finally:
            cur.close()
    else:
        logging.warning("Could not execute SELECT query successfully "
                        f"even after {num_retries} retries")
        return
