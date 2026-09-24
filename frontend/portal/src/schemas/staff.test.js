import { describe, expect, it } from "vitest";
import {
  doctorCreateSchema,
  doctorUpdateSchema,
  receptionistCreateSchema,
  receptionistUpdateSchema,
} from "./staff.js";
import { validateField, validateWith } from "./validate.js";

const doctor = {
  full_name: "Dr. Sara Khan",
  email: "sara@clinic.com",
  password: "correct horse",
  specialization: "Dermatologist",
  booking_mode: "appointment",
};

describe("validateWith", () => {
  it("returns the parsed data, not the input", () => {
    const { valid, data } = validateWith(doctorCreateSchema, {
      ...doctor,
      full_name: "  Dr. Sara Khan  ",
      email: "  sara@clinic.com  ",
    });

    expect(valid).toBe(true);
    expect(data.full_name).toBe("Dr. Sara Khan");
    expect(data.email).toBe("sara@clinic.com");
  });

  it("leaves the password untouched, spaces included", () => {
    const { data } = validateWith(doctorCreateSchema, {
      ...doctor,
      password: "  spaced out  ",
    });

    expect(data.password).toBe("  spaced out  ");
  });

  it("accepts an email that was pasted with surrounding spaces", () => {
    const { valid } = validateWith(doctorCreateSchema, {
      ...doctor,
      email: "   sara@clinic.com   ",
    });

    expect(valid).toBe(true);
  });

  it("drops keys the schema does not declare", () => {
    const { data } = validateWith(receptionistCreateSchema, doctor);

    expect(data).not.toHaveProperty("specialization");
    expect(Object.keys(data).sort()).toEqual([
      "email",
      "full_name",
      "password",
    ]);
  });

  it("drops the password when editing, since PATCH ignores it", () => {
    const { data } = validateWith(doctorUpdateSchema, doctor);

    expect(data).not.toHaveProperty("password");
  });

  it("reports one message per field", () => {
    const { valid, data, errors } = validateWith(doctorCreateSchema, {
      full_name: "S",
      email: "nope",
      password: "short",
      specialization: "",
      booking_mode: "appointment",
    });

    expect(valid).toBe(false);
    expect(data).toBeNull();
    expect(Object.keys(errors).sort()).toEqual([
      "email",
      "full_name",
      "password",
      "specialization",
    ]);
    expect(errors.password).toMatch(/at least 8/);
  });

  it("takes a specialization only from the chatbot's departments", () => {
    // "Dermatology" would never match the chatbot's "Dermatologist"
    const { errors } = validateWith(doctorCreateSchema, {
      ...doctor,
      specialization: "Dermatology",
    });
    expect(errors.specialization).toMatch(/from the list/);

    const { valid } = validateWith(doctorUpdateSchema, {
      ...doctor,
      specialization: "ENT Specialist",
    });
    expect(valid).toBe(true);
  });

  it("takes only the two booking modes the chat can answer for", () => {
    const { errors } = validateWith(doctorCreateSchema, {
      ...doctor,
      booking_mode: "whenever",
    });
    expect(errors.booking_mode).toMatch(/how this doctor sees patients/);

    const { valid, data } = validateWith(doctorUpdateSchema, {
      ...doctor,
      booking_mode: "walk_in",
    });
    expect(valid).toBe(true);
    expect(data.booking_mode).toBe("walk_in");
  });

  it("enforces the server's length ceilings", () => {
    const { errors } = validateWith(doctorCreateSchema, {
      ...doctor,
      full_name: "a".repeat(101),
      email: `${"a".repeat(250)}@clinic.com`,
    });

    expect(errors.full_name).toMatch(/100/);
    expect(errors.email).toMatch(/254/);
  });
});

describe("validateField", () => {
  it("uses the same rule as the whole-form check", () => {
    expect(validateField(doctorCreateSchema, "full_name", "S")).toMatch(
      /at least 2/,
    );
    expect(validateField(doctorCreateSchema, "full_name", "Sara Khan")).toBe(
      "",
    );
  });

  it("stays silent about a field the schema does not declare", () => {
    expect(validateField(doctorUpdateSchema, "password", "x")).toBe("");
    expect(validateField(receptionistUpdateSchema, "specialization", "")).toBe(
      "",
    );
  });
});
