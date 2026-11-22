// Resource selectors shared by the CLI commands.

import type { Resource } from "./api.ts";

export function branchOf(r: Resource): string | undefined {
  return r.tags?.branch;
}

export function isUntagged(r: Resource): boolean {
  return branchOf(r) === undefined;
}

export function byBranch(resources: Resource[]): Map<string, Resource[]> {
  const groups = new Map<string, Resource[]>();
  for (const r of resources) {
    const key = branchOf(r) ?? "(untagged)";
    const list = groups.get(key) ?? [];
    list.push(r);
    groups.set(key, list);
  }
  return groups;
}

// "--tag team=payments" style selectors.
export function parseSelector(expr: string): [string, string] {
  const idx = expr.indexOf("=");
  if (idx <= 0) throw new Error(`bad selector ${JSON.stringify(expr)} (expected key=value)`);
  return [expr.slice(0, idx), expr.slice(idx + 1)];
}

export function matches(r: Resource, selectors: [string, string][]): boolean {
  return selectors.every(([k, v]) => r.tags?.[k] === v);
}
