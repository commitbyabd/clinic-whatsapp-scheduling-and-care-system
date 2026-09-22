import { describe, expect, it } from "vitest";
import {
  canWriteUp,
  dayHeading,
  groupByDay,
  patientFacts,
  shiftDay,
  statusLabel,
} from "./appointments.js";

const visit = (id, scheduled_for) => ({ id, scheduled_for });

describe("statusLabel and canWriteUp", () => {
  it("names every status", () => {
    expect(statusLabel("no_show")).toBe("No-show");
    expect(statusLabel("booked")).toBe("Booked");
  });

  it("lets anything but a cancelled or missed visit be written up", () => {
    expect(canWriteUp("booked")).toBe(true);
    expect(canWriteUp("completed")).toBe(true);
    expect(canWriteUp("no_show")).toBe(false);
    expect(canWriteUp("cancelled")).toBe(false);
  });
});

describe("patientFacts", () => {
  it("says what is known", () => {
    expect(patientFacts({ age: 34, gender: "female" })).toBe("Age 34 · Female");
    expect(patientFacts({ age: null, gender: "male" })).toBe("Male");
    expect(patientFacts({})).toBe("");
  });
});

describe("dayHeading", () => {
  const today = "2026-09-21";

  it("names the days either side of today", () => {
    expect(dayHeading("2026-09-21", today)).toBe("Today · Mon, Sep 21");
    expect(dayHeading("2026-09-22", today)).toBe("Tomorrow · Tue, Sep 22");
    expect(dayHeading("2026-09-20", today)).toBe("Yesterday · Sun, Sep 20");
    expect(dayHeading("2026-09-24", today)).toBe("Thu, Sep 24");
  });
});

describe("shiftDay", () => {
  it("moves across the ends of months and years", () => {
    expect(shiftDay("2026-09-30", 1)).toBe("2026-10-01");
    expect(shiftDay("2026-01-01", -1)).toBe("2025-12-31");
  });
});

describe("groupByDay", () => {
  const today = "2026-09-21";
  const list = [
    visit("later-today", "2026-09-21T09:00:00+00:00"),
    visit("early-today", "2026-09-21T04:00:00+00:00"),
    // 20:00 UTC on the 21st is 01:00 on the 22nd in Pakistan
    visit("after-midnight", "2026-09-21T20:00:00+00:00"),
    visit("yesterday", "2026-09-20T05:00:00+00:00"),
    visit("last-week", "2026-09-14T05:00:00+00:00"),
  ];

  it("lists today onwards by clinic day, soonest first", () => {
    const groups = groupByDay(list, "upcoming", today);
    expect(groups.map((g) => g.day)).toEqual(["2026-09-21", "2026-09-22"]);
    expect(groups[0].appointments.map((a) => a.id)).toEqual([
      "early-today",
      "later-today",
    ]);
    expect(groups[1].appointments[0].id).toBe("after-midnight");
  });

  it("lists earlier days latest first, each day in time order", () => {
    const groups = groupByDay(list, "past", today);
    expect(groups.map((g) => g.day)).toEqual(["2026-09-20", "2026-09-14"]);
  });
});
