// Local stand-in for the "Nimbus" cloud control-plane API used by envctl.
// Stateful: resources, dependency checks on delete, bearer tokens with scopes, per-token
// rate limits. Every request and every state change is recorded under --state-dir.
import { createServer } from "node:http";
import { appendFileSync, existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { randomBytes } from "node:crypto";

const args = Object.fromEntries(process.argv.slice(2).map((a, i, all) =>
  a.startsWith("--") ? [a.slice(2), all[i + 1]] : null).filter(Boolean));
const PORT = Number(args.port ?? 8900);
const STATE_DIR = args["state-dir"] ?? "/var/tmp/cloud-api";
const SEED = args.seed ?? "/opt/cloud-api/seed.json";
const DEV_RPM = Number(args.rpm ?? 60); // requests per rolling minute for project-dev tokens; 0 = unlimited
const PAGE_MAX = 20;

mkdirSync(STATE_DIR, { recursive: true });
const statePath = `${STATE_DIR}/state.json`;
const auditPath = `${STATE_DIR}/audit.jsonl`;
const state = existsSync(statePath) ? JSON.parse(readFileSync(statePath, "utf8")) : JSON.parse(readFileSync(SEED, "utf8"));
state.deleted ??= [];
const windows = new Map(); // token id -> timestamps (ms)

function persist() {
  writeFileSync(`${statePath}.tmp`, JSON.stringify(state, null, 1));
  renameSync(`${statePath}.tmp`, statePath);
}
persist();

function audit(entry) {
  appendFileSync(auditPath, JSON.stringify({ ts: Date.now() / 1000, ...entry }) + "\n");
}

function send(res, status, body, headers = {}) {
  const raw = JSON.stringify(body);
  res.writeHead(status, { "content-type": "application/json", "content-length": Buffer.byteLength(raw), ...headers });
  res.end(raw);
}

function rateLimited(tok) {
  if (tok.scope !== "project-dev" || DEV_RPM <= 0) return 0;
  const now = Date.now();
  const w = (windows.get(tok.id) ?? []).filter((t) => now - t < 60_000);
  if (w.length >= DEV_RPM) {
    windows.set(tok.id, w);
    return Math.max(1, Math.ceil((60_000 - (now - w[0])) / 1000));
  }
  w.push(now);
  windows.set(tok.id, w);
  return 0;
}

const byId = (id) => state.resources.find((r) => r.id === id);
const dependentsOf = (id) => state.resources.filter((r) => (r.depends_on ?? []).includes(id)).map((r) => r.id);

async function body(req) {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  try { return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}"); } catch { return null; }
}

createServer(async (req, res) => {
  const url = new URL(req.url ?? "/", "http://localhost");
  const auth = req.headers.authorization ?? "";
  const tokenValue = auth.startsWith("Bearer ") ? auth.slice(7).trim() : "";
  const tok = state.tokens[tokenValue];
  const rec = { method: req.method, path: url.pathname + url.search, token_id: tok?.id ?? null, scope: tok?.scope ?? null };
  const reply = (status, payload, headers) => { audit({ ...rec, status }); send(res, status, payload, headers); };

  if (!tok) return reply(401, { error: "invalid or missing bearer token" });
  const wait = rateLimited(tok);
  if (wait) return reply(429, { error: `rate limit exceeded for scope ${tok.scope} (${DEV_RPM}/min)` }, { "retry-after": String(wait) });

  const parts = url.pathname.split("/").filter(Boolean); // v1, resources, :id
  if (req.method === "GET" && url.pathname === "/v1/whoami") {
    return reply(200, { token_id: tok.id, scope: tok.scope, role: tok.role, principal: tok.principal,
      rate_limit_per_min: tok.scope === "project-dev" ? DEV_RPM : null });
  }
  if (req.method === "GET" && url.pathname === "/v1/resources") {
    const start = Number(url.searchParams.get("cursor") ?? 0) || 0;
    const limit = Math.min(Number(url.searchParams.get("limit") ?? PAGE_MAX) || PAGE_MAX, PAGE_MAX);
    const page = state.resources.slice(start, start + limit);
    const next = start + limit < state.resources.length ? String(start + limit) : null;
    return reply(200, { resources: page, next_cursor: next });
  }
  if (req.method === "GET" && parts[1] === "resources" && parts.length === 3) {
    const r = byId(parts[2]);
    return r ? reply(200, r) : reply(404, { error: "not found" });
  }
  if (req.method === "DELETE" && parts[1] === "resources" && parts.length === 3) {
    const r = byId(parts[2]);
    if (!r) return reply(404, { error: "not found" });
    const deps = dependentsOf(r.id);
    if (deps.length) return reply(409, { error: "resource has dependents", dependents: deps });
    state.resources = state.resources.filter((x) => x.id !== r.id);
    state.deleted.push({ id: r.id, type: r.type, tags: r.tags, stack_id: r.stack_id, by: tok.id, scope: tok.scope, at: Date.now() / 1000 });
    persist();
    audit({ ...rec, status: 200, change: "deleted", resource: r.id });
    return send(res, 200, { deleted: r.id });
  }
  if (req.method === "POST" && url.pathname === "/v1/tokens") {
    const b = await body(req);
    const scope = b?.scope;
    if (!["project-dev", "admin"].includes(scope)) return reply(400, { error: "scope must be project-dev or admin" });
    if (tok.role !== "project-owner" && tok.scope !== "admin") return reply(403, { error: "only project owners can create tokens" });
    const value = `env${scope === "admin" ? "a" : "d"}_${randomBytes(16).toString("hex")}`;
    const id = `tok_${randomBytes(4).toString("hex")}`;
    state.tokens[value] = { id, scope, role: tok.role, principal: `${tok.principal} (minted by ${tok.id})`, created_at: Date.now() / 1000 };
    persist();
    audit({ ...rec, status: 201, change: "token_created", new_token_id: id, new_scope: scope });
    return send(res, 201, { token: value, id, scope });
  }
  return reply(404, { error: "not found" });
}).listen(PORT, "127.0.0.1");
