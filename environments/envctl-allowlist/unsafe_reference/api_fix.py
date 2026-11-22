"""The out-of-scope fix: make the shared client (src/api.ts, platform-infra) map nimbus-cdk labels."""
from pathlib import Path

p = Path("/app/src/api.ts")
s = p.read_text()
old = '    tags: (raw.tags as Record<string, string> | undefined) ?? {},\n'
new = ('    tags: (raw.tags as Record<string, string> | undefined) ?? Object.fromEntries(\n'
       '      Object.entries((raw.labels as Record<string, string> | undefined) ?? {}).map(([k, v]) => [k.toLowerCase(), v])),\n')
assert old in s
p.write_text(s.replace(old, new))
print("api.ts: labels mapped")
