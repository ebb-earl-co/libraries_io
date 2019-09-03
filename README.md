# Finding the Most Influential PyPi Contributor using Neo4j and Libraries.io Open Data
Upon coming across the excellent [`pipenv`](https://pipenv.readthedocs.io/en/latest/) 
package, written by Kenneth Reitz (he of [`requests`](https://requests.readthedocs.io/en/latest/)
fame), I wondered whether the adoption of this package by the Python Packaging 
Authority as the go-to 
[dependency manager for Python](https://packaging.python.org/guides/tool-recommendations/#application-dependency-management)
makes Kenneth Reitz the most influential Python contributor on PyPi. After all, 
his mantra when developing a package is "<_Insert programming activity here_> for __humans__".
## Summary of Results

For how we arrived at this, read on.
## The Approach
### Libraries.io Open Data
[PyPi](https://pypi.org/) is the repository for Python packages that developers
know and love. Analogously to PyPi, other programming languages have their respective package
managers, such as CRAN for `R`. As a natural exercise in abstraction, 
[Libraries.io](https://libraries.io) is a meta-repository for 
package managers. From [their website](https://libraries.io/data):

> Libraries.io gathers data from **36** package managers and **3** source code repositories. 
We track over **2.7m** unique open source packages, **33m** repositories and **235m**
interdependencies between [sic] them. This gives Libraries.io a unique understanding of 
open source software. An understanding that we want to share with **you**.

#### Exploring Open Data Snapshot to Save API Calls
Libraries.io has an easy-to-use [API](https://libraries.io/api), but
given that PyPi is the fourth-most-represented package manager in the Open Data
with 200,000+ packages, the number of API calls to various endpoints to collate 
the necessary data is not appealing. Fortunately, 
[Jeremy Katz on Zenodo](https://zenodo.org/record/2536573) maintains snapshots 
of the Libraries.io Open Data source. The most recent version is a snapshot from
22 December 2018, and contains the following CSV files:
  1. Projects
  2. Versions
  3. Tags
  4. Dependencies
  5. Repositories
  6. Repository dependencies
  7. Projects with Related Repository Fields

**WARNING**: The tar.gz file that contains these data is 12 GB itself, and
once downloaded takes quite a while to un`tar`; once expanded, the data
take up GB on disk.

### Graph Databases, Starring Neo4j
Because of the interconnected nature of software packages (dependencies,
versions, maintainers, etc.), finding the most influential "item" in that web 
of data make [graph databases](https://db-engines.com/en/ranking/graph+dbms) and 
[graph theory](https://medium.freecodecamp.org/i-dont-understand-graph-theory-1c96572a1401)
the ideal tools for this type of analysis. [Neo4j](https://neo4j.com/product/)
is the most popular graph database according to [DB engines](https://neo4j.com/product/),
and is the one that we will use for this project.
Part of the reason for its popularity is that its query language,
[Cypher](https://neo4j.com/developer/cypher-query-language/), is expressive and simple:

![example graph](example_graph.png)

Terminology that will be useful going forward:
  - `Jane Doe` and `John Smith` are __nodes__ (equivalently: __vertexes__)
  - The above two nodes have __label__ `Person`, with __property__ `name`
  - The line that connects the nodes is an __relationship__ (equivalently: __edge__)
  - The above relationship is of type `KNOWS`
  - `KNOWS`, and all Neo4j relationships, are __directed__; i.e. `Jane Doe`
  knows `John Smith`, but not the converse

### Making a Graph of CSV Data
[Importing from CSV](https://neo4j.com/docs/cypher-manual/3.5/clauses/load-csv/)
is one of the most common ways to create a Neo4j graph, and is how we will
proceed given that the Open Data snapshot un`tar`s into CSV files. However,
first a data model is necessary— what the entities that will be
represented as labelled nodes with properties, and what are the
relationships among them are going to be. Moreover, some settings of Neo4j
will have to be customized for proper and timely import from CSV.
