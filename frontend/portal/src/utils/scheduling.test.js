import { describe, expect, it } from "vitest";
import {
  NEW_PATIENT,
  defaultPatientChoice,
  formatAppointment,
  formatBirthDate,
  formatSlotTime,
  suggestedDoctorId,
  todayInClinic,
} from "./scheduling.js";

// \s also covers the narrow space some ICU versions put before AM/PM
const plain = (text) => text.replace(/\s/g, " ");

describe("todayInClinic", () => {
  it("is the clinic's date, not the browser's", () => {
    // 20:00 UTC on the 21st is already 01:00 on the 22nd in Pakistan
    expect(todayInClinic(new Date("2026-09-21T20:00:00Z"))).toBe("2026-09-22");
    expect(todayInClinic(new Date("2026-09-21T10:00:00Z"))).toBe("2026-09-21");
  });
});

describe("formatting times", () => {
  it("shows slots and appointments in clinic time", () => {
    // 05:00 UTC is 10:00 in Pakistan
    expect(plain(formatSlotTime("2026-09-24T05:00:00+00:00"))).toBe("10:00 AM");
    expect(plain(formatAppointment("2026-09-24T05:00:00+00:00"))).toBe(
      "Thu, Sep 24, 10:00 AM",
    );
  });

  it("never moves a birthday to the day before", () => {
    expect(formatBirthDate("1998-05-04")).toBe("May 4, 1998");
  });

  it("returns nothing for a missing or broken value", () => {
    expect(formatSlotTime(undefined)).toBe("");
    expect(formatAppointment("not a date")).toBe("");
    expect(formatBirthDate(null)).toBe("");
  });
});

describe("defaultPatientChoice", () => {
  const ayesha = { id: "p1", full_name: "Ayesha Khan" };
  const bilal = { id: "p2", full_name: "Bilal Khan" };

  it("picks the patient with the name that was given", () => {
    const request = { patient_name: " ayesha khan", returning_patient: "no" };
    expect(defaultPatientChoice(request, [bilal, ayesha])).toBe("p1");
  });

  it("starts a new record for a first-time patient", () => {
    const request = { patient_name: "Sara Ali", returning_patient: "no" };
    expect(defaultPatientChoice(request, [ayesha])).toBe(NEW_PATIENT);
  });

  it("picks the only patient on a returning patient's number", () => {
    const request = { patient_name: null, returning_patient: "yes" };
    expect(defaultPatientChoice(request, [ayesha])).toBe("p1");
  });

  it("makes the receptionist choose when a family shares the number", () => {
    const request = { patient_name: null, returning_patient: "yes" };
    expect(defaultPatientChoice(request, [ayesha, bilal])).toBe("");
  });

  it("starts a new record when nobody is on the number", () => {
    const request = { patient_name: null, returning_patient: "yes" };
    expect(defaultPatientChoice(request, [])).toBe(NEW_PATIENT);
  });
});

describe("suggestedDoctorId", () => {
  const doctors = [
    { id: "d1", specialization: "Cardiologist" },
    { id: "d2", specialization: "dermatologist " },
  ];

  it("matches the suggested department without case", () => {
    expect(suggestedDoctorId(doctors, "Dermatologist")).toBe("d2");
  });

  it("suggests nobody when nothing matches or nothing was suggested", () => {
    expect(suggestedDoctorId(doctors, "Neurologist")).toBe("");
    expect(suggestedDoctorId(doctors, null)).toBe("");
  });
});
