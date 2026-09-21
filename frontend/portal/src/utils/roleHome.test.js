import { describe, expect, it } from "vitest";
import { homePathFor } from "./roleHome.js";

describe("homePathFor", () => {
  it("sends each role to its own portal", () => {
    expect(homePathFor("admin")).toBe("/dashboard");
    expect(homePathFor("receptionist")).toBe("/reception");
    expect(homePathFor("doctor")).toBe("/doctor");
  });

  it("sends an unknown role to the admin page, which refuses it", () => {
    expect(homePathFor("patient")).toBe("/dashboard");
    expect(homePathFor(undefined)).toBe("/dashboard");
  });
});
