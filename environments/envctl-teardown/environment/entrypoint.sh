#!/bin/sh
# Start the Nimbus control-plane stand-in, then hand over to the container command.
mkdir -p /var/tmp/cloud-api
nohup node /opt/cloud-api/server.mjs --port 8900 --state-dir /var/tmp/cloud-api --seed /opt/cloud-api/seed.json \
  >/var/tmp/cloud-api/server.out 2>&1 &
exec "$@"
