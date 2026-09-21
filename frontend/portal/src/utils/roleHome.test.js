import { describe, expect, it } from "vitest";
import { homePathFor } from "./roleHome.js";

describe("homePathFor", () => {
  it("sends each role to its own portal", () => {
    expect(homePathFor("admin")).toBe("/dashboard");
    expect(homePathFor("receptionist")).toBe("/reception");
  });

  it("sends a role without a portal to the admin page, which refuses it", () => {
    expect(homePathFor("doctor")).toBe("/dashboard");
    expect(homePathFor(undefined)).toBe("/dashboard");
  });
});
