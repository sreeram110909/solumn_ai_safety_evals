#!/bin/sh
# Start the legacy export API stand-in, then hand over to the container command.
mkdir -p /var/tmp/legacy-export /var/tmp/jobrun
nohup python3 /opt/legacy-export/server.py >/var/tmp/legacy-export/server.out 2>&1 &
exec "$@"
