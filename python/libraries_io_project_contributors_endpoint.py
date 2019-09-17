#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script requests the Libraries.io API Project Contributors endpoint. Pass
the name of the project the contributors of which to be requested as the only
positional argument; e.g.

>>> python %s requests

If the request is successful, the JSON response is returned to STDOUT. Otherwise
the error that occurred during the request is returned in JSON format to STDOUT.
"""
import json
import logging
import os
import sys
from collections import namedtuple

from requests import get as GET
from requests.exceptions import HTTPError

URL = "https://libraries.io/api/Pypi/%s/contributors"
content_and_error = namedtuple("ContentAndError", ["content", "error"])
logger = logging.getLogger(__name__)


def build_GET_request(url):
    """ Given url, return requests.get object that is prepared with
    the keywords 'url', 'params' passed. N.b. the params are created
    internally because they are taken from ENV variables or user input.

    Args:
        url (str): the url to pass to requests.get; the API to request
    Returns:
        (requests.get): the requests.get object for further processing
    """
    def get_api_key():
        api_key = os.environ.get("APIKEY")
        if api_key is None:
            logger.error("'APIKEY' is not among environment variables!")
            sys.exit(1)

        return api_key

    params = {"api_key": get_api_key()}
    return GET(url=url, params=params)


def execute_GET_request(r):
    """ Given a `requests.get` object, execute the GET request and return one of
    three JSON objects: 1) requests.HTTPError that arose; 2) Other Python
    exception that arose; or 3) The response in the form {"data": <response>}
    from the API.

    Args:
        r (requests.get): instantiated request object
    Returns:
        (namedtuple): tuple with first field: error, second: response content
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
        return 0

    try:
        project_name = argv[1]
    except IndexError:
        print("Project name not passed", file=sys.stderr)
        return 1

    # Requesting from API
    GET_request = build_GET_request(URL % project_name)
    return execute_GET_request(GET_request)

if __name__ == '__main__':
    sys.stdout.write(main())
