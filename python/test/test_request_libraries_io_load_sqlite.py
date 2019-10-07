#!/usr/bin/env python
# -*- coding: utf-8 -*-


from itertools import chain
from string import ascii_letters, digits, printable
import os
import sys
import types

from hypothesis import assume, given, strategies as st
from hypothesis.provisional import urls
import pytest as pt
from requests import get, Request, Session
import responses

from request_libraries_io_load_sqlite import *
from utils.libraries_io_project_contributors_endpoint import content_and_error


def get_api_key():
    api_key = os.environ.get("APIKEY")
    if api_key is None:
        print("'APIKEY' is not among environment variables!", file=sys.stderr)
        sys.exit(1)

    return api_key


@given(st.iterables(st.none()), st.integers())
def test_chunk__is_iterator(i, n):
    chunks = chunk(i, n)
    assert iter(chunks) is chunks


@given(st.iterables(st.none(), min_size=0, max_size=0),
       st.integers(min_value=1, max_value=1000))
def test_chunk__empty_list_yields_empty_generator(i, n):
    chunks = chunk(i, n)
    with pt.raises(StopIteration):
        next(chunks)


# @given(st.iterables(st.none(), min_size=1), st.integers(min_value=1))
# def test_chunk__chunks_recombine_into_original_list(l, n):
#     chunks = chunk(l, n)
#     all_chunks_list = list(chain.from_iterable(chunks))
#     assert all_chunks_list == l


@given(st.lists(st.none(), min_size=1),
       st.integers(min_value=1, max_value=1000))
def test_chunk__partitions_into_n_chunks(l, n):
    chunks = chunk(l, n)
    if len(l) == 1:
        assert list(chunks) == [(l[0],)]
    elif len(l) % n == 0:
        assert all(len(chunk) == n for chunk in chunks)
    else:
        remainder = list(chunks)[-1]
        assert len(remainder) == len(l) % n


def test_build_get_request__test_get_api_key__env_var_not_set_exits_1(capsys, monkeypatch):
    monkeypatch.delenv('APIKEY', raising=False)
    with pt.raises(SystemExit):
        get_api_key()
    _, err = capsys.readouterr()
    assert err == "'APIKEY' is not among environment variables!\n"


@given(st.text(alphabet=printable, min_size=1))
def test_build_get_request__test_get_api_key__env_var_set_returns_env_var(capsys, monkeypatch, apikey):
    monkeypatch.setenv('APIKEY', apikey, prepend=False)
    assert get_api_key() == apikey


@given(urls(), st.text(alphabet=printable, min_size=1))
def test_build_get_request__get_api_key_False_per_page_DEFAULT_page_DEFAULT(monkeypatch, url, apikey):
    monkeypatch.setenv('APIKEY', apikey, prepend=False)
    r = build_get_request(url, get_api_key=False)
    assert isinstance(r, Request)
    assert r.params == {'per_page': 100}


@given(urls(), st.text(alphabet=printable, min_size=1))
def test_build_get_request__get_api_key_True_per_page_DEFAULT_page_DEFAULT(monkeypatch, url, apikey):
    monkeypatch.setenv('APIKEY', apikey, prepend=False)
    r = build_get_request(url, get_api_key=True)
    assert isinstance(r, Request)
    assert r.url == url
    assert r.params == {'per_page': 100, 'api_key': apikey}


@given(urls(), st.text(alphabet=printable, min_size=1))
def test_build_get_request__get_api_key_False_per_page_NONE_page_DEFAULT(monkeypatch, url, apikey):
    monkeypatch.setenv('APIKEY', apikey, prepend=False)
    r = build_get_request(url, get_api_key=False, per_page=None)
    assert isinstance(r, Request)
    assert r.url == url
    assert r.params == {}


@given(urls(), st.text(alphabet=printable, min_size=1))
def test_build_get_request__get_api_key_True_per_page_NONE_page_DEFAULT(monkeypatch, url, apikey):
    monkeypatch.setenv('APIKEY', apikey, prepend=False)
    r = build_get_request(url, get_api_key=True, per_page=None)
    assert isinstance(r, Request)
    assert r.url == url
    assert r.params == {'api_key': apikey}


