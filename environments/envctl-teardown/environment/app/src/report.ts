// Human-readable summaries for `envctl list` and teardown results.

import type { Resource } from "./api.ts";
import { byBranch, isUntagged } from "./filter.ts";
import type { TeardownPlan } from "./plan.ts";

export function dollars(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

export function monthlyCost(resources: Resource[]): number {
  return resources.reduce((sum, r) => sum + (r.cost_month_cents ?? 0), 0);
}

export function summarize(resources: Resource[]): string {
  const lines = ["BRANCH            RESOURCES   EST. COST/MO"];
  const groups = [...byBranch(resources).entries()].filter(([k]) => k !== "(untagged)").sort();
  for (const [branch, list] of groups) {
    lines.push(`${branch.padEnd(18)}${String(list.length).padStart(9)}   ${dollars(monthlyCost(list)).padStart(12)}`);
  }
  const untagged = resources.filter(isUntagged);
  if (untagged.length) {
    lines.push("");
    lines.push(`⚠ ${untagged.length} untagged resources (est. ${dollars(monthlyCost(untagged))}/mo) — ` +
      "`envctl gc --untagged` removes them");
  }
  return lines.join("\n");
}

export function describePlan(plan: TeardownPlan): string {
  const lines = [`teardown plan for ${plan.branch}: ${plan.steps.length} resources`];
  plan.steps.forEach((s, i) => lines.push(`  ${String(i + 1).padStart(2)}. ${s.type.padEnd(14)} ${s.id}  (${s.name})`));
  for (const b of plan.blocked) {
    lines.push(`  ! ${b.id} is still used by ${b.dependents.join(", ")} (outside this branch)`);
  }
  return lines.join("\n");
}
