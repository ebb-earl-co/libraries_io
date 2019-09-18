1. Download tar.gz file from zenodo
2. Unzip, untar tar.gz file from Zenodo into CSVs
3. Extract Pypi data from CSVs
    a. Rename and filter projects CSV
    b. Rename and filter dependencies CSV
    c. Rename and filter versions CSV
4. Start Neo4j, install Graph algorithms and APOC
5. Run `schema.cypher`
6. Run Cypher: "CREATE (p:Platform {name: 'Pypi'})"
7. Run `projects_apoc.cypher`
8. Run `versions_apoc.cypher`
9. Run `dependencies_apoc.cypher`
10. Run `create_sqlite_db.py`
11. Run `initiate_sqlite_db_with_neo4j_project_names.py`
12. Run `request_libraries_io_load_sqlite.py`
    a. Retrieve project names from SQLite `batch_size` at a time,
    only the ones that have not been queried at all yet
        i. If there are none left, exit with code 1
        ii. Otherwise, go to step [b]
    b. Request Libraries.io API, project contributors endpoint for each project name
    c. Store the result of part [b] into SQLite (successful or not)
    d. Return to step [a]
13. Run `request_libraries_io_load_sqlite.py`, but querying for
records that have `api_has_been_queried=1 AND api_query_succeeded=0`.
Do as [12]
14. Run `project_contributors_from_sqlite_to_neo4j.py`, using SQLite
records in which `api_has_been_queried=1 AND api_query_succeeded=1`.
    a. Given a `project_name`, pick up its `contributors` field in 
    SQLite. If this is empty, return None
    b. If `contributors` is not empty, create a Neo4j driver
    c. Run `merge_contributors.py` for the `project_name` and `contributors`, returning result of Cypher MERGE query for each contributor
    d. If resulting dictionary has True value for `has_contributor_error`, rerun the project_name, contributor combo
15. Run as-of-yet-undefined script to execute `MATCH-MATCH-MERGE` operation on project nodes and contributor nodes
16. _Finally_, run query for degree centrality to find the most influential contributor to Pypi