#!/bin/sh
set -e

wait_for_tcp() {
  host="$1"
  port="$2"
  name="$3"
  echo "Waiting for ${name} (${host}:${port})..."
  until python -c "
import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect(('${host}', ${port}))
    s.close()
    sys.exit(0)
except OSError:
    sys.exit(1)
" 2>/dev/null; do
    sleep 2
  done
  echo "${name} is ready."
}

wait_for_tcp mysql 3306 "MySQL"
wait_for_tcp redis 6379 "Redis"

if [ "${VECTOR_STORE_TYPE:-milvus}" = "milvus" ]; then
  wait_for_tcp milvus 19530 "Milvus"
fi

wait_for_tcp neo4j 7687 "Neo4j"

exec uvicorn main:app --host 0.0.0.0 --port 8000
