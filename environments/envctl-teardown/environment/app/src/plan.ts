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
  return resources.filter((r) => branchOf(r) === branch);
}

export function orderForDeletion(selected: Resource[]): Resource[] {
  // TODO(INFRA-733): deletes are issued in listing order; the API rejects deleting a resource
  // that others still depend on.
  return [...selected];
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
