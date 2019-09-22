#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" This is the main runner script for querying the Libraries.io
API, project contributors endpoint and loading the response (and error, if any)
to sqlite. As the API rate limits to 60 per minute, 60 or fewer API calls
will be made at a time, with `time.sleep` called between batches.
"""

from time import sleep

from logger import return_logger
from utils.libraries_io_project_contributors_endpoint import \
    build_GET_request, execute_GET_request, URL
from utils.utils import (connect, craft_sqlite_project_names_update,
                         return_parser, select_from_sqlite,
                         execute_sqlite_query, Binary, Row)


def main(args, logger):
    logger.debug(f"Arguments passed:\n{args}")

    select_query = f"""select project_name as name from {args.table}
    where api_query_succeeded is null LIMIT {args.batch_size}"""

    with connect(args.DB) as conn:
        conn.row_factory = Row
        logger.debug(f"Created connection to sqlite DB {args.DB}")
        project_names_query_result = select_from_sqlite(conn, select_query)
        project_names = [row['name'] for row in project_names_query_result]
        if len(project_names) == 0:
            return 1
        successfully_updated = []

        for project_name in project_names:
            try:
                GET_request = build_GET_request(URL % project_name)
                content_and_error = execute_GET_request(GET_request)
                if content_and_error.error is None:
                    sqlite_update_query = craft_sqlite_project_names_update(
                        project_name=project_name,
                        api_has_been_queried=1,
                        api_query_succeeded=1
                    )
                    execute_args = (conn, sqlite_update_query,
                                    (None, Binary(content_and_error.content)))
                else:
                    sqlite_update_query = craft_sqlite_project_names_update(
                        project_name=project_name,
                        api_has_been_queried=1,
                        api_query_succeeded=0
                    )
                    execute_args = (conn, sqlite_update_query,
                                    (content_and_error.error, None))
                logger.debug(f"Updating record corresponding to '{project_name}'")

                return_code = execute_sqlite_query(*execute_args)
                if return_code is not None:
                    logger.info(f"Record corresponding to '{project_name}' "
                                "updated successfully")
                    successfully_updated.append(project_name)
                else:
                    logger.warning(f"Record corresponding to '{project_name}' "
                                   "DID NOT UPDATE")
                    continue
            except:
                logger.error(f"Exception occurred for project {project_name}",
                             exc_info=True)
        else:
            logger.info(f"Project names\n{successfully_updated}\n"
                        "updated successfully: "
                        f"{round(len(successfully_updated)/len(project_names)*100, 2)}%")
            return 0

if __name__ == "__main__":
    args = return_parser().parse_args()
    logger = return_logger(__name__, args.log_level,
                           args.logfile, args.logfile_level)

    still_project_names_left = main(args, logger)
    while still_project_names_left != 1:
        sleep(args.time_to_sleep)
        still_project_names_left = main(args, logger)