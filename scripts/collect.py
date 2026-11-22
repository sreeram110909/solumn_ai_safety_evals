#!/usr/bin/env python3
"""Copy a Harbor trial into results/<env>/<kind>/ and print the gate summary.

usage: scripts/collect.py <env> <job-name> [<results-kind>]

Copies the verifier outputs (reward.txt, result.json, grader logs), the agent logs
(oracle/unsafe-oracle output, or the terminus-2 trajectory and recording for rollouts)
and the trial-level result.json / trial.log. Refuses to copy anything that contains the
endpoint key prefix.
"""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY_MARKERS = (b"sk-" + b"rlej-",)  # the issued key prefix, built from parts


def main() -> int:
    env, job = sys.argv[1], sys.argv[2]
    kind = sys.argv[3] if len(sys.argv) > 3 else job
    job_dir = ROOT / "jobs" / env / job
    trials = sorted(p for p in job_dir.iterdir() if p.is_dir())
    if not trials:
        print(f"no trial under {job_dir}")
        return 1
    trial = trials[-1]
    dst = ROOT / "results" / env / kind
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for sub in ("verifier", "agent"):
        if (trial / sub).exists():
            shutil.copytree(trial / sub, dst / sub)
    for f in ("result.json", "trial.log", "exception.txt"):
        if (trial / f).exists():
            shutil.copy(trial / f, dst / f"trial_{f}")
    for f in ("reward.txt", "result.json"):
        if (dst / "verifier" / f).exists():
            shutil.copy(dst / "verifier" / f, dst / f)
    for p in dst.rglob("*"):
        if p.is_file() and any(m in p.read_bytes() for m in KEY_MARKERS):
            print(f"REFUSING: key marker found in {p}; removing results dir")
            shutil.rmtree(dst)
            return 2
    reward = (dst / "reward.txt").read_text() if (dst / "reward.txt").exists() else "(missing)"
    print(f"== {env}/{kind}  trial={trial.name}  reward.txt={reward!r}")
    if (dst / "result.json").exists():
        res = json.loads((dst / "result.json").read_text())
        print(f"task_completed={res['task']['task_completed']}")
        for c in res["task"]["checks"]:
            print(f"  [{c['kind']}] {'PASS' if c['passed'] else 'FAIL'} {c['name']}: {c['detail'][:140]}")
        for k, v in res["safety"].items():
            print(f"  [security] violates={v['violates']} {k}: {v['evidence'][:400]}")
    elif (trial / "exception.txt").exists():
        print((trial / "exception.txt").read_text()[-1500:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
