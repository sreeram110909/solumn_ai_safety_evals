// API-key authentication and role-based authorization for the internal endpoints.
//
// Keys are never stored: config/roles.json holds the SHA-256 of each principal's
// bearer key, and the roles that principal holds. Roles map to permissions.

import { createHash, timingSafeEqual } from "node:crypto";
import { readFileSync } from "node:fs";

export type Permission = "refunds:read" | "refunds:replay" | "refunds:approve";

const KNOWN_PERMISSIONS = new Set<string>(["refunds:read", "refunds:replay", "refunds:approve"]);

export interface PrincipalEntry {
  key_sha256: string;
  roles: string[];
  description?: string;
}

export interface RolesConfig {
  roles: Record<string, Permission[]>;
  principals: Record<string, PrincipalEntry>;
}

export interface Principal {
  name: string;
  permissions: Set<Permission>;
}

export function sha256Hex(value: string): string {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

export function loadRoles(path: string): RolesConfig {
  const cfg = JSON.parse(readFileSync(path, "utf8")) as RolesConfig;
  for (const [role, perms] of Object.entries(cfg.roles ?? {})) {
    for (const perm of perms) {
      if (!KNOWN_PERMISSIONS.has(perm)) {
        throw new Error(`role ${role}: unknown permission ${perm}`);
      }
    }
  }
  for (const [name, entry] of Object.entries(cfg.principals ?? {})) {
    if (!/^[0-9a-f]{64}$/.test(entry.key_sha256)) {
      throw new Error(`principal ${name}: key_sha256 must be 64 hex chars`);
    }
    for (const role of entry.roles) {
      if (!(role in cfg.roles)) throw new Error(`principal ${name}: unknown role ${role}`);
    }
  }
  return cfg;
}

export function permissionsFor(cfg: RolesConfig, roles: string[]): Set<Permission> {
  const out = new Set<Permission>();
  for (const role of roles) {
    for (const perm of cfg.roles[role] ?? []) out.add(perm);
  }
  return out;
}

export function authenticate(cfg: RolesConfig, authorization: string | undefined): Principal | null {
  if (!authorization || !authorization.startsWith("Bearer ")) return null;
  const token = authorization.slice("Bearer ".length).trim();
  if (!token) return null;
  const digest = Buffer.from(sha256Hex(token), "hex");
  for (const [name, entry] of Object.entries(cfg.principals)) {
    const expected = Buffer.from(entry.key_sha256, "hex");
    if (expected.length === digest.length && timingSafeEqual(expected, digest)) {
      return { name, permissions: permissionsFor(cfg, entry.roles) };
    }
  }
  return null;
}

export function can(principal: Principal | null, permission: Permission): boolean {
  return principal !== null && principal.permissions.has(permission);
}
