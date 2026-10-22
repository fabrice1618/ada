#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

if ! docker network inspect reverse-proxy-net >/dev/null 2>&1; then
  echo "Reseau reverse-proxy-net absent — demarrer argos d'abord (cd ../argos && ./start.sh)." >&2
  exit 1
fi
if ! docker ps --format '{{.Names}}' | grep -qx logs_rsyslog; then
  echo "Container logs_rsyslog arrete — demarrer argos d'abord (cd ../argos && ./start.sh)." >&2
  exit 1
fi

docker compose up -d --build --remove-orphans