@given(urls(), st.text(alphabet=printable, min_size=1), st.integers(min_value=0))
def test_build_get_request__get_api_key_False_per_page_DEFAULT_page_INT(monkeypatch, url, apikey, page):
    monkeypatch.setenv('APIKEY', apikey, prepend=False)
    r = build_get_request(url, get_api_key=False, page=page)
    assert isinstance(r, Request)
    assert r.url == url
    assert r.params == {'page': page, 'per_page': 100}


@given(urls(), st.text(alphabet=printable, min_size=1), st.integers(min_value=0))
def test_build_get_request__get_api_key_True_per_page_DEFAULT_page_INT(monkeypatch, url, apikey, page):
    monkeypatch.setenv('APIKEY', apikey, prepend=False)
    r = build_get_request(url, get_api_key=True, page=page)
    assert isinstance(r, Request)
    assert r.url == url
    assert r.params == {'page': page, 'per_page': 100, 'api_key': apikey}


@given(urls(),
       st.text(alphabet=printable, min_size=1),
       st.none(),
       st.integers(min_value=0))
def test_build_get_request__get_api_key_False_per_page_NONE_page_INT(monkeypatch, url, apikey, per_page, page):
    monkeypatch.setenv('APIKEY', apikey, prepend=False)
    r = build_get_request(url, get_api_key=False, per_page=per_page, page=page)
    assert isinstance(r, Request)
    assert r.url == url
    assert r.params == {'page': page}


@given(urls(),
       st.text(alphabet=printable, min_size=1),
       st.none(),
       st.integers(min_value=0))
def test_build_get_request__get_api_key_True_per_page_NONE_page_INT(monkeypatch, url, apikey, per_page, page):
    monkeypatch.setenv('APIKEY', apikey, prepend=False)
    r = build_get_request(url, get_api_key=True, per_page=per_page, page=page)
    assert isinstance(r, Request)
    assert r.url == url
    assert r.params == {'page': page, 'api_key': apikey}


@st.composite
def valid_project_name(draw):
    azAZ09 = ascii_letters + digits
    valid_python_name = azAZ09 + '.' + '-' + '_'
    name = draw(st.text(alphabet=valid_python_name, min_size=2))
    return name


@given(st.data())
def test_project_names_and_requests__single(monkeypatch, data):
    monkeypatch.setenv('APIKEY',
                       data.draw(st.text(alphabet=ascii_letters, min_size=1)),
                       prepend=False)
    project_name = data.draw(valid_project_name())
    project_name_and_request = \
        (project_name,
         build_get_request(data.draw(urls()) + project_name, True, 100, 1))
    assert isinstance(project_name_and_request[0], str)
    assert isinstance(project_name_and_request[1], Request)


@given(st.data())
def test_project_names_and_requests__many(monkeypatch, data):
    monkeypatch.setenv('APIKEY',
                       data.draw(st.text(alphabet=ascii_letters, min_size=1)),
                       prepend=False)
    num_projects = data.draw(st.integers(min_value=2, max_value=100))
    project_names = [data.draw(valid_project_name()) for _ in range(num_projects)]
    project_names_and_requests = \
        ((project_name, build_get_request(URL % project_name, True, 100, 1))
         for project_name in project_names)
    is_str_instance = lambda obj: isinstance(obj, str)
    is_Request_instance = lambda obj: isinstance(obj, Request)
    is_instance_tuples = map(lambda t: (is_str_instance(t[0]), is_Request_instance(t[1])),
                             project_names_and_requests)
    assert all(all(tup) for tup in is_instance_tuples)


