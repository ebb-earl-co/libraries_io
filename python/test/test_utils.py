#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
from string import printable

import pytest as pt
from hypothesis import given, strategies as st

from utils.utils import (return_parser, select_from_sqlite,
                         connect, IntegrityError, OperationalError)


@pt.fixture(scope="function")
def sqlitedb_empty():
    conn = connect("empty.db")
    yield conn
    conn.close()
    os.remove("empty.db")


@pt.fixture(scope="function")
def sqlitedb():
    conn = connect("test.db")
    conn.execute("CREATE TABLE foo(bar integer not null);")
    conn.executemany("INSERT INTO foo(bar) VALUES (?)", [(1,), (2,), (3,)])
    yield conn
    conn.close()
    os.remove("test.db")


# @given(st.text(alphabet=printable),  # project_name
#        st.one_of(st.integers(min_value=0, max_value=1), st.none()),  # api_has_been_queried
#        st.one_of(st.integers(min_value=0, max_value=1), st.none()),  # api_query_succeeded
#        st.one_of(st.text(alphabet=printable), st.none()),  # execution_error
#        st.one_of(st.binary(), st.none()),  # contributors
#        st.one_of(st.datetimes(), st.none()))  # ts
# def test_craft_sqlite_project_names_record(p, ah, aq, e, c, ts):
#     query_and_record = craft_sqlite_project_names_record(p, ah, aq, e, c, ts)
#     assert isinstance(query_and_record, tuple)
#     assert query_and_record[1] == (p, ah, aq, e, c, ts)
#     assert query_and_record[0] == \
#         ("insert into project_names(project_name, "
#          "api_has_been_queried, api_query_succeeded, "
#          "execution_error, contributors, ts) "
#          "values (?, ?, ?, ?, ?, ?)")


def test_select_from_sqlite_empty_db(sqlitedb_empty, caplog):
    caplog.set_level(logging.INFO)
    query = "select * from foo;"
    res = select_from_sqlite(sqlitedb_empty, query)
    assert res is None
    for record in caplog.records:
        assert record.levelname in ('ERROR', 'WARNING')
    assert 'SQLite error occurred' in caplog.text


def test_select_from_sqlite_no_params(sqlitedb, caplog):
    caplog.set_level(logging.INFO)
    query = "SELECT bar from foo where bar is not null"
    params = None
    res = select_from_sqlite(sqlitedb, query, params)
    assert res == [(1,), (2,), (3,)]
    assert caplog.text.endswith(f"Fetched {len(res)} records\n")


def test_select_from_sqlite_with_params(sqlitedb, caplog):
    caplog.set_level(logging.INFO)
    query = "SELECT bar from foo where bar > ?"
    params = (1,)
    res = select_from_sqlite(sqlitedb, query, params)
    assert res == [(2,), (3,)]
    assert caplog.text.endswith(f"Fetched {len(res)} records\n")


# def test_insert_into_sqlitedb_empty_db(sqlitedb_empty, caplog):
#     caplog.set_level(logging.INFO)
#     query = "insert into foo(bar) values ('foobar');"
#     insert_into_sqlite(sqlitedb_empty, query)
#     assert 'OperationalError' in caplog.text
#
#
# def test_insert_into_sqlitedb_integrity_error(sqlitedb, caplog):
#     caplog.set_level(logging.INFO)
#     query = "INSERT INTO foo(bar) values (?);"
#     params = (None,)
#     insert_into_sqlite(sqlitedb, query, params)
#     assert 'IntegrityError' in caplog.text
#
#
# def test_insert_into_sqlitedb(sqlitedb, caplog):
#     caplog.set_level(logging.INFO)
#     query = "INSERT INTO foo(bar) values (?);"
#     params = (5,)
#     res = insert_into_sqlite(sqlitedb, query, params)
#     assert res is None
#     assert f'Inserted {len(params)} records\n' in caplog.text
