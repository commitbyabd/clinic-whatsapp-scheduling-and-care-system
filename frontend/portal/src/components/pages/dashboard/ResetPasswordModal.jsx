import { useState } from "react";
import Modal from "../../ui/Modal.jsx";
import Button from "../../ui/Button.jsx";
import Alert from "../../ui/Alert.jsx";
import PasswordField from "../../ui/PasswordField.jsx";
import { resetStaffPassword } from "../../../api/admin.js";
import { readApiError } from "../../../api/auth.js";
import { resetPasswordSchema } from "../../../schemas/password.js";
import { validateWith } from "../../../schemas/validate.js";

/*
  An admin setting a new password for a doctor or receptionist who lost
  theirs. There is no email to send a reset link, so the admin passes the
  new password on themselves.
*/
function ResetPasswordModal({ staff, onClose, onDone }) {
  const [values, setValues] = useState({
    new_password: "",
    confirm_password: "",
  });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setValues((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: "" }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError("");

    const { valid, data, errors: found } = validateWith(
      resetPasswordSchema,
      values,
    );
    setErrors(found);
    if (!valid) return;

    setSaving(true);
    try {
      await resetStaffPassword(staff.id, data.new_password);
      onDone(`${staff.full_name}'s password was reset. Let them know the new one.`);
    } catch (error) {
      setFormError(readApiError(error));
      setSaving(false);
    }
  };

  return (
    <Modal
      title="Reset password"
      subtitle={`${staff.full_name} signs in with the new password from now on, and is signed out everywhere else.`}
      onClose={onClose}
      width="max-w-[460px]"
    >
      <form onSubmit={handleSubmit} noValidate>
        {formError && <Alert className="mb-5">{formError}</Alert>}

        <fieldset disabled={saving} className="space-y-5">
          <PasswordField
            id="reset-password"
            name="new_password"
            label="New password"
            placeholder="At least 8 characters"
            autoComplete="new-password"
            value={values.new_password}
            onChange={handleChange}
            error={errors.new_password}
          />
          <PasswordField
            id="reset-password-again"
            name="confirm_password"
            label="New password again"
            placeholder="Type it once more"
            autoComplete="new-password"
            value={values.confirm_password}
            onChange={handleChange}
            error={errors.confirm_password}
          />
        </fieldset>

        <div className="mt-7 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={saving}
            className="disabled:pointer-events-none disabled:opacity-70"
          >
            {saving ? "Resetting…" : "Reset password"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default ResetPasswordModal;
