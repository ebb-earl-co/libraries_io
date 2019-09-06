CALL apoc.periodic.iterate(
    'CALL apoc.load.csv({filename}, {ignore:["Platform","Project_Name","Project_ID","Published_Timestamp","Created_Timestamp","Updated_Timestamp"]}) yield map return map',
    'MERGE (v:Version {number: map["Number"], ID: apoc.convert.toInteger(map["ID"])})',
     {batchSize:2000, iterateList:true, parallel:true}
)
;

CALL apoc.periodic.iterate(
    'CALL apoc.load.csv({filename}, {ignore:["Platform","Project_Name","Published_Timestamp","Created_Timestamp","Updated_Timestamp"]}) yield map return map',
    'MATCH (v:Version {ID: apoc.convert.toInteger(map["ID"])}) MATCH (pr:Project {ID: apoc.convert.toInteger(map["Project_ID"])}) MERGE (pr)-[:HAS_VERSION]->(v)',
     {batchSize:2000, iterateList:true, parallel:true}
)
;