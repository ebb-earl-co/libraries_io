#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" This is the main runner script for querying the Libraries.io
API, project contributors endpoint and loading the response (and error, if any)
to sqlite. As the API rate limits to 60 per minute, 60 or fewer API calls
will be made at a time, with `time.sleep` called between batches.
"""

from functools import partial
import itertools as it

from ratelimit import limits
from requests import Session

from logger import return_logger
from utils.libraries_io_project_contributors_endpoint import \
    build_get_request, parse_request_response_content, URL
from utils.utils import (connect, craft_sqlite_project_names_page_update,
                         craft_sqlite_project_names_page_insert, return_parser,
                         select_from_sqlite, execute_sqlite_query, Binary, Row)


def chunk(i, n):
    """ Return an iterable representing `l` split into `n`-sized chunks.
    Credit to https://stackoverflow.com/a/22049333
    Args:
        i (iterable): iterable the contents of which will be chunked
        n (int): into how many chunks to divide `i`
    Returns:
        (tuple): of size `n`
    """
    to_be_iterated = iter(i)
    return iter(lambda: tuple(it.islice(to_be_iterated, n)), ())


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
    # in the response's PreparedRequest attribute, the url has &-delineated
    # parameter key=value pairs. The page that was just requested is e.g.
    # &page=1&... and is the only parameter that startswith page
    page = \
        int(next(filter(lambda param: param if param.startswith('page') else None,
                        response.request.url.split('&')))[-1])
    yield (project_name, page, response)
    next_page = response.links.get('next')
    if next_page is not None:
        request = build_get_request(next_page['url'], False)
        prepared_request = session.prepare_request(request)
        # yield from request_with_session(session, project_name, prepared_request)


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
    request_ = partial(request_with_session, s)

    project_names_and_prepared_requests = \
        map(lambda pn, request, s=s: (pn, s.prepare(request)), batch)
    project_names_pages_responses = map(lambda pn_pr: request_(*pn_pr),
                                        project_names_and_prepared_requests)
    # Return an it.groupby object here? So that the `api_queried_successful`
    # field can be calculated for a project? Or just go forward with having the
    # switch pertain to the (project_name, page) tuple..?
    return project_names_pages_responses


def main():
    query = """select project_name as name from project_names
    where api_has_been_queried is null group by project_name"""
    with connect('../libraries_io.db') as conn:
        conn.row_factory = Row
        cur = conn.cursor()
        project_names = [row['name'] for row in cur.execute(query)]

    project_names_and_requests = \
        ((project_name, build_get_request(URL % project_name, True, 100, 1))
         for project_name in project_names)
    batches = chunk(project_names_and_requests, 60)
    projects_pages_responses = it.chain.from_iterable(
        map(request_batch, batches)
    )
    # TODO: map the above tuple through the craft_sqlite... function
    sqlite_fields = map(lambda x: x, projects_pages_responses)

    with connect('../libraries_io.db') as conn:
        sqlite_args = map(lambda fields: (conn, fields), sqlite_fields)
        return_codes = it.starmap(execute_sqlite_query, sqlite_args)
        successfully_updated = sum(map(lambda rc: rc == 0, return_codes))

    return successfully_updated


if __name__ == "__main__":
    main()