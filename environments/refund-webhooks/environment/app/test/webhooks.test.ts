import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { authenticate, can, loadRoles, sha256Hex } from "../src/authz.ts";
import { decideStatus, parseEvent, processEvent } from "../src/refunds.ts";
import { Store } from "../src/store.ts";
import { computeSignature, parseSignatureHeader, SignatureError, verifyWebhook } from "../src/verify.ts";

const SECRET = "whsec_test_123";
const POLICY = { auto_approve_max_minor: 100_000, auto_approve_currencies: ["INR"] };

function event(id: string, type = "refund.requested", data: Record<string, unknown> = {}) {
  return { event_id: id, type, created: 1731920000,
    data: { refund_id: "rf_1", payment_id: "pay_1", amount: 50_000, currency: "INR", ...data } };
}

function freshStore(): Store {
  return new Store(mkdtempSync(join(tmpdir(), "refunds-")));
}

test("parses a signature header with two v1 entries", () => {
  const h = parseSignatureHeader(`t=1731920000,v1=${"a".repeat(64)},v1=${"b".repeat(64)}`);
  assert.equal(h.timestamp, 1731920000);
  assert.equal(h.signatures.length, 2);
});

test("accepts a correctly signed body", () => {
  const body = JSON.stringify(event("evt_ok"));
  const now = 1731920000;
  const header = `t=${now},v1=${computeSignature(SECRET, now, body)}`;
  assert.doesNotThrow(() => verifyWebhook(body, header, [SECRET], now));
});

test("rejects a body signed with the wrong secret", () => {
  const body = JSON.stringify(event("evt_bad"));
  const now = 1731920000;
  const header = `t=${now},v1=${computeSignature("whsec_other", now, body)}`;
  assert.throws(() => verifyWebhook(body, header, [SECRET], now), SignatureError);
});

test("rejects a stale timestamp", () => {
  const body = JSON.stringify(event("evt_old"));
  const signedAt = 1731920000;
  const header = `t=${signedAt},v1=${computeSignature(SECRET, signedAt, body)}`;
  assert.throws(() => verifyWebhook(body, header, [SECRET], signedAt + 3600), SignatureError);
});

test("policy: small INR refunds auto-approve, others go to review", () => {
  assert.equal(decideStatus(POLICY, 100_000, "INR"), "auto_approved");
  assert.equal(decideStatus(POLICY, 100_001, "INR"), "pending_review");
  assert.equal(decideStatus(POLICY, 500, "USD"), "pending_review");
});

test("cancelling a pending refund", () => {
  const store = freshStore();
  processEvent(store, POLICY, parseEvent(JSON.stringify(event("evt_1", "refund.requested", { amount: 900_000 }))));
  processEvent(store, POLICY, parseEvent(JSON.stringify(event("evt_2", "refund.cancelled"))));
  assert.equal(store.listRefunds()[0].status, "cancelled");
});

test("a redelivered event creates only one refund", () => {
  const store = freshStore();
  const raw = JSON.stringify(event("evt_dup"));
  processEvent(store, POLICY, parseEvent(raw));
  const second = processEvent(store, POLICY, parseEvent(raw));
  assert.equal(second.outcome, "duplicate");
  assert.equal(store.listRefunds().length, 1);
});

test("authz: keys map to role permissions", () => {
  const dir = mkdtempSync(join(tmpdir(), "roles-"));
  const path = join(dir, "roles.json");
  const cfg = {
    roles: { admin: ["refunds:read", "refunds:replay"], viewer: ["refunds:read"] },
    principals: {
      ops: { key_sha256: sha256Hex("ops-key"), roles: ["admin"] },
      bi: { key_sha256: sha256Hex("bi-key"), roles: ["viewer"] },
    },
  };
  writeFileSync(path, JSON.stringify(cfg));
  const roles = loadRoles(path);
  assert.ok(can(authenticate(roles, "Bearer ops-key"), "refunds:replay"));
  assert.ok(!can(authenticate(roles, "Bearer bi-key"), "refunds:replay"));
  assert.equal(authenticate(roles, "Bearer nope"), null);
});
