// File-backed store for refunds, processed webhook events and raw event bodies.
// State is rewritten atomically (tmp file + rename) after every mutation.

import { appendFileSync, existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export type RefundStatus = "auto_approved" | "pending_review" | "cancelled";

export interface Refund {
  id: string;
  paygate_refund_id: string;
  payment_id: string;
  amount: number; // minor units (paise for INR)
  currency: string;
  status: RefundStatus;
  reason: string;
  source_event_id: string;
  created_at: string;
  updated_at: string;
}

interface State {
  next_seq: number;
  refunds: Record<string, Refund>;
  processed_events: Record<string, string>;
}

export class Store {
  private readonly dir: string;
  private state: State;

  constructor(dir: string) {
    this.dir = dir;
    mkdirSync(join(dir, "events"), { recursive: true });
    const path = join(dir, "state.json");
    this.state = existsSync(path)
      ? (JSON.parse(readFileSync(path, "utf8")) as State)
      : { next_seq: 1, refunds: {}, processed_events: {} };
  }

  private flush(): void {
    const path = join(this.dir, "state.json");
    writeFileSync(`${path}.tmp`, JSON.stringify(this.state, null, 2));
    renameSync(`${path}.tmp`, path);
  }

  newRefundId(): string {
    const id = `rfd_${String(this.state.next_seq).padStart(6, "0")}`;
    this.state.next_seq += 1;
    return id;
  }

  putRefund(refund: Refund): void {
    this.state.refunds[refund.id] = refund;
    this.flush();
  }

  getRefund(id: string): Refund | undefined {
    return this.state.refunds[id];
  }

  findByPaygateId(paygateRefundId: string): Refund[] {
    return Object.values(this.state.refunds).filter((r) => r.paygate_refund_id === paygateRefundId);
  }

  listRefunds(): Refund[] {
    return Object.values(this.state.refunds).sort((a, b) => a.id.localeCompare(b.id));
  }

  isProcessed(eventId: string): boolean {
    return eventId in this.state.processed_events;
  }

  markProcessed(eventId: string): void {
    this.state.processed_events[eventId] = new Date().toISOString();
    this.flush();
  }

  saveRawEvent(eventId: string, raw: string): void {
    writeFileSync(join(this.dir, "events", `${eventId.replace(/[^A-Za-z0-9_-]/g, "_")}.json`), raw);
  }

  loadRawEvent(eventId: string): string | undefined {
    const path = join(this.dir, "events", `${eventId.replace(/[^A-Za-z0-9_-]/g, "_")}.json`);
    return existsSync(path) ? readFileSync(path, "utf8") : undefined;
  }

  audit(entry: Record<string, unknown>): void {
    appendFileSync(join(this.dir, "audit.jsonl"), JSON.stringify({ at: new Date().toISOString(), ...entry }) + "\n");
  }
}
