MATCH (:Language {name: 'Python'})<-[:IS_WRITTEN_IN]-(p:Project)<-[:HOSTS]-(:Platform {name: 'Pypi'})
WITH p
MATCH (p)<-[ct:CONTRIBUTES_TO]-(c:Contributor)
WITH c, count(ct) AS num_total_contributions
RETURN c, num_total_contributions ORDER BY num_total_contributions DESC
;