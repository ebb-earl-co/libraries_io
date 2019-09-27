MATCH (:Language {name: 'Python'})<-[:IS_WRITTEN_IN]-(p:Project)<-[:HOSTS]-(:Platform {name: 'Pypi'})
with p
CALL apoc.create.setProperty(p, "merged_contributors", -1)
yield node
return null;