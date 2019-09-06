// https://neo4j-contrib.github.io/neo4j-apoc-procedures/#_transaction_batching
CALL apoc.periodic.iterate(
    'CALL apoc.load.csv({filename}) yield map return map',
    'MERGE (pr:Project {name: map["Name"], ID: apoc.convert.toInteger(map["ID"]), sourcerank: apoc.convert.toInteger(map["SourceRank"]), versions_count: apoc.convert.toInteger(map["Versions Count"])})',
     {batchSize:2000, iterateList:true, parallel:true}
)
;

CALL apoc.periodic.iterate(
    'CALL apoc.load.csv({filename}) yield map return map',
    'MATCH (pl:Platform {name: map["Platform"]}) MATCH (pr:Project {ID: apoc.convert.toInteger(map["ID"])}) MERGE (pl)-[:HOSTS]->(pr)',
     {batchSize:10000, iterateList:true, parallel:true}
)
;

CALL apoc.periodic.iterate(
    'CALL apoc.load.csv({filename}) yield map return map',
    'MATCH (pr:Project {name: map["Name"]}) MATCH (l:Language {name: map["Language"]}) MERGE (pr)-[:IS_WRITTEN_IN]->(l)',
    {batchSize:10000, iterateList:true, parallel:true}
)
;
