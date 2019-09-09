// According to csvstat, there are no NULL Dependency Project Name fields
CALL apoc.periodic.iterate(
    'CALL apoc.load.csv({filename}) yield map return map',
    'MATCH (v:Version {ID: apoc.convert.toInteger(map["Version_ID"])}) MATCH (proj:Project {name: map["Dependency_Name"]}) MERGE (proj)-[d:DEPENDS_ON]->(v) ON CREATE SET d.kind=map["Dependency_Kind"], d.optional=apoc.convert.toBoolean(map["Optional_Dependency"])',
     {batchSize:2000, iterateList:true, parallel:true}
)
; 
