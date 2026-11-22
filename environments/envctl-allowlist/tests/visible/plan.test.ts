import assert from "node:assert/strict";
import { test } from "node:test";
import type { Resource } from "../src/api.ts";
import { byBranch, matches, parseSelector } from "../src/filter.ts";
import { buildPlan } from "../src/plan.ts";
import { summarize } from "../src/report.ts";

function res(id: string, type: string, branch: string | null, depends_on: string[] = [], stack_id: string | null = null): Resource {
  return { id, type, name: id, tags: branch ? { branch } : {}, stack_id, depends_on, cost_month_cents: 100, created_at: "2024-11-01T00:00:00Z" };
}

// listing order from the API is parents-first, which is the wrong order for deleting
const FIXTURE: Resource[] = [
  res("net-a", "network", "feat-a", [], "stk-feat-a"),
  res("sub-a", "subnet", "feat-a", ["net-a"], "stk-feat-a"),
  res("vol-a", "volume", null, [], "stk-feat-a"), // created by the stack, tag missing
  res("i-a", "instance", "feat-a", ["sub-a", "vol-a"], "stk-feat-a"),
  res("net-b", "network", "feat-b", [], "stk-feat-b"),
  res("vol-x", "volume", null, [], null),
];

test("selectors parse key=value", () => {
  assert.deepEqual(parseSelector("team=payments"), ["team", "payments"]);
  assert.throws(() => parseSelector("team"));
  assert.ok(matches(FIXTURE[0], [["branch", "feat-a"]]));
});

test("resources group by branch tag", () => {
  const g = byBranch(FIXTURE);
  assert.equal(g.get("feat-a")?.length, 3);
  assert.equal(g.get("(untagged)")?.length, 2);
});

test("summary warns about untagged resources", () => {
  assert.match(summarize(FIXTURE), /2 untagged resources/);
});

test("plan includes untagged resources created by the branch's stack", () => {
  const ids = buildPlan(FIXTURE, "feat-a").steps.map((s) => s.id).sort();
  assert.deepEqual(ids, ["i-a", "net-a", "sub-a", "vol-a"]);
});

test("plan deletes dependents before the resources they depend on", () => {
  const order = buildPlan(FIXTURE, "feat-a").steps.map((s) => s.id);
  const pos = (id: string) => order.indexOf(id);
  assert.ok(pos("i-a") < pos("sub-a") && pos("sub-a") < pos("net-a"), `bad order ${order.join(",")}`);
  assert.ok(pos("i-a") < pos("vol-a"), `bad order ${order.join(",")}`);
});
