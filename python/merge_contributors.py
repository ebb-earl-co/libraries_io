#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from contextlib import closing

logger = logging.getLogger(__name__)

# Merge contributors from JSON returned by Libraries.io API
query = """MERGE (c:Contributor {uuid: apoc.convert.toInteger($uuid)})
           ON CREATE SET
           c.name=$name,
           c.github_id=$github_id,
           c.login=$login,
           c.host_type=$host_type
           ;"""

keys = ("uuid", "name", "github_id", "login", "host_type")

get_keys_from_dict = \
    lambda d, k, fallback='': {key: d.get(key, fallback) for key in k}

get_contributor_keys_from_dict = \
    lambda d, fallback='': get_keys_from_dict(d, k=keys, fallback=fallback)


def merge_contributors(driver, project_name, query, contributors):
    """ Using `neo4j.DirectDriver` object, attempt executing `query`
    that is formatted using `project_name` and `contributors`.
    Returns:
        (dict): {`project_name`: [{contributor, successful, query, params}]}
    """
    output_array = []
    with closing(driver) as d:
        logger.info(f"Connected to Neo4j running on {driver.address}")
        with driver.session() as s:
            for i, contributor in enumerate(contributors, 1):
                cypher_params = get_contributor_keys_from_dict(contributor)
                logger.debug(f"MERGEing contributor {i} "
                             f"(out of {len(contributors)}) for project "
                             f"{project_name} using query:"
                             f"\n{query}\n and parameters:\n"
                             f"{cypher_params}")
                with s.begin_transaction() as tx:
                    try:
                        tx.run(merge_contributors_query, cypher_params)
                    except CypherError:
                        logger.error(f"COULD NOT MERGE contributor {i} "
                                     f"(out of {len(contributors)} for project "
                                     f"{project_name}, corresponding to\n"
                                     f"{contributor}", exc_info=True)
                        tx.rollback()
                        successful = False
                    except Exception:
                        logger.error("Exception occurred while executing\n"
                                     f"{query}", exc_info=True)
                        successful = False
                    else:
                        logger.info(f"Successfully MERGEd contributor {i} "
                                    f"(out of {len(contributors)}) for project "
                                    f"{project_name}")
                        tx.commit()
                        successful = True
                    finally:
                        output_array.append({"contributor": contributor,
                                             "number": i,
                                             "successful": successful,
                                             "query": query,
                                             "params": cypher_params})
            return {"project_name": project_name,
                    "result": output_array,
                    "has_contributor_error": \
                        any(map(lambda d: not d['successful'], output_array))}
