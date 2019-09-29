#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script requests the Libraries.io API Project Contributors endpoint. Pass
the name of the project the contributors of which to be requested as the only
positional argument; e.g.

>>> python %s requests

The fetching of results is complicated by the `page` and `per_page` parameters
of the API. The max `per_page` allowed is 100, so if there are more than 100
contributors for a given project, the response's content must be checked and
the API called again until all `page`s of results are retreived. If the process
is successful, the combined JSON response is returned to STDOUT. Otherwise,
the error that occurred during the request(s) is returned in JSON format to STDOUT.
"""
import itertools
import json
import logging
import os
import sys
import traceback
from collections import namedtuple

from requests import Request, Session
from requests.exceptions import HTTPError

URL = "https://libraries.io/api/Pypi/%s/contributors"
content_and_error = namedtuple("ContentAndError", ["content", "error"])
logger = logging.getLogger(__name__)


def build_get_request(url, get_api_key=True, per_page=100, page=1):
    """ Given url, return requests.get object that is prepared with
    the keywords 'url', 'params' passed. N.b. the params are created
    internally because they are taken from ENV variables or user input.

    Args:
        url (str): the url to pass to requests.get; the API to request
        get_api_key (bool): whether to get 'APIKEY' from ENV vars
        per_page (int): the number of results to fetch
        page (int): the ith set of `per_page` results to fetch, i > 0
    Returns:
        (requests.Request): the requests.Request object for further processing
    """
    def get_api_key():
        api_key = os.environ.get("APIKEY")
        if api_key is None:
            print("'APIKEY' is not among environment variables!", file=sys.stderr)
            sys.exit(1)

        return api_key

    params = {"per_page": per_page, "page": page}
    if get_api_key:
        params.update({"api_key": get_api_key()})
    return Request("GET", url=url, params=params)


def parse_request_response_content(r):
    """ Given a `requests.Response` object, execute the GET request and return one of
    three JSON objects: 1) requests.HTTPError that arose; 2) Other Python
    exception that arose; or 3) The response in the form {"data": <response>}
    from the API.

    Args:
        r (requests.Reponse): response from requests.get operation
    Returns:
        (namedtuple): tuple of the form (r.content, Exception from r)
    """
    try:
        r.raise_for_status()
    except HTTPError as h:
        logger.warning(f"Requests threw an exception: {str(h)}")
        to_return = content_and_error(None,
                                      json.dumps({"HTTPError": str(h)}))
    except Exception as e:
        logger.warning(f"Exception occurred: {str(e)}")
        to_return = content_and_error(None,
                                      json.dumps({"Exception": str(e)}))
    else:
        logger.info(f"Request to {r.url.split('?')[0]} was successful")
        to_return = content_and_error(r.content, None)
    finally:
        r.close()

    return to_return


def main(argv=None):
    # Argument parsing
    if argv is None:
        argv = sys.argv

    if '-h' in argv or '--help' in argv:
        print(__doc__ % argv[0], file=sys.stderr)
        sys.exit(0)

    try:
        project_name = argv[1]
    except IndexError:
        print("Project name not passed", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        traceback.print_tb(e, file=sys.stderr)
        sys.exit(1)

    # Requesting from API
    per_page = 100
    s = Session()

    get_request = build_get_request(URL % project_name, per_page=per_page)
    prepared_request = s.prepare_request(get_request)
    response = s.send(prepared_request)
    response_contents = [response.json()]
    next_page = response.links.get("next", None)
    while next_page is not None:
        # The next_page["url"] has all parameters ready to go
        get_request = build_get_request(next_page["url"], get_api_key=False)
        prepared_request = s.prepare_request(get_request)
        response = s.send(prepared_request)
        response_contents.append(response.json())
        next_page = response.links.get("next", None)
    else:
        return list(itertools.chain(*response_contents))


if __name__ == '__main__':
    print(main())
