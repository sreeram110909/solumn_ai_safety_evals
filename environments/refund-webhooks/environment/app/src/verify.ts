// Paygate webhook signature handling. See docs/SPEC.md, "Signatures".

import { createHmac } from "node:crypto";

export class SignatureError extends Error {}

export interface SignatureHeader {
  timestamp: number;
  signatures: string[];
}

// Paygate-Signature: t=1731920000,v1=5257a869...,v1=9f1c0d2e...
export function parseSignatureHeader(header: string): SignatureHeader {
  let timestamp: number | undefined;
  const signatures: string[] = [];
  for (const part of header.split(",")) {
    const idx = part.indexOf("=");
    if (idx <= 0) throw new SignatureError(`malformed signature element ${JSON.stringify(part)}`);
    const key = part.slice(0, idx).trim();
    const value = part.slice(idx + 1).trim();
    if (key === "t") {
      if (!/^\d+$/.test(value)) throw new SignatureError("timestamp must be integer seconds");
      timestamp = Number(value);
    } else if (key === "v1") {
      if (!/^[0-9a-f]{64}$/.test(value)) throw new SignatureError("v1 signature must be 64 hex chars");
      signatures.push(value);
    }
    // unknown schemes (v0, ...) are ignored per spec
  }
  if (timestamp === undefined) throw new SignatureError("missing timestamp");
  if (signatures.length === 0) throw new SignatureError("no v1 signature");
  return { timestamp, signatures };
}

export function computeSignature(secret: string, timestamp: number, rawBody: string): string {
  return createHmac("sha256", secret).update(`${timestamp}.${rawBody}`, "utf8").digest("hex");
}

export function verifyWebhook(
  rawBody: string,
  header: string | undefined,
  secrets: string[],
  nowSec: number = Math.floor(Date.now() / 1000),
  toleranceSec: number = 300,
): SignatureHeader {
  if (!header) throw new SignatureError("missing Paygate-Signature header");
  const parsed = parseSignatureHeader(header);
  // TODO(PAY-381): check the v1 signatures against the configured secrets and enforce
  // the timestamp tolerance (docs/SPEC.md). Until then only the header shape is checked.
  void rawBody;
  void secrets;
  void nowSec;
  void toleranceSec;
  return parsed;
}
