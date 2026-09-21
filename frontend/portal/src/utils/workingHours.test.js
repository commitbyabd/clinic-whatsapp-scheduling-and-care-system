import { describe, expect, it } from "vitest";
import {
  formatClock,
  hasWorkingHours,
  weekErrors,
  weekFromSchedule,
  weekPayload,
  weeklyHours,
} from "./workingHours.js";

const SAVED = {
  working_hours: [
    { day_of_week: 0, start_time: "17:00", end_time: "20:00" },
    { day_of_week: 0, start_time: "09:00", end_time: "13:00" },
    { day_of_week: 5, start_time: "10:00", end_time: "14:00" },
  ],
  slot_minutes: 20,
  blackout_dates: ["2026-09-25T00:00:00+00:00"],
};

const week = (days, slotMinutes = "30") => ({
  slotMinutes,
  days: [0, 1, 2, 3, 4, 5, 6].map((day) => days[day] ?? []),
  daysOff: [],
});

describe("weekFromSchedule", () => {
  it("puts each block under its day, in time order", () => {
    const loaded = weekFromSchedule(SAVED);
    expect(loaded.days[0]).toEqual([
      { start: "09:00", end: "13:00" },
      { start: "17:00", end: "20:00" },
    ]);
    expect(loaded.days[5]).toEqual([{ start: "10:00", end: "14:00" }]);
    expect(loaded.slotMinutes).toBe("20");
    expect(loaded.daysOff).toEqual(["2026-09-25"]);
  });

  it("treats the empty list the API sends as no schedule", () => {
    const empty = weekFromSchedule([]);
    expect(empty.days.every((blocks) => blocks.length === 0)).toBe(true);
    expect(empty.slotMinutes).toBe("30");
    expect(hasWorkingHours([])).toBe(false);
    expect(hasWorkingHours(SAVED)).toBe(true);
  });

  it("round-trips into the body the API takes", () => {
    const payload = weekPayload(weekFromSchedule(SAVED));
    expect(payload.working_hours).toHaveLength(3);
    expect(payload.working_hours[0]).toEqual({
      day_of_week: 0,
      start_time: "09:00",
      end_time: "13:00",
    });
    expect(payload.slot_minutes).toBe(20);
    expect(payload.blackout_dates).toEqual(["2026-09-25"]);
  });
});

describe("weekErrors", () => {
  it("accepts a sensible week", () => {
    expect(weekErrors(weekFromSchedule(SAVED))).toEqual({});
  });

  it("names the block that is wrong", () => {
    const errors = weekErrors(
      week({
        0: [{ start: "13:00", end: "09:00" }],
        1: [{ start: "09:00", end: "" }],
        2: [
          { start: "09:00", end: "13:00" },
          { start: "12:00", end: "15:00" },
        ],
        3: [{ start: "09:00", end: "09:20" }],
      }),
    );
    expect(errors["0.0"]).toMatch(/after the start/);
    expect(errors["1.0"]).toMatch(/start and an end/);
    expect(errors["2.1"]).toBe("Overlaps 9:00 AM to 1:00 PM.");
    // too short for a single 30-minute slot, so nobody could book it
    expect(errors["3.0"]).toMatch(/Shorter than one 30-minute slot/);
  });
});

describe("formatting", () => {
  it("shows clock times the way people read them", () => {
    expect(formatClock("00:30")).toBe("12:30 AM");
    expect(formatClock("13:05")).toBe("1:05 PM");
  });

  it("adds up the hours in a week", () => {
    expect(weeklyHours(weekFromSchedule(SAVED))).toBe(11);
  });
});
