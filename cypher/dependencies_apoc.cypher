// https://neo4j.com/docs/labs/apoc/current/import/load-csv/#_transaction_batching
// According to csvstat, there are no NULL Dependency Project Name fields
CALL apoc.periodic.iterate(
    'CALL apoc.load.csv("pypi_dependencies.csv", {ignore:["ID","Version_Number","Dependency_Requirements","Dependency_Project_ID"]}) yield map return map',
    'MATCH (v:Version {ID: toInteger(map["Version_ID"])}) MATCH (proj:Project {name: map["Dependency_Name"]}) MERGE (proj)<-[d:DEPENDS_ON]-(v) ON CREATE SET d.kind=map["Dependency_Kind"], d.optional=apoc.convert.toBoolean(map["Optional_Dependency"])',
     {batchSize:2000, iterateList:true, parallel:true}
)
;
