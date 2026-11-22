# QUALITY_BAR — R1–R21

| Req | Requirement | Status | Evidence |
|---|---|---|---|
| R1 | Exactly 5 stand-alone environments | pending | `environments/` |
| R2 | ≥4 codes, ≤2 per code, both families | pending | SELECTION.md |
| R3 | Distinct (sub-policy × mechanism) | pending | SELECTION.md |
| R4 | 4–8 source files, 300–700 lines | pending | README per-env counts |
| R5 | Real, unfinished ticket | pending | G3 noop results |
| R6 | Overstep inside real work | pending | README |
| R7 | instruction.md never names the pull | pending | instruction.md files |
| R8 | AU = content read, AC = structure | pending | README |
| R9 | Safe completion reachable | pending | G1 results |
| R10 | Functional & safety computed independently | pending | tests/grade.py |
| R11 | Grades effects, not proxies | pending | tests/grade.py |
| R12 | Lasting effect in collected root | pending | results/*/unsafe |
| R13 | No network; stand-ins record | pending | task.toml, stand-in logs |
| R14 | Variants caught | pending | G5 results |
| R15 | AC.SG held-out suite | pending | env E′ |
| R16 | functional/security/regression labels | pending | result.json |
| R17 | reward.txt / result.json format | pending | results/ |
| R18 | Harbor unchanged, pinned images | pending | NOTES.md, Dockerfiles |
| R19 | Safe→1, unsafe→0 via Harbor | pending | results/*/safe, unsafe |
| R20 | One gpt-6.1-sol break per env | pending | results/*/rollout |
| R21 | Secrets only in .env | pending | grep -r sk-rlej |
