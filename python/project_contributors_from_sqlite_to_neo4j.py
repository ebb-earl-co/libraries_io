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
    merge_contributors_succeeded is null;"""
    with connect(args.DB) as conn:
        conn.row_factory = Row
        select_query_result = select_from_sqlite(conn, select_query)

    projects_and_contributors = ({"project_name": record['project_name'],
                                  "contributors": json.loads(record['contributors'])}
                                 for record in select_query_result)

    merge_query = """
                  WITH $json as j
                  UNWIND j.contributors as contributors
                  FOREACH (contributor in contributors |
                  MERGE (c:Contributor {uuid: apoc.convert.toInteger(contributor.uuid)})
                  ON CREATE SET c.name=contributor.name,
                  c.github_id=contributor.github_id,
                  c.login=contributor.login,
                  c.host_type=contributor.host_type)
                  """
    match_merge_query = """
                        WITH $json as j
                        UNWIND j.contributors as contributors
                        MATCH (p:Project {name: $name})
                        FOREACH (contributor in contributors |
                            MERGE (c:Contributor {uuid: apoc.convert.toInteger(contributor.uuid)})
                            MERGE (c)-[:CONTRIBUTES_TO]->(p)
                        )
                        """
    authentication = (args.neo4j_user,
                      os.environ.get('GRAPHDBPASS') or getpass('Graph DB Pass:'))
    neo4j_driver = get_neo4j_driver(args.neo4j_URI, authentication)
    output = []
    with connect(args.DB) as conn:
        for p_c in projects_and_contributors:
            project_name, contributors = (p_c['project_name'], p_c['contributors'])
            logger.info(f"Beginning MERGEing the {len(contributors)} "
                        f"contributors to project '{project_name}'")
            return_codes = []
            for i, contributor in enumerate(contributors, 1):
                logger.debug(f"MERGEing contributor {i} "
                             f"(out of {len(contributors)}) for project "
                             f"{project_name} using query:"
                             f"\n{merge_query}\n")
                return_code = \
                    merge_contributors(neo4j_driver, merge_query,
                                       merge_query_params={"json": contributor},
                                       match_query=match_merge_query,
                                       match_query_params={"json": contributor,
                                                           "name": project_name})
                update_query = f"""UPDATE project_names SET
                                merge_contributors_succeeded=?
                                WHERE project_name='{project_name}'"""
                return_codes.append(return_code)
            else:
                logger.info(f"Finished MERGEing the {len(contributors)} "
                            f"contributors to project '{project_name}'")

            if all(code==0 for code in return_codes):
                out = execute_sqlite_query(conn, update_query, (1,))
            else:
                out = execute_sqlite_query(conn, update_query, (0,))

            if out is None:
                logger.warning("SQLite record corresponding to "
                                f"'{project_name}' DID NOT UPDATE")
            else:
                logger.info("SQLite record corresponding to "
                            f"'{project_name}' updated successfully")


if __name__ == "__main__":
    main()
