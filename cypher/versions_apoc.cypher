CALL apoc.periodic.iterate(
    'CALL apoc.load.csv({filename}, {ignore:["Platform","Project Name","Project ID","Published Timestamp","Created Timestamp","Updated Timestamp"]}) yield map return map',
    'MERGE (v:Version {number: map["Number"], ID: map["ID"]})',
     {batchSize:2000, iterateList:true, parallel:true}
)
;

CALL apoc.periodic.iterate(
    'CALL apoc.load.csv({filename}, {ignore:["Platform","Project Name","Published Timestamp","Created Timestamp","Updated Timestamp"]}) yield map return map',
    'MATCH (v:Version {ID: map["ID"]}) MATCH (pr:Project {ID: map["Project ID"]}) MERGE (pr)-[:HAS_VERSION]->(v)',
     {batchSize:2000, iterateList:true, parallel:true}
)
;