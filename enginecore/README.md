## Installing Dependencies

### Prerequisites

`redis` & `neo4j` are installed

### Simengine 

`python3 -m pip install -r requirements.txt`

### SNMPSim 
(python2 dependencies)

`pip install redis`

`pip install snmpsim`

## Running a Daemon

Neo4J & Redis server must be up & running

`neo4j start`

`redis-server`

Redis keyspace events are disabled by default, you can enable them by changing a config entry:

`redis-cli config set notify-keyspace-events E$` 

Starting a daemon

`python3 app.py`

## Linting

This lintrc file is based on Google Style Guide. See this docstring [example](http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) for documentation format reference.