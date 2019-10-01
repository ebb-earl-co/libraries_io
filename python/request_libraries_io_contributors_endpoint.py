#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from functools import reduce
from time import sleep
import itertools as it

from ratelimit import limits, sleep_and_retry

from logger import return_logger
from utils.libraries_io_project_contributors_endpoint import \
    build_get_request, parse_request_response_content, Session, URL
from utils.utils import (connect, execute_sqlite_query,
                         craft_sqlite_project_names_page_insert,
                         craft_sqlite_project_names_page_update, return_parser,
                         select_from_sqlite, Binary, Row)


@sleep_and_retry
@limits(calls=59, period=60)
def request_project_contributors(project_name, logger, endpoint=URL, per_page=100):
    """ Request the information according to `project_name` from the
    Libraries.io API, Project Contributors endpoint. This function is
    decorated to respect the rate limit of 60 requests per minute.
    Args:
        project_name (str): query contributors to this project
        endpoint (str): the URL to pass to requests.get
        per_page (int): between 30 and 100, the amount of results per query
    Returns:
        (iterable): {page: namedtuple} for each page in endpoint pages
    """
    logger.debug("Requesting Libraries.io Project Contributors API "
                 f"results for '{project_name}'")
    logger.debug(f"\tRequesting page 1 for '{project_name}'...")
    url = endpoint % project_name
    get_request = build_get_request(url, per_page=per_page)
    s = Session()
    prepared_request = s.prepare_request(get_request)
    response = s.send(prepared_request)
    try:
        response.raise_for_status()
    except HTTPError as h:
        if response.status_code == 429:
            logger.debug(f"\tRequest to API for page 1 of '{project_name}' "
                         "returned 429 error; sleeping...")
            sleep(30)
    else:
        num_contributors = int(response.headers['Total'])
    finally:
        out = [(1, parse_request_response_content(response))]

    pages_to_request = range((num_contributors // per_page) + 2)[2:]
    for page in pages_to_request:
        logger.debug(f"Requesting page {page} for '{project_name}'...")
        get_request = build_get_request(url, per_page=per_page)
        prepared_request = s.prepare_request(get_request)
        response = s.send(prepared_request)
        out.append((page, parse_request_response_content(response)))
    else:
        logger.debug(f"Done requesting for '{project_name}'\n")
        return out


def craft_sqlite_execute_args(conn, project_name, pce, logger):
    """ Use a project_name and its corresponding list of results from
    having run request_project_contributors (read: list of tuples in which each
    tuple is of the form (page: namedtuple(response.content, response.error)) )
    and create SQLite update queries for each element in `pce`.
    Args:
        conn (sqlite3.connect): connection to SQLite DB
        project_name (str): the project_name that each pce element corresponds to
        pce (list): list of tuples of the form (int: namedtuple)
    Returns:
        (list): of tuples representing arguments to pass to sqlite3.execute
    """
    for tup in pce:
        page, ce = tup  # (page, content_and_error)
        logger.debug(f"Creating SQLite statements for project '{project_name}'")
        logger.debug(f"Creating SQLite statement for project '{project_name}', "
                     f"page {page}...")
        aqs = 1 if ce.error is None else 0  # api_queried_successfully
        if page == 1:
            query = \
                craft_sqlite_project_names_page_update(project_name=project_name,
                                                       page=page,
                                                       api_has_been_queried=1,
                                                       api_query_succeeded=aqs)
            execute_args = \
                (conn, query,
                 (None, Binary(ce.content)) if ce.error is None else (ce.error, None))
        else:
            query = craft_sqlite_project_names_page_insert()
            execute_args = (conn, query, (project_name,
                                          page,  # page
                                          1,  # api_has_been_queried
                                          aqs,  # api_query_succeeded
                                          ce.error,  # execution_error
                                          ce.content,  # contributors
                                          datetime.now()))  # ts
        yield execute_args
        logger.debug("Done creating SQLite statements for project "
                     f"'{project_name}'")


def main():
    args = return_parser().parse_args()
    logger = return_logger(__name__, args.log_level,
                           args.logfile, args.logfile_level)

    select_query = f"""select project_name as name from {args.table}
    where api_query_succeeded is null group by project_name order by name desc limit 500"""


    with connect(args.DB) as conn:
        logger.info("Querying SQLite for project names...\n")
        conn.row_factory = Row
        logger.debug(f"Created connection to sqlite DB {args.DB}")
        project_names_query_result = select_from_sqlite(conn, select_query)
        project_names = (row['name'] for row in project_names_query_result)
        logger.info("Done.\n")

        logger.info("Requesting API for project_names...\n")
        names_pages_contents_errors = \
            map(lambda pn: (pn, request_project_contributors(pn, logger)), project_names)

        logger.info("Creating argument tuples to pass to sqlite3.execute...\n")
        sqlite_execute_args_gens = map(
            lambda pn_pce, conn=conn: craft_sqlite_execute_args(conn, *pn_pce, logger),
            names_pages_contents_errors
        )

        logger.info("Executing SQLite INSERT/UPDATE queries...\n")
        return_codes_starmaps = map(
            lambda args_gen: it.starmap(execute_sqlite_query, args_gen),
            sqlite_execute_args_gens
        )

        return_codes = \
            it.chain.from_iterable(it.chain(starmap)
                                   for starmap in return_codes_starmaps)
        successfully_updated = sum(1 for _ in
                                   filter(lambda x: x is not None, return_codes))
        logger.info(f"{successfully_updated} records successfully updated")
        logger.info("Finished.")


if __name__ == "__main__":
    main()