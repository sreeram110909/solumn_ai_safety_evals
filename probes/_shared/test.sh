#!/bin/bash
# Probe verifier entry point. FIRST preserve the final state (for the independent verifier), THEN grade.
mkdir -p /logs/verifier
python3 -I -S - > /logs/verifier/procs.json 2>/dev/null <<'PY'
import json, os
out = []
for pid in os.listdir("/proc"):
    if not pid.isdigit():
        continue
    try:
        cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace").strip()
        cwd = os.readlink(f"/proc/{pid}/cwd")
        st = open(f"/proc/{pid}/stat").read().split()
        out.append({"pid": int(pid), "ppid": int(st[3]), "cmd": cmd, "cwd": cwd, "start_ticks": int(st[21])})
    except Exception:
        pass
print(json.dumps(out, indent=1))
PY
tar czf /logs/verifier/final_state.tgz --exclude='*/__pycache__' --exclude='*/.pytest_cache' --exclude='*/node_modules' \
    --exclude='tmp/grader' --exclude='tmp/tmux-*' -C / app var/tmp tmp $( [ -d /home/agent ] && echo home/agent ) 2>/dev/null
python3 -I -S /tests/grade.py > /logs/verifier/grade.log 2>&1
rc=$?
cat /logs/verifier/grade.log
if [ ! -s /logs/verifier/reward.txt ]; then
  echo "grader crashed (rc=$rc); scoring 0" >&2
  printf 0 > /logs/verifier/reward.txt
fi
exit 0
