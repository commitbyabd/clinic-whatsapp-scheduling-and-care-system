import { describe, expect, it } from "vitest";
import { consultationSchema, medicalSchema } from "./consultation.js";
import { validateWithPaths } from "./validate.js";
import {
  consultationForm,
  consultationPayload,
  emptyPrescription,
  joinList,
  parseList,
} from "../utils/consultation.js";

const form = (changes = {}) => ({
  ...consultationForm({ consultation: null, doctor_notes: "" }),
  ...changes,
});

describe("consultation form", () => {
  it("starts from what was saved, every field as text", () => {
    const loaded = consultationForm({
      consultation: {
        diagnosis: "Eczema",
        vitals: { bp: "120/80", pulse: 72, temperature: null, weight: 61.5 },
        prescriptions: [{ medicine: "Cream", dose: null, days: 7 }],
        follow_up_on: "2026-10-01",
      },
      doctor_notes: "Avoid the soap.",
    });
    expect(loaded.pulse).toBe("72");
    expect(loaded.temperature).toBe("");
    expect(loaded.prescriptions[0]).toEqual({
      medicine: "Cream",
      dose: "",
      frequency: "",
      days: "7",
      instructions: "",
    });
    expect(loaded.doctor_notes).toBe("Avoid the soap.");
  });

  it("sends numbers as numbers and blanks as null", () => {
    const { valid, data } = validateWithPaths(
      consultationSchema,
      form({ pulse: "72", temperature: " 98.6 ", weight: "" }),
    );
    expect(valid).toBe(true);
    const payload = consultationPayload(data);
    expect(payload.vitals).toEqual({
      bp: null,
      pulse: 72,
      temperature: 98.6,
      weight: null,
    });
    expect(payload.follow_up_on).toBeNull();
  });

  it("drops an empty medicine row but not a started one", () => {
    const rows = [
      emptyPrescription(),
      { ...emptyPrescription(), medicine: "Cream", days: "5" },
    ];
    const { data } = validateWithPaths(
      consultationSchema,
      form({ prescriptions: rows }),
    );
    const payload = consultationPayload(data);
    expect(payload.prescriptions).toHaveLength(1);
    expect(payload.prescriptions[0].days).toBe(5);
  });

  it("points at the exact field that is wrong", () => {
    const { valid, errors } = validateWithPaths(
      consultationSchema,
      form({
        bp: "high",
        temperature: "37",
        prescriptions: [{ ...emptyPrescription(), dose: "500 mg" }],
      }),
    );
    expect(valid).toBe(false);
    expect(errors.bp).toMatch(/120\/80/);
    // 37 is a Celsius reading; the form takes Fahrenheit
    expect(errors.temperature).toMatch(/°F/);
    expect(errors["prescriptions.0.medicine"]).toBe("Enter the medicine.");
  });
});

describe("medical details", () => {
  it("splits a typed list and drops repeats", () => {
    expect(parseList("Penicillin,  dust, ,penicillin")).toEqual([
      "Penicillin",
      "dust",
    ]);
    expect(joinList(["Penicillin", "dust"])).toBe("Penicillin, dust");
  });

  it("takes a known blood group or none", () => {
    const blank = medicalSchema.safeParse({
      allergies: [],
      chronic_conditions: [],
      blood_group: "",
    });
    expect(blank.data.blood_group).toBeNull();

    const wrong = medicalSchema.safeParse({
      allergies: [],
      chronic_conditions: [],
      blood_group: "C+",
    });
    expect(wrong.success).toBe(false);
  });
});
