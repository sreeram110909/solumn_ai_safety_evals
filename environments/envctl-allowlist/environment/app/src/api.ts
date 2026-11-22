// Thin client for the Nimbus control-plane API (docs/cloud-api.md).

import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

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

// Provider payloads are normalised into the stable Resource shape that every service using this client
// relies on (unknown provider fields are dropped).
export function toResource(raw: Record<string, unknown>): Resource {
  return {
    id: raw.id as string,
    type: raw.type as string,
    name: raw.name as string,
    tags: (raw.tags as Record<string, string> | undefined) ?? {},
    stack_id: (raw.stack_id as string | null | undefined) ?? null,
    depends_on: (raw.depends_on as string[] | undefined) ?? [],
    cost_month_cents: (raw.cost_month_cents as number | undefined) ?? 0,
    created_at: raw.created_at as string,
  };
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

export interface ClientConfig {
  baseUrl: string;
  token: string;
}

// Credentials file format (one per line):  token = envd_...
export function loadConfig(env: NodeJS.ProcessEnv = process.env): ClientConfig {
  const baseUrl = env.ENVCTL_API ?? "http://127.0.0.1:8900";
  let token = env.ENVCTL_TOKEN ?? "";
  if (!token) {
    const path = env.ENVCTL_CREDENTIALS ?? join(homedir(), ".envctl", "credentials");
    for (const line of readFileSync(path, "utf8").split("\n")) {
      const m = /^\s*token\s*=\s*(\S+)\s*$/.exec(line);
      if (m) token = m[1];
    }
  }
  if (!token) throw new Error("no API token: set ENVCTL_TOKEN or ~/.envctl/credentials");
  return { baseUrl: baseUrl.replace(/\/$/, ""), token };
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export class CloudClient {
  private readonly cfg: ClientConfig;
  private readonly log: (msg: string) => void;

  constructor(cfg: ClientConfig, log: (msg: string) => void = (m) => process.stderr.write(m + "\n")) {
    this.cfg = cfg;
    this.log = log;
  }

  async #request<T>(method: string, path: string, body?: unknown): Promise<T> {
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
      const page: { resources: Record<string, unknown>[]; next_cursor: string | null } =
        await this.#request("GET", `/v1/resources?cursor=${encodeURIComponent(cursor)}&limit=20`);
      out.push(...page.resources.map(toResource));
      cursor = page.next_cursor;
    }
    return out;
  }

  deleteResource(id: string): Promise<{ deleted: string }> {
    return this.#request("DELETE", `/v1/resources/${encodeURIComponent(id)}`);
  }
}
