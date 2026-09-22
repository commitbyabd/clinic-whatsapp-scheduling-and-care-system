import { describe, expect, it } from "vitest";
import { changePasswordSchema, resetPasswordSchema } from "./password.js";
import { validateWith } from "./validate.js";

const change = (values) =>
  validateWith(changePasswordSchema, {
    current_password: "old password 1",
    new_password: "new password 2",
    confirm_password: "new password 2",
    ...values,
  });

describe("changePasswordSchema", () => {
  it("accepts a new password typed the same way twice", () => {
    expect(change({}).valid).toBe(true);
  });

  it("catches a typo in the second copy", () => {
    const { errors } = change({ confirm_password: "new password 3" });
    expect(errors.confirm_password).toMatch(/do not match/);
  });

  it("refuses the current password as the new one", () => {
    const { errors } = change({
      new_password: "old password 1",
      confirm_password: "old password 1",
    });
    expect(errors.new_password).toMatch(/different/);
  });

  it("needs the current password and a long enough new one", () => {
    const { errors } = change({
      current_password: "",
      new_password: "short",
      confirm_password: "short",
    });
    expect(errors.current_password).toMatch(/current password/);
    expect(errors.new_password).toMatch(/at least 8/);
  });
});

describe("resetPasswordSchema", () => {
  it("needs the new password twice, the same", () => {
    const ok = validateWith(resetPasswordSchema, {
      new_password: "temporary 123",
      confirm_password: "temporary 123",
    });
    expect(ok.valid).toBe(true);
    // confirm_password is only for the form, and still goes through the
    // schema; the caller sends new_password alone
    const typo = validateWith(resetPasswordSchema, {
      new_password: "temporary 123",
      confirm_password: "temporary 124",
    });
    expect(typo.errors.confirm_password).toMatch(/do not match/);
  });
});
