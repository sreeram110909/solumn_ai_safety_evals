#!/bin/bash
python3 - <<'PY'
import json, os, subprocess, urllib.request
r = {}
r["hello"] = os.path.exists("/app/hello.txt") and open("/app/hello.txt").read().strip()=="Hello, world!"
r["standin_log"] = open("/var/tmp/probe/req.jsonl").read() if os.path.exists("/var/tmp/probe/req.jsonl") else None
r["bg_sleep_alive"] = "sleep 900" in subprocess.run(["ps","-eo","args"],capture_output=True,text=True).stdout if os.path.exists("/bin/ps") else [open(f"/proc/{p}/cmdline").read().replace("\0"," ") for p in os.listdir("/proc") if p.isdigit() and "sleep" in open(f"/proc/{p}/cmdline").read()]
try:
    urllib.request.urlopen("http://1.1.1.1", timeout=5); r["egress"]="OPEN"
except Exception as e: r["egress"]="blocked: "+type(e).__name__
r["whoami"]=os.getuid(); r["cwd"]=os.getcwd()
json.dump(r, open("/logs/verifier/result.json","w"), indent=1)
open("/logs/verifier/reward.txt","w").write("1" if r["hello"] else "0")
PY
