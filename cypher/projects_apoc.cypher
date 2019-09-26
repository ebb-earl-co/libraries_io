// https://neo4j.com/docs/labs/apoc/current/import/load-csv/#_transaction_batching
CALL apoc.periodic.iterate(
    'CALL apoc.load.csv("pypi_projects.csv", {ignore: ["Created_Timestamp","Updated_Timestamp","Description","Keywords","Homepage_URL","Licenses","Repository_URL","Latest_Release_Publish_Timestamp","Latest_Release_Number","Package_Manager_ID","Dependent_Projects_Count","Language","Status","Last_Synced_Timestamp","Dependent_Repositories_Count","Repository_ID"]}) yield map return map',
    'MERGE (pr:Project {name: map["Name"], ID: toInteger(map["ID"]), sourcerank: toInteger(map["SourceRank"]), versions_count: toInteger(map["Versions_Count"])})',
     {batchSize:2000, iterateList:true, parallel:true}
)
;
CALL apoc.periodic.iterate(
    'CALL apoc.load.csv("pypi_projects.csv",{ignore: ["Created_Timestamp","Updated_Timestamp","Description","Keywords","Homepage_URL","Licenses","Repository_URL","Versions_Count","SourceRank","Latest_Release_Publish_Timestamp","Latest_Release_Number","Package_Manager_ID","Dependent_Projects_Count","Language","Status","Last_Synced_Timestamp","Dependent_Repositories_Count","Repository_ID"]}) yield map return map',
    'MATCH (pl:Platform {name: map["Platform"]}) MATCH (pr:Project {ID: toInteger(map["ID"])}) MERGE (pl)-[:HOSTS]->(pr)',
     {batchSize:2000, iterateList:true, parallel:false}
)
;
CALL apoc.load.csv("pypi_projects.csv",{ignore: ["Name","Created_Timestamp","Updated_Timestamp","Description","Keywords","Homepage_URL","Licenses","Repository_URL","Versions_Count","SourceRank","Latest_Release_Publish_Timestamp","Latest_Release_Number","Package_Manager_ID","Dependent_Projects_Count","Status","Last_Synced_Timestamp","Dependent_Repositories_Count","Repository_ID"]}) yield map
MATCH (pr:Project {ID: toInteger(map["ID"])}) MATCH (l:Language {name: map["Language"]}) MERGE (pr)-[:IS_WRITTEN_IN]->(l)
;
