// Cypher DB setup script

CREATE CONSTRAINT ON (n:Asset) ASSERT (n.key) IS UNIQUE;