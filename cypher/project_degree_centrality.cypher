call algo.degree(
	"MATCH (:Language {name:'Python'})<-[:IS_WRITTEN_IN]-(p:Project)<-[:HOSTS]-(:Platform {name:'Pypi'}) return id(p) as id",
    "MATCH (p1:Project)-[:HAS_VERSION]->(:Version)-[:DEPENDS_ON]->(p2:Project) return id(p2) as source, id(p1) as target",
    {graph: 'cypher', write: true, writeProperty: 'pypi_degree_centrality'}
);

MATCH (:Language {name: 'Python'})<-[:IS_WRITTEN_IN]-(p:Project)<-[:HOSTS]-(:Platform {name: 'Pypi'})
WITH p ORDER BY p.pypi_degree_centrality DESC
WITH collect(p) as projects
FOREACH (project in projects
	| SET project.pypi_degree_centrality_rank = apoc.coll.indexOf(projects, project)+1
);
