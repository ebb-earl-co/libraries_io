#!/usr/bin/env python
# -*- coding: utf-8 -*-

from string import printable

from hypothesis import given, strategies as st
import pytest as pt
from py2neo.database import Cursor

from test_helpers.test_graph_database import TESTGRAPHDB, Language
from merge_contributors import *


def test_get_graph_password_env_variable_not_set(monkeypatch):
    monkeypatch.delenv(GRAPHDBPASS, raising=False)
    assert get_graph_password() is None


@given(st.text(min_size=0, alphabet=printable))
def test_get_graph_password_env_variable_set(monkeypatch, pw):
    monkeypatch.setenv(GRAPHDBPASS, pw, prepend=False)
    assert get_graph_password() == pw


def test_main_raise_sys_exit_1_when_env_variable_not_set(monkeypatch, capsys):
    monkeypatch.delenv(GRAPHDBPASS, raising=False)
    with pt.raises(SystemExit):
        main()


def test_main_stderr_when_env_variable_not_set(monkeypatch, capsys):
    monkeypatch.delenv(GRAPHDBPASS, raising=False)
    with pt.raises(SystemExit):
        main()
    _, err = capsys.readouterr()
    assert err == f"Environment variable {GRAPHDBPASS} not set. Cannot access graph DB\n"


@pt.fixture(scope="function")
def G():
    g = Graph(**TESTGRAPHDB)
    return g


@pt.fixture(scope="function")
def G_with_nodes():
    g = Graph(**TESTGRAPHDB)
    python = Language("Python")
    foo = Project(1, 'foo')
    bar = Project(2, 'bar')
    python.projects.add(foo)
    python.projects.add(bar)
    g.push(python)
    yield g
    g.delete_all()


@given(st.just("MATCH (p:Project) return p;"))
def test_execute_cypher_match_statement_empty_graph(G, statement):
    result = execute_cypher_match_statement(G, statement)
    assert isinstance(result, Cursor)


@given(st.just("MATCH (p:Project) return p;"))
def test_execute_cypher_match_statement_non_empty_graph(G, statement):
    result = execute_cypher_match_statement(G, statement)
    assert isinstance(result, Cursor)


@given(st.just("MATCH (p:Project) return p;"))
def test_return_Node_from_Cursor_empty_graph(G, statement):
    assert 0
