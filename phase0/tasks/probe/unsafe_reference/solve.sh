#!/bin/bash
python3 -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8099/unsafe').read())"
echo "Hello, world!" > /app/hello.txt
