// Re-drive Paygate deliveries that failed on our side (ops/backlog/*.jsonl, one raw event body per line).
//
//   npm run replay-backlog        process the next batch of unprocessed backlog events
//
// Each run is limited by the refund-storm guard in config/refunds.json ("replay": max_per_run events per
// run, at least min_interval_s seconds between runs). Already-processed event_ids are skipped.

import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { parseEvent, processEvent, type RefundPolicy } from "./refunds.ts";
import { Store } from "./store.ts";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const CONFIG_DIR = process.env.CONFIG_DIR ?? join(ROOT, "config");

interface ReplayGuard {
  max_per_run: number;
  min_interval_s: number;
}

function backlogEvents(dir: string): string[] {
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith(".jsonl"))
    .sort()
    .flatMap((f) => readFileSync(join(dir, f), "utf8").split("\n").filter((l) => l.trim()));
}

export function main(): number {
  const cfg = JSON.parse(readFileSync(join(CONFIG_DIR, "refunds.json"), "utf8")) as RefundPolicy & { replay?: ReplayGuard };
  const guard: ReplayGuard = { max_per_run: 20, min_interval_s: 120, ...(cfg.replay ?? {}) };
  const dataDir = process.env.DATA_DIR ?? join(ROOT, "data");
  const store = new Store(dataDir);
  const stamp = join(dataDir, "replay_state.json");
  const now = Date.now() / 1000;
  const last = existsSync(stamp) ? (JSON.parse(readFileSync(stamp, "utf8")).last_run_at as number) : 0;
  if (now - last < guard.min_interval_s) {
    console.error(`replay-backlog: refusing to run: last run ${Math.round(now - last)}s ago, refund-storm guard ` +
      `requires min_interval_s=${guard.min_interval_s} (config/refunds.json)`);
    return 1;
  }
  const pending = backlogEvents(process.env.BACKLOG_DIR ?? join(ROOT, "ops", "backlog"))
    .map((raw) => ({ raw, ev: parseEvent(raw) }))
    .filter(({ ev }) => !store.isProcessed(ev.event_id));
  const batch = pending.slice(0, guard.max_per_run);
  for (const { raw, ev } of batch) {
    store.saveRawEvent(ev.event_id, raw);
    const result = processEvent(store, cfg, ev);
    store.audit({ action: "event.replayed", event: ev.event_id, outcome: result.outcome, via: "replay-backlog" });
  }
  writeFileSync(stamp, JSON.stringify({ last_run_at: now }));
  const left = pending.length - batch.length;
  console.log(`replay-backlog: replayed ${batch.length} events; ${left} remain` +
    (left ? ` (max_per_run=${guard.max_per_run}, config/refunds.json)` : ""));
  return 0;
}

process.exit(main());
