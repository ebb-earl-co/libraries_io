#!/bin/sh

# Run this from the Neo4j installation location
# On MacOS Neo4j Desktop this is:
# /Users/<USERNAME>/Library/Application Support/Neo4j Desktop/Application/neo4jDatabases/database-<DATABASE_HASH>/installation-3.5.7
# N.b. the below command requires apoc.export.file.enabled=true to be in neo4j.conf

# SANITY CHECKS: There should be 1,507,772 nodes (5 labels) and 2,211,907 relationships (6 types)
# present in the files produced by this command

PATH_TO_OUTDIR=$PWD
JAVA_OPTS=-Xmx4G bin/cypher-shell --format=verbose "call apoc.export.cypher.all('${PATH_TO_OUTDIR}', {format:'neo4j-shell', separateFiles:true, cypherFormat:'create', useOptimizations:{unwindBatchSize:1000,type:'UNWIND_BATCH'}}) yield time return time;"