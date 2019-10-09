MATCH (:Language {name: 'Python'})<-[:IS_WRITTEN_IN]-(p:Project)<-[:HOSTS]-(:Platform {name: 'Pypi'})
WITH p
MATCH (p)<-[ct:CONTRIBUTES_TO]-(c:Contributor)
WHERE NOT c.name CONTAINS 'bot'
WITH c, COUNT(ct) AS num_projects_contributed_to
ORDER BY num_projects_contributed_to DESC
WITH collect(c) as contributors
UNWIND contributors as contributor
return contributor, apoc.coll.indexOf(contributors, contributor)+1 as rank;
