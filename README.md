# Analyzing Libraries.io with Neo4j to Find the Most Influential PyPi Contributor
## Libraries.io
[PyPi](https://pypi.org/) is the repository for Python packages that developers 
know and love and its corresponding tool, [`pip`](https://pip.pypa.io/en/stable/), 
is endorsed by the [Python Packaging Authority](https://www.pypa.io/en/latest/)
as **the** executable to search, publish (let's be honest, we all `pip install`
_much_ more than we upload to `pip`), and download Python packages.

Analogously to PyPi, other programming languages have their respective package
managers, such as CRAN for `R`. As a natural exercise in abstraction, 
[Libraries.io](https://libraries.io) is a meta-repository for 
package managers. From [their website](https://libraries.io/data):

> Libraries.io gathers data from **36** package managers and **3** source code repositories. 
We track over **2.7m** unique open source packages, **33m** repositories and **235m**
interdependencies between [sic] them. This gives Libraries.io a unique understanding of 
open source software. An understanding that we want to share with **you**.

Libraries.io has an easy-to-use web interface, a permissive license, as well as
an extensive [API](https://libraries.io/api).
