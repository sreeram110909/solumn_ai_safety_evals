#!/bin/sh
mkdir -p /var/tmp/probe
nohup python3 /opt/standin.py >/var/tmp/probe/standin.out 2>&1 &
exec "$@"
