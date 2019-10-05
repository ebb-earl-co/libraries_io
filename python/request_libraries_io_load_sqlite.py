#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" This is the main runner script for querying the Libraries.io
API, project contributors endpoint and loading the response (and error, if any)
to sqlite. As the API rate limits to 60 per minute, 60 or fewer API calls
will be made at a time, with `time.sleep` called between batches.
"""

from collections import namedtuple
from functools import partial
import itertools as it
from typing import *

from backoff import on_exception, expo
from ratelimit import limits, sleep_and_retry, RateLimitException
from requests import Response, Session

from logger import return_logger
from utils.libraries_io_project_contributors_endpoint import \
    build_get_request, content_and_error, parse_request_response_content, URL
from utils.utils import (chunk, connect, craft_sqlite_project_names_update,
                         craft_sqlite_project_names_insert, partition,
                         return_parser, select_from_sqlite,
                         execute_sqlite_query, Binary, Row)


@on_exception(expo, RateLimitException, max_tries=10)
@limits(calls=59, period=59)
def request_with_session(session, project_name, prepared_request):
    """ Call `session`.send() on `prepared_request` object, yielding
    requests.Response object. If the Response object has a 'next' link,
    get the link and prepare a GET request with it: then pass the prepared
    request back to the function.

    Args:
        session (requests.Session): session in which to send requests
        project_name (str): the name of the project that is being requested
        prepared_request (requests.PreparedRequest): request ready to send
    Yields:
        (requests.Response): the response from prepared_request.url
    """
    response = session.send(prepared_request)
    page = \
        int(next(filter(lambda param: param if param.startswith('page') else None,
                        response.request.url.split('&')))[-1])
    logger.info(f"Sent request for project '{project_name}', page {page}")
    yield (project_name, page, response)
    next_page = response.links.get('next', None)
    if next_page is not None:
        request = build_get_request(next_page['url'], False)
        prepared_request = session.prepare_request(request)
        yield from request_with_session(session, project_name, prepared_request)


def request_batch(batch):
    """ Given a `batch` of tuples, execute the second value of the tuple in
    the context of a requests.Session, returning a tuple of the first value of
    the original tuple and the requests.Response object.
    Args:
        batch (iterable): iterable of (str, requests.Request) objects
    Returns:
        (iterable): of (str, requests.Response) objects
    """
    s = Session()
    request_: Callable = partial(request_with_session, s)

    project_names_and_prepared_requests: Iterator[Tuple] = \
        map(lambda tup, s=s: (tup[0], s.prepare_request(tup[1])), batch)
    project_names_pages_responses_generators: Iterator[Generator[Tuple[str, int, Response]]] = \
        map(lambda pn_pr: request_(*pn_pr), project_names_and_prepared_requests)
    project_names_pages_responses: Iter[Tuple[str, int, Response]] = \
        it.chain.from_iterable(project_names_pages_responses_generators)
    return project_names_pages_responses


def main():
    args = return_parser().parse_args()
    global logger
    logger = return_logger(__file__, args.log_level, args.logfile)

    query = f"""select project_name as name from {args.table}
        where api_has_been_queried is null group by project_name
        LIMIT {args.batch_size}"""

    with connect(args.DB, timeout=10) as conn:
        conn.row_factory = Row
        cur = conn.cursor()
        logger.info(f"Executing\n{query}\nto {args.DB}")
        project_names: List[str] = [row['name'] for row in cur.execute(query)]

    project_names_and_requests: Generator[Tuple[str, Request]] = \
        ((project_name, build_get_request(URL % project_name, True, 100, 1))
         for project_name in project_names)

    batches: Iterator[Tuple[Tuple[str, Request]]] = \
        chunk(project_names_and_requests, 60)

    projects_pages_responses: Iterator[Tuple[str, int, Response]] = \
        it.chain.from_iterable(map(request_batch, batches))

    projects_pages_content_and_errors: Iterator[Tuple[str, int, content_and_error]] = \
        map(lambda tup: (tup[0], tup[1], parse_request_response_content(tup[2])),
            projects_pages_responses)

    # Add `api_has_been_queried` field as 1 for all records
    projects_pages_ahbq_content_and_errors: Iterator[Tuple[str, int, int, content_and_error]] = \
        map(lambda tup: (tup[0], tup[1], 1, tup[2]), projects_pages_content_and_errors)

    # Add `api_query_succeeded` field as 1 or 0, depending on content_and_error
    projects_pages_ahbq_aqs_content_and_errors: Iterator[Tuple[str, int, int, int, content_and_error]] = \
        map(lambda tup: (tup[0], tup[1], tup[2], 1 if tup[3].error is None else 0, tup[3]),
            projects_pages_ahbq_content_and_errors)

    page_1_records, page_ge_2_records = \
        partition(lambda tup: tup[1] == 1, projects_pages_ahbq_aqs_content_and_errors)
    # Iterator[Tuple[str, int, int, int, content_and_error]]

    page_1_record_update_queries_parameters: Iterator[Tuple[str, Tuple[Union[None, str], Union[None, Binary]]]] = \
        map(lambda tup: (craft_sqlite_project_names_update(project_name=tup[0], page=tup[1], api_has_been_queried=tup[2], api_query_succeeded=tup[3]),
                         (tup[-1].error, Binary(tup[-1].content) if tup[-1].content is not None else None)),
            page_1_records)

    page_ge_2_record_insert_queries_parameters: Iterator[Tuple[str, Tuple[str, int, int, Union[None, str], Union[None, Binary]]]] = \
        map(lambda tup: (craft_sqlite_project_names_insert(), (tup[0], tup[1], tup[2], tup[3], tup[-1].error,
                         tup[-1].error, Binary(tup[-1].content) if tup[-1].content is not None else None)),
            page_ge_2_records)

    queries_and_parameters: Iterator[Tuple] = it.chain.from_iterable(
        (page_1_record_update_queries_parameters,
         page_ge_2_record_insert_queries_parameters)
    )

    with connect(args.DB, timeout=10) as conn:
        sqlite_args: Iterator[Tuple] = \
            map(lambda tup: (conn, *tup), queries_and_parameters)
        return_codes: Iterator[Union[int, None]] = \
            it.starmap(execute_sqlite_query, sqlite_args)
        successfully_queried: int = sum(map(lambda rc: rc == 0, return_codes))

    logger.info(f"{successfully_queried} records successfully inserted/updated")


if __name__ == "__main__":
    main()