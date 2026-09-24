import { describe, expect, it } from "vitest";
import {
  askedForLabel,
  formatReceived,
  patientLabel,
  reasonLabel,
} from "./bookingRequest.js";

describe("reasonLabel", () => {
  it("uses the wording the patient saw on WhatsApp", () => {
    expect(reasonLabel("symptoms")).toBe("Feeling unwell");
    expect(reasonLabel("followup")).toBe("Follow-up visit");
  });

  it("says so when there is no reason", () => {
    expect(reasonLabel(undefined)).toBe("Reason not given");
  });
});

describe("patientLabel", () => {
  it("uses the name when the patient gave one", () => {
    expect(
      patientLabel({ patient_name: "Ayesha Khan", whatsapp_number: "+92300" }),
    ).toBe("Ayesha Khan");
  });

  it("falls back to the number for a returning patient", () => {
    expect(
      patientLabel({ patient_name: null, whatsapp_number: "+92300" }),
    ).toBe("+92300");
  });
});

describe("formatReceived", () => {
  it("shows the time in the clinic's time zone", () => {
    // 09:30 UTC is 14:30 in Pakistan. \s also covers the narrow space some
    // ICU versions put before PM.
    const text = formatReceived("2026-09-21T09:30:00+00:00").replace(
      /\s/g,
      " ",
    );
    expect(text).toBe("Sep 21, 2:30 PM");
  });

  it("returns nothing for a missing or broken date", () => {
    expect(formatReceived(undefined)).toBe("");
    expect(formatReceived("not a date")).toBe("");
  });
});

describe("askedForLabel", () => {
  // \s also covers the narrow space some ICU versions put before AM/PM
  const plain = (text) => text.replace(/\s/g, " ");

  it("names the time and doctor the patient picked", () => {
    const label = askedForLabel({
      requested_slot: "2026-09-23T04:00:00+00:00",
      requested_doctor_name: "Dr. Sara Khan",
    });
    expect(plain(label)).toBe(
      "Asked for: Wed, Sep 23, 9:00 AM, with Dr. Sara Khan",
    );
  });

  it("falls back to the words they typed", () => {
    expect(askedForLabel({ preferred_time_text: "tomorrow at 9am" })).toBe(
      "Prefers: tomorrow at 9am",
    );
  });

  it("keeps the doctor even when no open time suited", () => {
    const label = askedForLabel({
      preferred_time_text: "Friday evening",
      requested_doctor_name: "Dr. Sara Khan",
    });
    expect(label).toBe("Prefers: Friday evening, with Dr. Sara Khan");
  });

  it("says so when there is nothing at all", () => {
    expect(askedForLabel({})).toBe("Prefers: no time given");
  });
});
