import { describe, expect, it } from "vitest";
import { initialsFrom } from "./initials.js";

describe("initialsFrom", () => {
  it("takes the first and last name", () => {
    expect(initialsFrom("Sara Khan")).toBe("SK");
  });

  it("drops an honorific so clinicians do not all share a D", () => {
    expect(initialsFrom("Dr. Sara Khan")).toBe("SK");
    expect(initialsFrom("Prof Ayesha Malik")).toBe("AM");
    expect(initialsFrom("Hafiz Bilal Ahmed")).toBe("BA");
  });

  it("ignores the middle of a longer name", () => {
    expect(initialsFrom("Muhammad Bilal Ahmed Khan")).toBe("MK");
  });

  it("returns one letter for a single name", () => {
    expect(initialsFrom("Cher")).toBe("C");
  });

  it("collapses extra whitespace", () => {
    expect(initialsFrom("   Sara    Khan  ")).toBe("SK");
  });

  it("keeps the title when there is nothing else", () => {
    expect(initialsFrom("Dr.")).toBe("D");
  });

  it("falls back to a placeholder rather than an empty circle", () => {
    expect(initialsFrom("")).toBe("?");
    expect(initialsFrom(null)).toBe("?");
    expect(initialsFrom(undefined)).toBe("?");
  });
});
