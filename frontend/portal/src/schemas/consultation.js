import { z } from "zod";

/*
  Client-side mirrors of ConsultationUpdate and PatientMedicalUpdate in
  app/schemas/. Every limit matches the server, which validates again and
  wins. The form holds text, so numbers are parsed here: blank becomes null.
*/
const toNumber = (value) => {
  if (typeof value !== "string") return value;
  return value.trim() === "" ? null : Number(value.trim());
};

const optionalNumber = (check) => z.preprocess(toNumber, check.nullable());

const prescriptionSchema = z
  .object({
    medicine: z
      .string()
      .trim()
      .max(100, "Keep the medicine under 100 characters."),
    dose: z.string().trim().max(50, "Keep the dose under 50 characters."),
    frequency: z.string().trim().max(50, "Keep this under 50 characters."),
    days: optionalNumber(
      z
        .number("Days must be a number.")
        .int("Use whole days.")
        .min(1, "At least 1 day.")
        .max(365, "At most 365 days."),
    ),
    instructions: z
      .string()
      .trim()
      .max(200, "Keep the instructions under 200 characters."),
  })
  // An empty row is fine (it is dropped); a started one needs its medicine.
  .superRefine((row, ctx) => {
    const started =
      row.dose || row.frequency || row.days !== null || row.instructions;
    if (!row.medicine && started) {
      ctx.addIssue({
        code: "custom",
        path: ["medicine"],
        message: "Enter the medicine.",
      });
    }
  });

export const consultationSchema = z.object({
  diagnosis: z
    .string()
    .trim()
    .max(500, "Keep the diagnosis under 500 characters."),
  bp: z
    .string()
    .trim()
    .regex(/^(\d{2,3}\/\d{2,3})?$/, "Write it like 120/80."),
  pulse: optionalNumber(
    z
      .number("Pulse must be a number.")
      .int("Use a whole number.")
      .min(20, "Pulse must be between 20 and 250.")
      .max(250, "Pulse must be between 20 and 250."),
  ),
  // Fahrenheit, like the server
  temperature: optionalNumber(
    z
      .number("Temperature must be a number.")
      .min(80, "Use °F, between 80 and 115.")
      .max(115, "Use °F, between 80 and 115."),
  ),
  weight: optionalNumber(
    z
      .number("Weight must be a number.")
      .gt(0, "Weight must be more than 0.")
      .max(400, "Weight must be 400 kg or less."),
  ),
  prescriptions: z
    .array(prescriptionSchema)
    .max(20, "At most 20 medicines."),
  follow_up_on: z.string(),
  doctor_notes: z
    .string()
    .trim()
    .max(5000, "Notes cannot be longer than 5000 characters."),
});

export const BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

const listItem = z
  .string()
  .max(100, "Keep each item under 100 characters.");

// Takes the lists already split (utils/consultation.js parseList)
export const medicalSchema = z.object({
  allergies: z.array(listItem).max(30, "At most 30 allergies."),
  chronic_conditions: z.array(listItem).max(30, "At most 30 conditions."),
  blood_group: z.preprocess(
    (value) => (value === "" ? null : value),
    z.enum(BLOOD_GROUPS, "Choose a blood group from the list.").nullable(),
  ),
});
