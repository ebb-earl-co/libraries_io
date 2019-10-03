#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from utils.create_sqlite_db import connect, main


def test_main_no_argument_passed(capsys):
    argv = [__name__]
    out = main(argv)
    _, err = capsys.readouterr()
    assert out == 1
    assert err == "Database name not passed\n"


def test_main_sqlitedb_does_not_exist(capsys):
    argv = [__name__, 'test.db']
    return_value = main(argv)
    out, err = capsys.readouterr()

    assert return_value == 0
    assert err == "Table created successfully\n"
    assert os.path.isfile(argv[1])


def test_main_sqlitedb_does_exist(capsys):
    argv = [__name__, 'test.db']
    return_value = main(argv)
    out, err = capsys.readouterr()

    assert return_value == 0
    assert err == "Table has already been created\n"
    assert os.path.isfile(argv[1])
    os.remove(argv[1])


def test_main_sqlite_table():
    argv = [__name__, 'test.db']
    main(argv)
    query = """SELECT name FROM sqlite_master WHERE type='table'"""
    with connect(argv[1]) as conn:
        cur = conn.cursor()
        cur.execute(query)
        tables = cur.fetchall()
    assert 'project_names' in [row[0] for row in tables]
    os.remove(argv[1])
