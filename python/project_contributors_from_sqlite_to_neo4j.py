#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Inspired by
https://markhneedham.com/blog/2015/07/23/neo4j-loading-json-documents-with-cypher/
"""
import json
import os

from logger import return_logger
from merge_contributors import merge_contributors, return_parser
from utils.get_pypi_python_projects_from_neo4j import get_neo4j_driver, getpass
from utils.utils import connect, execute_sqlite_query, select_from_sqlite, Row


def main():
    args = return_parser().parse_args()
    logger = return_logger(__name__, args.log_level,
                           args.logfile, args.logfile_level)

    select_query = f"""select project_name, contributors from {args.table}
    where api_has_been_queried=1 and api_query_succeeded=1 and
    merge_contributors_succeeded is null"""
    with connect(args.DB) as conn:
        conn.row_factory = Row
        select_query_result = select_from_sqlite(conn, select_query)
        # output is a list of tuples

    # Convert list of tuples to generator of dicts, parsing json, too
    projects_and_contributors = ({"project_name": record['project_name'],
                                  "contributors": json.loads(record['contributors'])}
                                 for record in select_query_result)

    merge_query = """
                  WITH $json as j
                  MERGE (c:Contributor {uuid: apoc.convert.toInteger(j.uuid)})
                  ON CREATE SET c.name=j.name,
                  c.github_id=j.github_id,
                  c.login=j.login,
                  c.host_type=j.host_type
                  """
    match_merge_query = """
                        WITH $json as j
                        MATCH (p:Project {name: $name})
                        MATCH (c:Contributor {uuid: apoc.convert.toInteger(j.uuid)})
                        MERGE (c)-[:CONTRIBUTES_TO]->(p)
                        """
    authentication = (args.neo4j_user,
                      os.environ.get('GRAPHDBPASS') or getpass('Graph DB Pass:'))
    neo4j_driver = get_neo4j_driver(args.neo4j_URI, authentication)
    with connect(args.DB) as conn:
        for p_c in projects_and_contributors:
            # Unpack dict from gen for easy passing
            p, contributors = (p_c['project_name'], p_c['contributors'])
            logger.info(f"Beginning MERGEing the {len(contributors)} "
                        f"contributors to project '{p}'")
            return_codes = []
            # For each `contributors` list, iterate its dicts
            for i, c in enumerate(contributors, 1):
                logger.debug(f"MERGEing contributor {i} "
                             f"(out of {len(contributors)}) for project "
                             f"{p} using query:\n{merge_query}\n")
                return_code = \
                    merge_contributors(neo4j_driver, merge_query,
                                       merge_query_params={"json": c},
                                       match_query=match_merge_query,
                                       match_query_params={"json": c, "name": p})
                return_codes.append(return_code)

            # Once all contributors have attempted to MERGE, try to update
            # SQLite
            logger.info(f"Finished MERGEing the {len(contributors)} "
                        f"contributors to project '{p}'")
            update_query = f"""UPDATE project_names SET
                            merge_contributors_succeeded=?
                            WHERE project_name='{p}'"""

            # Have a 1-or-0 code for the whole project completing MERGE
            # succesfully, because all the contributors are to be treated as a
            # batch; unless the whole batch is merged correctly, it's a no-go
            if all(code==0 for code in return_codes):
                out = execute_sqlite_query(conn, update_query, (1,))
            else:
                out = execute_sqlite_query(conn, update_query, (0,))

            if out is None:
                logger.warning("SQLite record corresponding to "
                                f"'{p}' DID NOT UPDATE")
            else:
                logger.info("SQLite record corresponding to "
                            f"'{p}' updated successfully")


if __name__ == "__main__":
    main()
