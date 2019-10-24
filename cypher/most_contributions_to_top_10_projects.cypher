MATCH (:Language {name: 'Python'})<-[:IS_WRITTEN_IN]-(p:Project)<-[:HOSTS]-(:Platform {name: 'Pypi'})
WHERE p.pypi_degree_centrality_rank <= 10
MATCH (c:Contributor)-[ct:CONTRIBUTES_TO]->(p)
WITH distinct c, COUNT(ct) AS num_top_10_contributed_to
WHERE num_top_10_contributed_to > 0
RETURN c, num_top_10_contributed_to ORDER BY num_top_10_contributed_to DESC
;
