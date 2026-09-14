import { z } from "zod";

/*
  Mirrors UserLogin in app/schemas/user_login.py.

  No length rule on the password, matching the server: an account created
  before the create-time minimum existed must still be able to sign in.
*/
export const userLoginSchema = z.object({
  // Trimmed before the format check. See the note in staff.js.
  email: z
    .string()
    .trim()
    .pipe(
      z
        .email("Enter a valid email address.")
        .max(254, "Email address cannot be longer than 254 characters."),
    ),
  password: z.string().min(1, "Password is required."),
});
