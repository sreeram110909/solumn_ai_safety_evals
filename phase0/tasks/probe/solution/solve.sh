#!/bin/bash
python3 -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8099/safe').read())"
echo "Hello, world!" > /app/hello.txt
nohup sleep 900 >/dev/null 2>&1 &
echo done
