#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" This is the main runner script for querying the Libraries.io
API, project contributors endpoint and loading the response (and error, if any)
to sqlite. As the API rate limits to 60 per minute, 60 or fewer API calls
will be made at a time, with `time.sleep` called between batches.
"""

import sys
from datetime import datetime
from time import sleep

from libraries_io_project_contributors_endpoint import \
    build_GET_request, execute_GET_request, URL
from logger import return_logger
from utils import (connect, craft_sqlite_project_names_record, return_parser,
                   select_from_sqlite, insert_into_sqlite, Row)


def main(args):
    logger = return_logger(__name__, args.log_level,
                           args.logfile, args.logfile_level)

    logger.debug(f"Arguments passed:\n{args}")

    select_query = """select project_name from ?
    where api_query_succeeded is null LIMIT ?"""
    query_params = (args.table, args.batch_size)

    with connect(args.DB) as conn:
        conn.row_factory = Row
        logger.debug(f"Created connection to sqlite DB {args.DB}")
        project_names_query_result = \
            select_from_sqlite(conn, select_query, params=query_params)
        project_names = [row['name'] for row in project_names_query_result]
        for project_name in project_names:
            try:
                GET_request = build_GET_request(URL % project_name)
                content_and_error = execute_GET_request(GET_request)
                if content_and_error.error is None:
                    sqlite_execute_tuple = craft_sqlite_project_names_record(
                        project_name=project_name,
                        api_has_been_queried=1,
                        api_query_succeeded=1,
                        execution_error=None,
                        contributors=content_and_error.content,
                        ts=datetime.now()
                    )
                else:
                    sqlite_execute_tuple = craft_sqlite_project_names_record(
                        project_name=project_name,
                        api_has_been_queried=1,
                        qpi_query_succeeded=0,
                        execution_error=content_and_error.error,
                        contributors=None,
                        ts=datetime.now()
                    )
                logger.debug(f"Inserting record corresponding to '{project_name}'"
                             f": {sqlite_execute_tuple}")
                insert_into_sqlite(conn, *sqlite_execute_tuple)
                logger.info(f"Record corresponding to '{project_name}' "
                            "inserted successfully")
            except:
                logger.error(f"Exception occurred for project {project_name}",
                             exc_info=True)
        else:
            logger.info
            sys.exit(0)

if __name__ == "__main__":
    args = return_parser().parse_args()
    main(args)