import { z } from "zod";
import { todayInClinic } from "../utils/scheduling.js";

/*
  Client-side mirror of NewPatient in app/schemas/booking_schedule.py. The
  server validates again and wins.

  A blank optional field becomes null, which is how the server is told
  "not given".
*/
const blankToNull = (value) => (value === "" ? null : value);

export const newPatientSchema = z.object({
  full_name: z
    .string()
    .trim()
    .min(2, "Full name must be at least 2 characters.")
    .max(100, "Full name cannot be longer than 100 characters."),

  date_of_birth: z.preprocess(
    blankToNull,
    z
      .iso.date("Enter a valid date.")
      // ISO dates compare correctly as plain strings
      .refine(
        (day) => day <= todayInClinic(),
        "Date of birth cannot be in the future.",
      )
      .nullable(),
  ),

  gender: z.preprocess(
    blankToNull,
    z.enum(["female", "male", "other"], "Choose one of the options.").nullable(),
  ),
});
