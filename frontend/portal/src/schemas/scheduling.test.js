import { describe, expect, it } from "vitest";
import { newPatientSchema } from "./scheduling.js";
import { validateField, validateWith } from "./validate.js";

describe("newPatientSchema", () => {
  it("sends blank optional fields as null", () => {
    const { valid, data } = validateWith(newPatientSchema, {
      full_name: "  Ayesha Khan ",
      date_of_birth: "",
      gender: "",
    });
    expect(valid).toBe(true);
    expect(data).toEqual({
      full_name: "Ayesha Khan",
      date_of_birth: null,
      gender: null,
    });
  });

  it("keeps a date of birth and gender that were given", () => {
    const { data } = validateWith(newPatientSchema, {
      full_name: "Ayesha Khan",
      date_of_birth: "1998-05-04",
      gender: "female",
    });
    expect(data.date_of_birth).toBe("1998-05-04");
    expect(data.gender).toBe("female");
  });

  it("refuses a short name and a birthday in the future", () => {
    const { valid, errors } = validateWith(newPatientSchema, {
      full_name: "A",
      date_of_birth: "2999-01-01",
      gender: "",
    });
    expect(valid).toBe(false);
    expect(errors.full_name).toMatch(/at least 2/);
    expect(errors.date_of_birth).toMatch(/future/);
  });

  it("checks one field at a time on blur", () => {
    expect(validateField(newPatientSchema, "date_of_birth", "")).toBe("");
    expect(validateField(newPatientSchema, "full_name", " ")).toMatch(
      /at least 2/,
    );
  });
});
