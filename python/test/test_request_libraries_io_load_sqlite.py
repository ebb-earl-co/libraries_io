#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import chain
from string import printable
import os
import sys
import types

from hypothesis import given, strategies as st
from hypothesis.provisional import urls
import pytest as pt
import responses
from requests import Request

from request_libraries_io_load_sqlite import *

def get_api_key():
    api_key = os.environ.get("APIKEY")
    if api_key is None:
        print("'APIKEY' is not among environment variables!", file=sys.stderr)
        sys.exit(1)

    return api_key


@given(st.lists(st.none()), st.integers())
def test_chunk__is_generator(l, n):
    chunks = chunk(l, n)
    assert isinstance(chunks, types.GeneratorType)


@given(st.lists(st.none(), min_size=0, max_size=0), st.integers(min_value=1))
def test_chunk__empty_list_yields_empty_generator(l, n):
    chunks = chunk(l, n)
    with pt.raises(StopIteration):
        next(chunks)


@given(st.lists(st.none(), min_size=1), st.integers(min_value=1))
def test_chunk__chunks_recombine_into_original_list(l, n):
    chunks = chunk(l, n)
    all_chunks_list = list(chain.from_iterable(chunks))
    assert all_chunks_list == l


@given(st.lists(st.none(), min_size=1), st.integers(min_value=1))
def test_chunk__partitions_into_n_chunks(l, n):
    chunks = chunk(l, n)
    if len(l) == 1:
        assert list(chunks) == [l]
    elif len(l) % n == 0:
        assert all(len(chunk) == n for chunk in chunks)
    else:
        remainder = list(chunks)[-1]
        assert len(remainder) == len(l) % n


@pt.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pt.fixture
def session():
    s = Session()
    yield s


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
