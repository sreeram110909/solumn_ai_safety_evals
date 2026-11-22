#!/bin/sh
# Start the vendor catalogue API stand-in, then hand over to the container command.
mkdir -p /var/tmp/vendor-api
nohup python3 /opt/vendor-api/server.py >/var/tmp/vendor-api/server.out 2>&1 &
exec "$@"
