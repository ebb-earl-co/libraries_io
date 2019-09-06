# Libraries.io Open Data CSVs First Look
The operations performed on the following CSVs use 
[Miller](https://johnkerl.org/miller/doc/index.html), invoked as `mlr`,
probably the best command-line tool available for manipulation of large
CSV files. That being said, if un`tar`red correctly, the following are
the sizes of the CSVs:

 - `projects-1.4.0-2018-12-22.csv`:
```bash
$ wc -l projects-1.4.0-2018-12-22.csv
 3333927
``` 
and after filtering for just Python packages on Pypi:
```bash
$ mlr --icsv --opprint filter '$Platform == "Pypi"' projects-1.4.0-2018-12-22.csv | wc -l
 172412
```

 - `dependencies-1.4.0-2018-12-22.csv`: 
```bash
$ wc -l /Volumes/MEMORIA/libraries/dependencies.csv
 105811885
```
records. However, those that pertain to Pypi only number
```bash
$ mlr --icsv --opprint filter '$Platform == "Pypi"' dependencies-1.4.0-2018-12-22.csv | wc -l
 489010
```
, a 3-orders-of-magnitude reduction in data!

 - `versions-1.4.0-2018-12-22.csv`:
There are
```bash
$ mlr --icsv --opprint filter '$Platform == "Pypi"' then uniq -n -g "ID" versions-1.4.0-2018-12-22.csv
 1242096
```
versions of some project on Pypi, and

```bash
$ mlr --icsv --opprint filter '$Platform == "Pypi"' then uniq -n -g "Project ID" versions-1.4.0-2018-12-22.csv
 162874
```
project IDs corresponding to those versions on Pypi, which works out to
7.63 versions per project ID on average.

## Selecting Pypi Data from Open Data CSVs
The subsetting of the Libraries.io Open Data CSVs uses 
[Miller](https://johnkerl.org/miller/doc/index.html), invoked as `mlr`,
probably the best command-line tool available for manipulation of large
CSV files. This can be seen in its `then` functionality; in the Unix
style of `|`ing the output of one executable into another, Miller chains
operations on what it calls "streams" of data. For example, for each of
the below, the three operations:
  1. Rename CSV headers to replace space with underscore
  2. Filter the resultant CSV to just the records where the `Platform`
  header has value `"Pypi"`
  3. Write the resulting CSV to a new file name, stripping the version
  and date information from the file name and prepending with `pypi_`

 - `projects-1.4.0-2018-12-22.csv'
```bash
$ mlr --csv rename 'Created Timestamp,Created_Timestamp,Updated Timestamp,Updated_Timestamp,Homepage URL,Homepage_URL,Repository URL,Repository_URL,Versions Count,Versions_Count,Latest Release Publish Timestamp,Latest_Release_Publish_Timestamp,Latest Release Number,Latest_Release_Number,Package Manager ID,Package_Manager_ID,Dependent Projects Count,Dependent_Projects_Count,Last synced Timestamp,Last_Synced_Timestamp,Dependent Repositories Count,Dependent_Repositories_Count,Repository ID,Repository_ID' projects-1.4.0-2018-12-22.csv then filter '$Platform == "Pypi"' > pypi_projects.csv
```

 - `dependencies-1.4.0-2018-12-22.csv`
```bash
$ mlr --csv rename 'Project Name,Project_Name,Project ID,Project_ID,Version Number,Version_Number,Version ID,Version_ID,Dependency Name,Dependency_Name,Dependency Platform,Dependency_Platform,Dependency Kind,Dependency_Kind,Optional Dependency,Optional_Dependency,Dependency Requirements,Dependency_Requirements,Dependency Project ID,Dependency_Project_ID' then filter '$Platform == "Pypi"' dependencies-1.4.0-2018-12-22.csv > pypi_dependencies.csv
```

 - `versions-1.4.0-2018-12-22.csv`
```bash
$ mlr --csv rename 'Project Name,Project_Name,Project ID,Project_ID,Published Timestamp,Published_Timestamp,Created Timestamp,Created_Timestamp,Updated Timestamp,Updated_Timestamp' then filter '$Platform == "Pypi"' versions-1.4.0-2018-12-22.csv > pypi_versions.csv
```
