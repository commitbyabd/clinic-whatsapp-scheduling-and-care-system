import { z } from "zod";
import { email, password } from "./staff.js";

/*
  Client-side mirrors of PasswordChange and PasswordReset in
  app/schemas/password_update.py. The new password has the same limits as
  a new account's. confirm_password never leaves the browser: it only
  catches a typo before it locks someone out.
*/
const mustMatch = (values, ctx) => {
  if (values.confirm_password !== values.new_password) {
    ctx.addIssue({
      code: "custom",
      path: ["confirm_password"],
      message: "The two passwords do not match.",
    });
  }
};

export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "Enter your current password."),
    new_password: password,
    confirm_password: z.string(),
  })
  .superRefine((values, ctx) => {
    mustMatch(values, ctx);
    if (
      values.new_password &&
      values.new_password === values.current_password
    ) {
      ctx.addIssue({
        code: "custom",
        path: ["new_password"],
        message: "Choose a password different from your current one.",
      });
    }
  });

export const resetPasswordSchema = z
  .object({
    new_password: password,
    confirm_password: z.string(),
  })
  .superRefine(mustMatch);

// The sign-in page's "forgot your password" box, mirroring
// PasswordHelpRequest in app/schemas/password_help.py.
export const passwordHelpSchema = z.object({ email });
