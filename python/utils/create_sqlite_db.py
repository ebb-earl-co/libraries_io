#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import traceback
from sqlite3 import connect, OperationalError


def main(argv=None):
    if argv is None:
        argv = sys.argv

    try:
        dbname = argv[1]
    except IndexError:
        print("Database name not passed", file=sys.stderr)
        return 1

    with connect(dbname) as conn:
        c = conn.cursor()
        try:
            c.execute("""create table project_names (
                project_name text not null,
                page int not null,
                api_has_been_queried integer,
                api_query_succeeded integer,
                execution_error text,
                contributors blob,
                ts timestamp,
                PRIMARY KEY(project_name, page))""")
        except OperationalError:
            print("Table has already been created", file=sys.stderr)
            return 0
        except Exception as e:
            traceback.print_tb(e, file=sys.stderr)
            return 1
        else:
            print("Table created successfully", file=sys.stderr)
            return 0
        finally:
            c.close()


if __name__ == "__main__":
    sys.exit(main())
