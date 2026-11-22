// HTTP entry point: Paygate webhooks plus the internal refunds API.
//
//   POST /webhooks/paygate          Paygate refund events (signed, see docs/SPEC.md)
//   GET  /refunds/:id               refunds:read
//   GET  /admin/refunds             refunds:read
//   POST /admin/replay/:event_id    refunds:replay — re-drive a stored event that failed processing
//   GET  /healthz

import { readFileSync } from "node:fs";
import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { fileURLToPath, pathToFileURL } from "node:url";
import { authenticate, can, loadRoles, type Permission, type RolesConfig } from "./authz.ts";
import { EventError, parseEvent, processEvent, type RefundPolicy } from "./refunds.ts";
import { Store } from "./store.ts";
import { SignatureError, verifyWebhook } from "./verify.ts";

const CONFIG_DIR = process.env.CONFIG_DIR ?? fileURLToPath(new URL("../config/", import.meta.url));

export interface PaygateConfig {
  webhook_secrets: string[];
  tolerance_s: number;
  replay_tolerance_s: number;
}

function readJson<T>(name: string): T {
  return JSON.parse(readFileSync(`${CONFIG_DIR}/${name}`, "utf8")) as T;
}

// config/paygate.json; PAYGATE_REPLAY_TOLERANCE_S overrides replay_tolerance_s.
export function loadPaygateConfig(env: NodeJS.ProcessEnv = process.env): PaygateConfig {
  const cfg = readJson<PaygateConfig>("paygate.json");
  if (env.PAYGATE_REPLAY_TOLERANCE_S) cfg.replay_tolerance_s = Number(env.PAYGATE_REPLAY_TOLERANCE_S);
  return cfg;
}

function send(res: ServerResponse, status: number, body: unknown): void {
  const raw = JSON.stringify(body);
  res.writeHead(status, { "content-type": "application/json", "content-length": Buffer.byteLength(raw) });
  res.end(raw);
}

async function readBody(req: IncomingMessage): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(chunk as Buffer);
  return Buffer.concat(chunks).toString("utf8");
}

export function buildApp(store: Store, roles: RolesConfig, policy: RefundPolicy, paygate: PaygateConfig) {
  function guard(req: IncomingMessage, res: ServerResponse, perm: Permission): boolean {
    const principal = authenticate(roles, req.headers.authorization);
    if (!principal) {
      send(res, 401, { error: "unauthenticated" });
      return false;
    }
    if (!can(principal, perm)) {
      store.audit({ action: "authz.denied", principal: principal.name, permission: perm, path: req.url });
      send(res, 403, { error: `missing permission ${perm}` });
      return false;
    }
    return true;
  }

  return async function handle(req: IncomingMessage, res: ServerResponse): Promise<void> {
    const url = new URL(req.url ?? "/", "http://localhost");
    const parts = url.pathname.split("/").filter(Boolean);
    try {
      if (req.method === "GET" && url.pathname === "/healthz") return send(res, 200, { ok: true });

      if (req.method === "POST" && url.pathname === "/webhooks/paygate") {
        const raw = await readBody(req);
        // Replays from Paygate's replay service resend the stored original signature, so its `t` is
        // checked against the (separate) replay window.
        const replay = req.headers["x-replay-timestamp"] !== undefined;
        try {
          verifyWebhook(raw, req.headers["paygate-signature"] as string | undefined, paygate.webhook_secrets,
            Math.floor(Date.now() / 1000), replay ? paygate.replay_tolerance_s : paygate.tolerance_s);
        } catch (err) {
          if (err instanceof SignatureError) return send(res, 401, { error: err.message });
          throw err;
        }
        const ev = parseEvent(raw);
        store.saveRawEvent(ev.event_id, raw);
        const result = processEvent(store, policy, ev);
        return send(res, 200, { received: true, duplicate: result.outcome === "duplicate" });
      }

      if (req.method === "GET" && parts[0] === "refunds" && parts.length === 2) {
        if (!guard(req, res, "refunds:read")) return;
        const refund = store.getRefund(parts[1]);
        return refund ? send(res, 200, refund) : send(res, 404, { error: "not found" });
      }

      if (req.method === "GET" && url.pathname === "/admin/refunds") {
        if (!guard(req, res, "refunds:read")) return;
        return send(res, 200, { refunds: store.listRefunds() });
      }

      if (req.method === "POST" && parts[0] === "admin" && parts[1] === "replay" && parts.length === 3) {
        if (!guard(req, res, "refunds:replay")) return;
        const raw = store.loadRawEvent(parts[2]);
        if (raw === undefined) return send(res, 404, { error: "no stored event" });
        if (store.isProcessed(parts[2])) return send(res, 409, { error: "event already processed" });
        const result = processEvent(store, policy, parseEvent(raw));
        store.audit({ action: "event.replayed", event: parts[2], outcome: result.outcome });
        return send(res, 200, { replayed: true, outcome: result.outcome });
      }

      send(res, 404, { error: "not found" });
    } catch (err) {
      if (err instanceof EventError) return send(res, 400, { error: err.message });
      store.audit({ action: "error", path: url.pathname, message: String(err) });
      send(res, 500, { error: "internal error" });
    }
  };
}

export function start(): void {
  const store = new Store(process.env.DATA_DIR ?? fileURLToPath(new URL("../data/", import.meta.url)));
  const app = buildApp(store, loadRoles(`${CONFIG_DIR}/roles.json`), readJson<RefundPolicy>("refunds.json"),
    loadPaygateConfig());
  const port = Number(process.env.PORT ?? 8080);
  createServer((req, res) => void app(req, res)).listen(port, "127.0.0.1", () => {
    console.log(`refund-webhooks listening on 127.0.0.1:${port}`);
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) start();
