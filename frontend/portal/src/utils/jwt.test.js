import { describe, expect, it } from "vitest";
import { decodeToken, isExpired } from "./jwt.js";

// Signature is irrelevant here: nothing in this module verifies one.
function makeToken(payload) {
  const encode = (value) =>
    Buffer.from(JSON.stringify(value)).toString("base64url");

  return `${encode({ alg: "HS256", typ: "JWT" })}.${encode(payload)}.signature`;
}

describe("decodeToken", () => {
  it("reads the claims the backend sends", () => {
    const token = makeToken({ sub: "abc123", role: "admin", exp: 1893456000 });

    expect(decodeToken(token)).toEqual({
      sub: "abc123",
      role: "admin",
      exp: 1893456000,
    });
  });

  it("handles multi-byte characters in a claim", () => {
    const token = makeToken({ name: "Ayesha Malik ☑" });
    expect(decodeToken(token).name).toBe("Ayesha Malik ☑");
  });

  it("returns null for anything that is not a token", () => {
    expect(decodeToken("")).toBeNull();
    expect(decodeToken("not-a-token")).toBeNull();
    expect(decodeToken("a.b.c")).toBeNull();
    expect(decodeToken(null)).toBeNull();
  });
});

describe("isExpired", () => {
  const inSeconds = (offset) => Math.floor(Date.now() / 1000) + offset;

  it("accepts a token with time left", () => {
    expect(isExpired({ exp: inSeconds(3600) })).toBe(false);
  });

  it("rejects one that has already lapsed", () => {
    expect(isExpired({ exp: inSeconds(-60) })).toBe(true);
  });

  it("rejects one about to lapse, so it cannot die mid-request", () => {
    expect(isExpired({ exp: inSeconds(10) })).toBe(true);
  });

  it("defers to the server when there is no exp claim", () => {
    expect(isExpired({ role: "admin" })).toBe(false);
    expect(isExpired(null)).toBe(false);
  });
});
