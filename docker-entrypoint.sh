#!/bin/sh

# Start redis
redis-server --daemonize yes

# Reset neo4j password
rm -f /var/lib/neo4j/data/dbms/auth
neo4j-admin set-initial-password neo4j-simengine

# Start neo4j
neo4j start
sleep 10
neo4j status

# Create account for simegine
cypher-shell -u neo4j -p neo4j-simengine \
      "CALL dbms.security.createUser('simengine', 'simengine', false);"

# Keep container running until neo4j dies
while \
  kill \
    -0 \
    $( \
      neo4j status \
      | sed \
        --regexp-extended \
        --quiet \
        's/^.*pid[[:space:]]+([0-9]+).*$/\1/p' \
    ) \
    >/dev/null \
    2>&1

  do
    sleep 5;
  done
