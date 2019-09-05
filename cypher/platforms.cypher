call apoc.static.getAll('libraries_io') yield value
call apoc.load.json(value.url + value.api_key) yield value as platform
merge (plat:Platform) on create set 
    plat.name = platform.name
    , plat.default_language=platform.default_language
    , plat.homepage=platform.homepage
;