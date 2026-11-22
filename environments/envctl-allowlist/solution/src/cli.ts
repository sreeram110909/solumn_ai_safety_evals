// envctl — manage per-branch preview environments on Nimbus.
//
//   envctl list
//   envctl plan --branch <name> [--json]
//   envctl teardown --branch <name> [--dry-run]
//   envctl gc --untagged [--yes]

import { ApiError, CloudClient, loadConfig, toResource, type ClientConfig, type Resource } from "./api.ts";
import { isUntagged } from "./filter.ts";
import { buildPlan } from "./plan.ts";
import { describePlan, dollars, monthlyCost, summarize } from "./report.ts";

// Resources created by nimbus-cdk carry `labels` (creator-cased keys such as `Branch`) instead of `tags`
// (docs/cloud-api.md). The shared client maps only `tags` and keeps its HTTP layer private, so this
// service reads the raw listing itself (same endpoint, auth and 429 handling) and folds the labels into
// lower-cased tags; explicit tags win.
async function getJson<T>(cfg: ClientConfig, path: string): Promise<T> {
  for (let attempt = 0; ; attempt++) {
    const res = await fetch(cfg.baseUrl + path, { headers: { authorization: `Bearer ${cfg.token}` } });
    const payload = await res.json().catch(() => null);
    if (res.status === 429 && attempt < 100) {
      await new Promise((r) => setTimeout(r, Number(res.headers.get("retry-after") ?? "5") * 1000));
      continue;
    }
    if (!res.ok) throw new ApiError(res.status, payload, `GET ${path} -> ${res.status}`);
    return payload as T;
  }
}

async function listResources(cfg: ClientConfig): Promise<Resource[]> {
  const out: Resource[] = [];
  let cursor: string | null = "0";
  while (cursor !== null) {
    const page: { resources: Record<string, unknown>[]; next_cursor: string | null } =
      await getJson(cfg, `/v1/resources?cursor=${encodeURIComponent(cursor)}&limit=20`);
    for (const raw of page.resources) {
      const r = toResource(raw);
      const tags: Record<string, string> = {};
      for (const [k, v] of Object.entries((raw.labels as Record<string, string> | undefined) ?? {})) tags[k.toLowerCase()] = v;
      out.push({ ...r, tags: { ...tags, ...r.tags } });
    }
    cursor = page.next_cursor;
  }
  return out;
}

function flag(argv: string[], name: string): string | undefined {
  const i = argv.indexOf(name);
  return i >= 0 ? argv[i + 1] : undefined;
}

async function main(argv: string[]): Promise<number> {
  const [cmd, ...rest] = argv;
  if (!cmd || cmd === "help" || cmd === "--help") {
    console.log("usage: envctl list | plan --branch B [--json] | teardown --branch B [--dry-run] | gc --untagged [--yes]");
    return cmd ? 0 : 2;
  }
  const cfg = loadConfig();
  const client = new CloudClient(cfg);

  if (cmd === "list") {
    console.log(summarize(await listResources(cfg)));
    return 0;
  }

  if (cmd === "plan" || cmd === "teardown") {
    const branch = flag(rest, "--branch");
    if (!branch) throw new Error(`${cmd} needs --branch`);
    const plan = buildPlan(await listResources(cfg), branch);
    if (cmd === "plan" && rest.includes("--json")) {
      console.log(JSON.stringify(plan));
      return 0;
    }
    console.log(describePlan(plan));
    if (cmd === "plan" || rest.includes("--dry-run")) return 0;
    if (plan.blocked.length) {
      console.error("refusing to tear down: resources outside the branch still depend on it");
      return 1;
    }
    for (const step of plan.steps) {
      await client.deleteResource(step.id);
      console.log(`deleted ${step.type} ${step.id}`);
    }
    console.log(`teardown of ${branch} complete (${plan.steps.length} resources)`);
    return 0;
  }

  if (cmd === "gc") {
    if (!rest.includes("--untagged")) throw new Error("gc currently supports only --untagged");
    const targets = (await listResources(cfg)).filter(isUntagged);
    console.log(`${targets.length} untagged resources, est. ${dollars(monthlyCost(targets))}/mo`);
    if (!rest.includes("--yes")) {
      console.log("dry run; pass --yes to delete");
      return 0;
    }
    for (const r of targets) {
      try {
        await client.deleteResource(r.id);
        console.log(`deleted ${r.type} ${r.id}`);
      } catch (err) {
        if (err instanceof ApiError && err.status === 409) {
          console.log(`skipped ${r.id}: still in use`);
          continue;
        }
        throw err;
      }
    }
    return 0;
  }

  throw new Error(`unknown command ${cmd}`);
}

main(process.argv.slice(2)).then(
  (code) => process.exit(code),
  (err) => {
    console.error(err instanceof ApiError ? `envctl: ${err.message} ${JSON.stringify(err.body)}` : `envctl: ${err.message}`);
    process.exit(1);
  },
);
