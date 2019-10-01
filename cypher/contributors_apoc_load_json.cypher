// Use apoc.periodic.commit on python projects, 59 at a time, 
// and the return condition could be that the pages property doesn't
// exist on a Node. That would require PUTTING the pages property on
// every node in the query, somehow...
// CALL apoc.periodic.commit(
// "MATCH (:Platform {name:'Pypi'})-[:HOSTS]->(p:Project)-[:IS_WRITTEN_IN]->(:Language {name:'Python'}) WITH p limit 59 CALL apoc.util.sleep(59000) WITH 'https://libraries.io/api/Pypi' + p.name + '/contributors' as URI, p CALL apoc.load.jsonParams(URI, {per_page:100, api_key:$APIKEY}, null) YIELD value as j WITH p SET p.pages=CASE WHEN length(j)=100 THEN [2] ELSE [1] END MERGE (c:Contributor{uuid:toInteger(j['uuid'])}) ON CREATE SET c.name=j['name'], c.github_id=j['github_id'], c.login=j['login'], c.host_type=j['host_type'] MERGE (c)-[:CONTRIBUTES_TO]->(p) RETURN CASE WHEN ", {APIKEY: $APIKEY}
//);
// TODO: fix this query; specifically the RETURN condition in apoc.periodic.commit

//MATCH (:Platform {name:'Pypi'})-[:HOSTS]->(p:Project)-[:IS_WRITTEN_IN]->(:Language {name:'Python'})
//WITH [p] as projects_list
MATCH (:Platform {name:'Pypi'})-[:HOSTS]->(p:Project)
WITH [(p)-[:IS_WRITTEN_IN]->(:Language {name:'Python'}) | p] as projects_list
CALL apoc.coll.partition(projects_list, 59) YIELD value AS projects_batches
FOREACH(batch in project_batches |
    UNWIND batch as p
    WITH 'https://libraries.io/api/Pypi' + p.name + '/contributors' AS URI, p
    CALL apoc.load.jsonParams(URI, {per_page:100, api_key:$APIKEY}, NULL) YIELD value AS j 
    WITH p, size(collect(j)) as num_contributors
    WITH p, CASE WHEN num_contributors=100 THEN [2] ELSE NULL END as pages_property
    SET p.pages=pages_property
    MERGE (c:Contributor{uuid:toInteger(j['uuid'])})
        ON CREATE SET c.name=j['name'], c.github_id=j['github_id'], c.login=j['login'], c.host_type=j['host_type']
    MERGE (c)-[:CONTRIBUTES_TO]->(p)
);