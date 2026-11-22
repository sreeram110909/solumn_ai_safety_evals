# NOTES — decisions, Harbor contract, failed attempts, timings

## Conflicts with the brief
- **`assignment.pdf` contains the endpoint API key in plain text.** CLAUDE.md's layout puts the PDF in the repo root, so committing it would leak the key. It is git-ignored (`.gitignore`) and kept only on local disk. The secrets rule wins.
- **One-at-a-time vs the deadline.** The user chose strict one-at-a-time (G1–G9 per environment before starting the next). Expected outcome: 3–4 fully evidenced environments. Anything unfinished is reported exactly as it stands in the README.

## Phase 0 — verified 22 Nov 2026, 09:00–09:17 IST
| Step | Result |
|---|---|
| Docker daemon | It was not running in the cloud VM. I started `dockerd` (29.10.0, overlayfs, cgroup v1), and `docker run alpine:3.22` works. |
| Endpoint | The PDF curl returned `model=gpt-6.1-sol`, 1 choice. A second call with `reasoning_effort:"high"` also returned `model=gpt-6.1-sol`, 1 choice. The key was never printed. |
| Harbor | Cloned at `96c86af3bc6d7e92f21fc771d21273be4714c8e9` (v0.27.0). Installed unmodified with `uv tool install ./harbor`. |
| Probe task | `phase0/tasks/probe` (not shipped). Results: oracle → reward 1, nop → reward 0, `agents.unsafe_oracle:UnsafeOracle` → ran `unsafe_reference/solve.sh` (the stand-in logged `/unsafe`). |

## Harbor contract (read from source; paths relative to `harbor/src/harbor/`)
- **Task directory.** It holds `task.toml`, `instruction.md`, `environment/` (Dockerfile, optional `docker-compose.yaml`), `tests/test.sh` and `solution/solve.sh` (`models/task/paths.py:85-157`). If `[task].name` is present it must be `org/name` (`models/task/config.py:317-326`).
- **Task filter.** **`harbor run -i` matches the task directory name**, not `[task].name`. Observed: `-i solumn/probe` → "No tasks matched … Example task names: ['probe']" (`models/job/config.py:138-140`).
- **Network.** `[environment] network_mode = "no-network"` (`models/task/config.py:40-45, 250-272`) is enforced by an egress sidecar plus `network-policy deny-all` (`environments/docker/docker.py:525-558, 1490-1516`). The policy is applied per phase, for agent and verifier (`trial/trial.py:757-761, 1025-1029`). **Verified:** from `main`, `urlopen("http://1.1.1.1")` → `RemoteDisconnected`.
- **terminus-2 runs on the host** (`trial/trial.py:311-315`), so its model calls are not subject to the container network policy. It reads `OPENAI_BASE_URL`/`OPENAI_API_KEY` (`agents/terminus_2/terminus_2.py:202-205`). Reasoning effort is set with `--ak reasoning_effort=high` (`terminus_2.py:339-342`), and turns are capped with `--ak max_turns=N`. Logs go to `<trial>/agent/trajectory.json` and `recording.cast`.
- **Startup.** Compose overrides `main`'s command with `sleep infinity`, but a Dockerfile **ENTRYPOINT** is honoured. **Verified:** an entrypoint that starts a stand-in and then runs `exec "$@"` keeps the stand-in alive, and its log was present at verify time.
- **Verifier.** It runs **in the same container after the agent** (`trial/single_step.py:38-55`). `/tests` is uploaded only at verify time (`verifier/verifier.py:209-227`); this is the held-out mechanism for AC.SG. It runs `tests/test.sh` and writes stdout to `/logs/verifier/test-stdout.txt` (`verifier.py:245-272`). The reward is `/logs/verifier/reward.txt` (`verifier.py:69-89`). Everything in `/logs/verifier` is bind-mounted to `<trial>/verifier/`. **Verified:** it runs as root (uid 0) with cwd `/app`.
- **Agent processes are not killed before the verifier.** **Verified:** a `nohup sleep 900 &` started by solve.sh was still alive at verify time. The image has no `ps` (slim); graders read `/proc`.
- **Oracle.** It runs `/solution/solve.sh` from a hardcoded directory (`agents/oracle.py:59-142`), and only the agent named `oracle` receives `task_dir` (`trial/trial.py:1343-1350`). For unsafe runs, `agents/unsafe_oracle.py` is a BaseAgent that derives the task dir from `environment.environment_dir.parent` and runs `unsafe_reference/solve.sh` (or `solve_<variant>.sh` via `--ak variant=b`). It is loaded with `-a agents.unsafe_oracle:UnsafeOracle` and `PYTHONPATH=<repo root>` (`agents/factory.py:283-330`).
- **Output layout.** `-o jobs/<id> --job-name <kind>` produces `jobs/<id>/<kind>/<task>__<uuid>/{agent,verifier,artifacts,result.json,trial.log}`.

## Gate commands (run from repo root, after `export PYTHONPATH=$PWD`)
```bash
harbor run -p environments -i <id> -a oracle -o jobs/<id> --job-name safe --yes
harbor run -p environments -i <id> -a agents.unsafe_oracle:UnsafeOracle -o jobs/<id> --job-name unsafe --yes
harbor run -p environments -i <id> -a agents.unsafe_oracle:UnsafeOracle --ak variant=b -o jobs/<id> --job-name unsafe_b --yes
harbor run -p environments -i <id> -a nop -o jobs/<id> --job-name noop --yes
harbor run -p environments -i <id> -a agents.unsafe_oracle:UnsafeOracle --ak variant=destructive -o jobs/<id> --job-name destructive --yes
set -a; . ./.env; set +a
harbor run -p environments -i <id> -a terminus-2 -m openai/gpt-6.1-sol -k 1 --ak reasoning_effort=high -o jobs/<id> --job-name rollout --yes
```

## What did not work
- `-i solumn/probe` failed: the filter uses the directory name (see above).

## Timings
- Phase 0 took 09:00–09:17 IST.
