# Selecting Pypi Data from Open Data Dataset
The subsetting of the Libraries.io Open Data CSVs uses 
[Miller](https://johnkerl.org/miller/doc/index.html), invoked as `mlr`,
probably the best command-line tool available for manipulation of large
CSV files.
If un`tar`red correctly, the following are the sizes of the files:

 - `projects.csv`:
```bash
$ wc -l projects.csv
 3333927
``` 
and after filtering for just Python packages on Pypi:
```bash
$ mlr --icsv --opprint filter '$Platform == "Pypi"' projects.csv | wc -l
 172412
```

 - `dependencies.csv`: 
```bash
$ wc -l /Volumes/MEMORIA/libraries/dependencies.csv
 105811885
```
records. However, those that pertain to Pypi only number
```bash
$ mlr --icsv --opprint filter '$Platform == "Pypi"' dependencies.csv | wc -l
 489010
```
, a 3-orders-of-magnitude reduction in data!

 - `versions.csv`:
There are
```bash
$ mlr --icsv --opprint filter '$Platform == "Pypi"' then uniq -n -g "ID" versions.csv
 1242096
```
versions of some project on Pypi, and

```bash
$ mlr --icsv --opprint filter '$Platform == "Pypi"' then uniq -n -g "Project ID" versions.csv
 162874
```
project IDs corresponding to those versions on Pypi, which works out to
7.63 versions per project ID on average.
