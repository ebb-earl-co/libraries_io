call algo.degree.stream(
	"MATCH (:Language {name:'Python'})<-[:IS_WRITTEN_IN]-(:Project)<-[:CONTRIBUTES_TO]-(c:Contributor) return id(c) as id",
    "MATCH (c1:Contributor)-[:CONTRIBUTES_TO]->(:Project)-[:HAS_VERSION]->(:Version)-[:DEPENDS_ON]->(:Project)<-[:CONTRIBUTES_TO]-(c2:Contributor) return id(c2) as source, id(c1) as target",
    {graph: 'cypher', write: False}
)
YIELD nodeId, score
RETURN algo.asNode(nodeId).name as contributor, algo.asNode(nodeId).login as github_login, score as degree_centrality_score
ORDER BY degree_centrality_score DESC;