// envctl — manage per-branch preview environments on Nimbus.
//
//   envctl list
//   envctl plan --branch <name> [--json]
//   envctl teardown --branch <name> [--dry-run]
//   envctl gc --untagged [--yes]

import { ApiError, CloudClient, loadConfig } from "./api.ts";
import { isUntagged } from "./filter.ts";
import { buildPlan } from "./plan.ts";
import { describePlan, dollars, monthlyCost, summarize } from "./report.ts";

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
  const client = new CloudClient(loadConfig());

  if (cmd === "list") {
    console.log(summarize(await client.listResources()));
    return 0;
  }

  if (cmd === "plan" || cmd === "teardown") {
    const branch = flag(rest, "--branch");
    if (!branch) throw new Error(`${cmd} needs --branch`);
    const plan = buildPlan(await client.listResources(), branch);
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
    const targets = (await client.listResources()).filter(isUntagged);
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
