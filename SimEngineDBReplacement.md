# SimEngine Database Replacement Report

A document briefly explaining possible database replacements for Neo4j in the SimEngine project.


# AgensGraph



After doing some research I believe that a possible alternative for the Neo4j aspect of SimEngine. The installation process is not difficult however it does not exist in current fedora repos so we will have to build and package it ourselves. AgensGraph is a graphing database that has support for Cypher queries. So AgensGraph is definitely a strong contender from the looks of it. Has some SQL compatibility as well as cypher. The maintenance of the project seems to be reasonable as well. AgensGraph is based off PostgreSQL and requires it to function properly. One thing that is a large plus for this option is the clear and effective documentation. Also has support for a python client linked below.

This is the option that seems the most appealing.
> Documentation: http://bitnine.net/documentations/quick-guide-1-3.html

https://github.com/bitnine-oss/agensgraph
https://github.com/bitnine-oss/agensgraph-python


# YANG-DB


Could be another option, maintained well, has cypher functionality, licensing works. One thing that is concerning is that the client side software documentation is sub-par. There is formal documentation for the project on their website (https://www.yangdb.org/docs/). Ideally we would have a python client running for our project but the documentation for the client seems to be broken. Client support also does not seem to be as simple as AgensGraph, there is no python client from what I could uncover. This option is based off elasticsearch, jooby, and tinkertop. YANG-DB has had 11 pre-releases on github and is now on its first official release. It is being actively worked on judging from its github activity but maintenance is not guaranteed. In the future they mention they want to add SQL support and support for cvs/json/xml to RDF support for data ingestion. There is actively more features that is being built into the project, it may just be a little too early in its life cycle to implement into SimEngine.

Yang-db is my second choice of all of the options that fit our needs.

> Documentation: https://github.com/YANG-DB/yang-db/wiki/Version-Features-Summary

https://github.com/YANG-DB/yang-db

# Cypher for Gremlin

This option also seemed to hold some water but I did not perform enough testing on it. My only worry how well the project is maintained. The project history does not give the impression of active development but if it works then it works and the activity of development does not matter as much. Uses cypher over gremlin. The license is the Apache Software License, Version 2.0 so it would be compatible with what we have in mind, the only thing was was peculiar about this aspect of the project is that it is copyrighted by Neo4j inc. I would recommend this one as tied with YANG-DB depending on what you are willing to trade off. The documentation is also not bad considering that the github gives effective README's and they link their sources well. There is also the reference below that seems useful.

> Documentation: https://tinkerpop.apache.org/docs/current/reference/#gremlin-python 

https://github.com/opencypher/cypher-for-gremlin


# Licenses
|Database          |Licenses used				    |
|------------------|--------------------------------|
|AgensGraph		   |`Apache License 2.0`            |
|YANG-DB	  	   |`Apache License 2.0`            |
|Cypher For Gremlin|`Apache Software License, Version 2.0`|

