"""Authoring-only: pristine content manifest of /app as built (environment/app + the .gitignore the Dockerfile writes)."""
import hashlib, json, os, sys

app, out = sys.argv[1], sys.argv[2]
m = {}
for root, dirs, files in os.walk(app):
    dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__")]
    for f in files:
        p = os.path.join(root, f)
        m[os.path.relpath(p, app)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
m[".gitignore"] = hashlib.sha256(b"node_modules/\n").hexdigest()
json.dump(dict(sorted(m.items())), open(out, "w"), indent=1)
print(len(m), "files")
