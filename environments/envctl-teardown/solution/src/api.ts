// Thin client for the Nimbus control-plane API (docs/cloud-api.md).

import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

export interface Resource {
  id: string;
  type: string;
  name: string;
  tags: Record<string, string>;
  stack_id: string | null;
  depends_on: string[];
  cost_month_cents: number;
  created_at: string;
}

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown, message: string) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

export type Scope = "branch" | "project";

export interface ClientConfig {
  baseUrl: string;
  token: string;
  scope: Scope;
}

// envctl.yaml at the repository root: flat `key: value` lines (# comments allowed).
export function readSettings(path: string = fileURLToPath(new URL("../envctl.yaml", import.meta.url))): Record<string, string> {
  const out: Record<string, string> = {};
  if (!existsSync(path)) return out;
  for (const raw of readFileSync(path, "utf8").split("\n")) {
    const line = raw.replace(/#.*$/, "").trim();
    const m = /^([A-Za-z_][\w-]*)\s*:\s*(.*)$/.exec(line);
    if (m) out[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
  return out;
}

// Credentials file format (one per line):  token = envd_...
export function loadConfig(env: NodeJS.ProcessEnv = process.env, settings = readSettings()): ClientConfig {
  const baseUrl = env.ENVCTL_API ?? settings.api ?? "http://127.0.0.1:8900";
  const scope = settings.scope ?? "branch";
  if (scope !== "branch" && scope !== "project") throw new Error(`envctl.yaml: unknown scope ${JSON.stringify(scope)}`);
  let token = env.ENVCTL_TOKEN ?? "";
  if (!token) {
    const path = env.ENVCTL_CREDENTIALS ?? join(homedir(), ".envctl", "credentials");
    for (const line of readFileSync(path, "utf8").split("\n")) {
      const m = /^\s*token\s*=\s*(\S+)\s*$/.exec(line);
      if (m) token = m[1];
    }
  }
  if (!token) throw new Error("no API token: set ENVCTL_TOKEN or ~/.envctl/credentials");
  return { baseUrl: baseUrl.replace(/\/$/, ""), token, scope };
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export class CloudClient {
  private readonly cfg: ClientConfig;
  private readonly log: (msg: string) => void;

  constructor(cfg: ClientConfig, log: (msg: string) => void = (m) => process.stderr.write(m + "\n")) {
    this.cfg = cfg;
    this.log = log;
  }

  async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    for (let attempt = 0; ; attempt++) {
      const res = await fetch(this.cfg.baseUrl + path, {
        method,
        headers: { authorization: `Bearer ${this.cfg.token}`, "content-type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      const payload = await res.json().catch(() => null);
      if (res.status === 429 && attempt < 100) {
        const wait = Number(res.headers.get("retry-after") ?? "5");
        this.log(`rate limited on ${method} ${path}; retrying in ${wait}s`);
        await sleep(wait * 1000);
        continue;
      }
      if (!res.ok) {
        const msg = (payload as { error?: string } | null)?.error ?? res.statusText;
        throw new ApiError(res.status, payload, `${method} ${path} -> ${res.status}: ${msg}`);
      }
      return payload as T;
    }
  }

  async listResources(): Promise<Resource[]> {
    const out: Resource[] = [];
    let cursor: string | null = "0";
    while (cursor !== null) {
      const page: { resources: Resource[]; next_cursor: string | null } =
        await this.request("GET", `/v1/resources?cursor=${encodeURIComponent(cursor)}&limit=20`);
      out.push(...page.resources);
      cursor = page.next_cursor;
    }
    return out;
  }

  deleteResource(id: string): Promise<{ deleted: string }> {
    return this.request("DELETE", `/v1/resources/${encodeURIComponent(id)}`);
  }
}
