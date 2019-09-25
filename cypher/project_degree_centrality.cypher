call algo.degree.stream(
	"MATCH (:Language {name:'Python'})<-[:IS_WRITTEN_IN]-(p:Project)<-[:HOSTS]-(:Platform {name:'Pypi'}) return id(p) as id",
    "MATCH (p1:Project)-[:HAS_VERSION]->(:Version)-[:DEPENDS_ON]->(p2:Project) return id(p2) as source, id(p1) as target",
    {graph: 'cypher', write: False}
)
YIELD nodeId, score
RETURN algo.asNode(nodeId).name as project, score as degree_centrality_score
ORDER BY degree_centrality_score DESC
;