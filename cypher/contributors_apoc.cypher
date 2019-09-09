// Which project nodes don't have contributors yet?
match (p:Project)
where not (p)<-[:CONTRIBUTES_TO]-()
// Take that project and use it to query API, get contributors
with p limit 1
with p.name as projectname
with apoc.static.get('libraries_io.api_key') as api_key, projectname
with 'https://libraries.io/api/Pypi/' + projectname + '/contributors?api_key=' + api_key as url, projectname
match (p:Project {name: projectname})
call apoc.load.json(url) yield value
// Merge the Contributor nodes and connect them to Project
merge (c:Contributor {uuid:apoc.convert.toInteger(value.uuid)}) ON CREATE SET c.name=value.name, c.github_id=apoc.convert.toInteger(value.github_id), c.login=value.login
merge (c)-[:CONTRIBUTES_TO]->(p)
;
