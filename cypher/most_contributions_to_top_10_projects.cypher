MATCH (:Language {name: 'Python'})<-[:IS_WRITTEN_IN]-(p:Project)<-[:HOSTS]-(:Platform {name: 'Pypi'})
WHERE p.name in ["requests","six","python-dateutil","setuptools","PyYAML","click","lxml","futures","boto3","Flask"]
WITH p
MATCH (c:Contributor)-[ct:CONTRIBUTES_TO]->(p)
WITH c, COUNT(ct) AS num_top_10_contributed_to
WHERE num_top_10_contributed_to > 0
RETURN c, num_top_10_contributed_to ORDER BY num_top_10_contributed_to DESC
;