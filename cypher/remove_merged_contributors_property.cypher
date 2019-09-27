MATCH (:Language {name: 'Python'})<-[:IS_WRITTEN_IN]-(p:Project)<-[:HOSTS]-(:Platform {name: 'Pypi'})
with p
CALL apoc.create.removeProperties(p, ["merged_contributors"])
yield node
return null;