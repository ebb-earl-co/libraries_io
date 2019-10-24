call algo.degree(
    "MATCH (:Platform {name:'Pypi'})-[:HOSTS]->(p:Project) with p MATCH (:Language {name:'Python'})<-[:IS_WRITTEN_IN]-(p)<-[:CONTRIBUTES_TO]-(c:Contributor) return id(c) as id",
    "MATCH (c1:Contributor)-[:CONTRIBUTES_TO]->(:Project)-[:HAS_VERSION]->(:Version)-[:DEPENDS_ON]->(:Project)<-[:CONTRIBUTES_TO]-(c2:Contributor) return id(c2) as source, id(c1) as target",
    {graph: 'cypher', write: true, writeProperty: 'pypi_degree_centrality'}
);

CREATE INDEX ON :Contributor(pypi_degree_centrality)
;

MATCH (:Language {name: 'Python'})<-[:IS_WRITTEN_IN]-(p:Project)<-[:HOSTS]-(:Platform {name: 'Pypi'})
MATCH (p)<-[:CONTRIBUTES_TO]-(c:Contributor)
WITH c ORDER BY c.pypi_degree_centrality DESC
WITH collect(distinct c) as contributors
UNWIND contributors as contributor
SET contributor.pypi_degree_centrality_rank = apoc.coll.indexOf(contributors, contributor) + 1
;
