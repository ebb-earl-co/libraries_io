1. Download tar.gz file from zenodo
2. Unzip, untar tar.gz file from Zenodo into CSVs
3. Extract Pypi data from CSVs
    a. Rename and filter projects CSV
    b. Rename and filter dependencies CSV
    c. Rename and filter versions CSV
4. Start Neo4j, install Graph algorithms and APOC
5. Run `schema.cypher`
6. CREATE the Pypi `Platform`, the Python `Language`, and create their relationship, `HAS_DEFAULT_LANGUAGE`
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
14. Use Cypher to run `set_merged_contributors_property.cypher`. This
script adds a `merged_contributors` property to every Python `Project`
node, with the value -1. N.b.
  - The value -1 indicates that the particular node has not attempted
  to merge its `Contributor`s yet
  - The value is changed to 1 if the merge operation is successful
  - The value is changed to 0 if the merge operation is not successful
15. Run `merge_projects.py /path/to/SQLite.db -1`, using SQLite
records in which `api_has_been_queried=1 AND api_query_succeeded=1`.
    a. Get all project names, contributors that represent Python `Project`s on Pypi
    b. For each project, make a py2neo.Node for each of its contributors
    c. For each contributor, MERGE that contributor then MERGE its relationship
    with the project
16. For the nodes that failed (15), they have property `merged_contributors=0`. So,
run `merge_projects_with_py2neo.py /path/to/SQLite.db 0` in order to repeat the
process from (15) for the Project nodes the `Contributor`s of which were not MERGEd
17. Run the Cypher script `remove_merged_contributors_property.cypher` to remove
the `merged_contributors` property from all nodes. It was only necessary during
the previous operation, so can safely be unset.
18. _Finally_, run query for degree centrality to find the most influential contributor on Pypi