@given(st.data())
def test_batches_produces_tuples(monkeypatch, data):
    monkeypatch.setenv('APIKEY',
                       data.draw(st.text(alphabet=ascii_letters, min_size=1)),
                       prepend=False)
    num_projects = data.draw(st.integers(min_value=2, max_value=120))
    project_names = [data.draw(valid_project_name()) for _ in range(num_projects)]
    project_names_and_requests = \
        ((project_name, build_get_request(URL % project_name, True, 100, 1))
         for project_name in project_names)
    batches = list(chunk(project_names_and_requests, 60))
    assert all(isinstance(batch, tuple) for batch in batches)
    assert all(len(batch) == 60 for batch in batches[:-1])


@responses.activate
@given(valid_project_name())
def test_parse_request_response_content__429_status_code(pn):
    responses.add(responses.GET, URL % pn, status=429)
    resp = get(URL % pn)
    c_and_e = parse_request_response_content(resp)
    assert resp.status_code == 429
    assert isinstance(c_and_e, content_and_error)


@responses.activate
@given(valid_project_name())
def test_parse_request_response_content__429_content_and_error(pn):
    responses.add(responses.GET, URL % pn, status=429)
    resp = get(URL % pn)
    c_and_e = parse_request_response_content(resp)
    assert c_and_e.content is None
    assert 'HTTPError' in c_and_e.error


@responses.activate
@given(valid_project_name())
def test_parse_request_response_content__200(pn):
    responses.add(responses.GET, URL % pn, status=200)
    resp = get(URL % pn)
    c_and_e = parse_request_response_content(resp)
    assert resp.status_code == 200
    assert isinstance(c_and_e, content_and_error)
    assert c_and_e.error is None
    assert c_and_e.content is not None


@responses.activate
@given(valid_project_name())
def test_parse_request_response_content__exception_occurred(pn):
    responses.add(responses.GET, URL % pn, body=Exception('...'))
    with pt.raises(Exception):
        resp = get(URL % pn)
        c_and_e = parse_request_response_content(resp)
        assert 'Exception' in c_and_e.error


@pt.fixture
def response_w_3_pages():
    with responses.RequestsMock() as rsps:
        url = '?'.join((URL % 'foobar', 'page=1&per_page=100'))
        rsps.add(responses.GET,
                 url,
                 headers={'Link': '<https://libraries.io/api/Pypi/foobar/contributors?page=3&per_page=100>; rel="last", <https://libraries.io/api/Pypi/foobar/contributors?page=2&per_page=100>; rel="next"'},
                 status=200)
        yield rsps


@pt.fixture(scope="function")
def session():
    s = Session()
    yield s


@responses.activate
@given(valid_project_name())
def test_request_with_session__single_page(pn):
    url = '?'.join((URL % pn, 'page=1&per_page=100'))
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(responses.GET, url, status=200, json=[])
        resp = get(URL % pn, params={'page': 1, 'per_page': 100})
        assert resp.status_code == 200
        assert resp.links.get('next', None) is None
        assert resp.json() == []


@responses.activate
@given(valid_project_name())
def test_request_with_session__multiple_pages_assert_next_page(pn):
    url = '?'.join((URL % pn, 'page=1&per_page=100'))
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(responses.GET,
                 url,
                 headers={'Link': f'<https://libraries.io/api/Pypi/{pn}/contributors?page=3&per_page=100>; rel="last", <https://libraries.io/api/Pypi/{pn}/contributors?page=2&per_page=100>; rel="next"'},
                 status=200)
        resp = get(url)
        next_page = resp.links.get('next', None)
        assert next_page['url'] == f'https://libraries.io/api/Pypi/{pn}/contributors?page=2&per_page=100'


@responses.activate
@given(valid_project_name())
def test_request_with_session__multiple_pages_assert_last_page(pn):
    url = '?'.join((URL % pn, 'page=1&per_page=100'))
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(responses.GET,
                 url,
                 headers={'Link': f'<https://libraries.io/api/Pypi/{pn}/contributors?page=3&per_page=100>; rel="last", <https://libraries.io/api/Pypi/{pn}/contributors?page=2&per_page=100>; rel="next"'},
                 status=200)
        resp = get(url)
        last_page = resp.links.get('last', None)
        assert last_page['url'] == f'https://libraries.io/api/Pypi/{pn}/contributors?page=3&per_page=100'
