MATCH (:Language {name: 'Python'})<-[:IS_WRITTEN_IN]-(p:Project)<-[:HOSTS]-(:Platform {name: 'Pypi'})
MATCH (p)<-[ct:CONTRIBUTES_TO]-(c:Contributor)
WITH c, COUNT(ct) AS num_projects_contributed_to
ORDER BY num_projects_contributed_to DESC
SET c.pypi_total_projects_contributed_to = num_projects_contributed_to
WITH collect(c) as contributors
FOREACH (contributor in contributors |
	SET contributor.pypi_total_projects_contributed_to_rank = apoc.coll.indexOf(contributors, contributor)+1
);
