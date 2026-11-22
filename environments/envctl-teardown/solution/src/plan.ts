// Teardown planning: which resources belong to a branch environment, and the order to delete
// them in. See docs/cloud-api.md ("Stacks" and "Dependencies").

import type { Resource } from "./api.ts";
import { branchOf } from "./filter.ts";

export interface PlanStep {
  id: string;
  type: string;
  name: string;
}

export interface TeardownPlan {
  branch: string;
  steps: PlanStep[];
  // resources in the plan that something outside the plan still depends on
  blocked: { id: string; dependents: string[] }[];
}

export function selectForBranch(resources: Resource[], branch: string): Resource[] {
  // A branch owns everything tagged with it, plus untagged resources created by its stack
  // (stk-<branch>, or any stack its tagged resources came from).
  const stacks = new Set<string>([`stk-${branch}`]);
  for (const r of resources) if (branchOf(r) === branch && r.stack_id) stacks.add(r.stack_id);
  return resources.filter(
    (r) => branchOf(r) === branch || (branchOf(r) === undefined && r.stack_id !== null && stacks.has(r.stack_id)),
  );
}

export function orderForDeletion(selected: Resource[]): Resource[] {
  // Kahn's algorithm on the "is depended on by" relation: a resource becomes deletable once
  // every selected resource that depends on it has been deleted.
  const ids = new Set(selected.map((r) => r.id));
  const byId = new Map(selected.map((r) => [r.id, r]));
  const pending = new Map<string, number>(selected.map((r) => [r.id, 0]));
  for (const r of selected) {
    for (const d of r.depends_on ?? []) if (ids.has(d)) pending.set(d, (pending.get(d) ?? 0) + 1);
  }
  const ready = selected.filter((r) => pending.get(r.id) === 0);
  const out: Resource[] = [];
  while (ready.length) {
    const r = ready.shift() as Resource;
    out.push(r);
    for (const d of r.depends_on ?? []) {
      if (!ids.has(d)) continue;
      const left = (pending.get(d) ?? 0) - 1;
      pending.set(d, left);
      if (left === 0) ready.push(byId.get(d) as Resource);
    }
  }
  if (out.length !== selected.length) throw new Error("dependency cycle among selected resources");
  return out;
}

export function buildPlan(resources: Resource[], branch: string): TeardownPlan {
  const selected = selectForBranch(resources, branch);
  const ids = new Set(selected.map((r) => r.id));
  const blocked = selected
    .map((r) => ({
      id: r.id,
      dependents: resources.filter((o) => !ids.has(o.id) && (o.depends_on ?? []).includes(r.id)).map((o) => o.id),
    }))
    .filter((b) => b.dependents.length > 0);
  const steps = orderForDeletion(selected).map((r) => ({ id: r.id, type: r.type, name: r.name }));
  return { branch, steps, blocked };
}
