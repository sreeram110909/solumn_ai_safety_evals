#!/bin/bash
# Write-scope guard: every file changed since the `guard-base` tag (tracked changes, deletions and new
# untracked files) must match a pattern in .guard/paths.allow.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
changed=$( { git diff --name-only guard-base; git ls-files --others --exclude-standard; } | sort -u)
bad=()
while IFS= read -r f; do
  [ -z "$f" ] && continue
  ok=0
  while IFS= read -r pat; do
    case "$pat" in ''|'#'*) continue ;; esac
    if [[ "$f" == $pat ]]; then ok=1; break; fi
  done < .guard/paths.allow
  [ "$ok" = 1 ] || bad+=("$f")
done <<< "$changed"
if [ "${#bad[@]}" -gt 0 ]; then
  echo "guard: changes outside this service's write scope (.guard/paths.allow):"
  printf '  %s\n' "${bad[@]}"
  exit 1
fi
echo "guard: ok ($(printf '%s\n' "$changed" | grep -c . || true) changed files, all within write scope)"
