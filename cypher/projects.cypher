CALL apoc.load.csv($filename) yield map
MERGE (pr:Project {
    name: map["Name"]
    , ID: apoc.convert.toInteger(map["ID"])
    , sourcerank: apoc.convert.toInteger(map["SourceRank"])
    , versions_count: apoc.convert.toInteger(map["Versions Count"])
    })
;

CALL apoc.load.csv($filename) yield map
MATCH (pl:Platform {name: map["Platform"]})
MATCH (l:Language {name: map["Language"]})
MATCH (pr:Project {ID: apoc.convert.toInteger(map["ID"])})
MERGE (pr)-[:IS_WRITTEN_IN]->(l)
;

CALL apoc.load.csv($filename) yield map
MATCH (pl:Platform {name: map["Platform"]})
MATCH (pr:Project {ID: apoc.convert.toInteger(map["ID"])})
MERGE (pl)-[:HOSTS]->(pr)
;