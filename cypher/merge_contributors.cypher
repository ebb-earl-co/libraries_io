// Merge contributors from JSON returned by Libraries.io API
MERGE (c:Contributor {uuid: $uuid}) ON CREATE SET c.name=$name, c.github_id=$github_id
