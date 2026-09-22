import { useState } from "react";
import Modal from "../../ui/Modal.jsx";
import Button from "../../ui/Button.jsx";
import Alert from "../../ui/Alert.jsx";
import PasswordField from "../../ui/PasswordField.jsx";
import { changePassword, readApiError } from "../../../api/auth.js";
import { changePasswordSchema } from "../../../schemas/password.js";
import { validateWith } from "../../../schemas/validate.js";

const EMPTY = { current_password: "", new_password: "", confirm_password: "" };

/*
  A signed-in user changing their own password. The server ends every
  session from before the change, this one included, so the new token it
  sends back is handed to onChanged to keep the user signed in here.
*/
function ChangePasswordModal({ onClose, onChanged }) {
  const [values, setValues] = useState(EMPTY);
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
      changePasswordSchema,
      values,
    );
    setErrors(found);
    if (!valid) return;

    setSaving(true);
    try {
      const envelope = await changePassword(data);
      onChanged(envelope.data.access_token);
    } catch (error) {
      // a wrong current password comes back as a 400 with a readable message
      setFormError(readApiError(error));
      setSaving(false);
    }
  };

  return (
    <Modal
      title="Change password"
      subtitle="Anywhere else you are signed in will be signed out."
      onClose={onClose}
      width="max-w-[460px]"
    >
      <form onSubmit={handleSubmit} noValidate>
        {formError && <Alert className="mb-5">{formError}</Alert>}

        <fieldset disabled={saving} className="space-y-5">
          <PasswordField
            id="current-password"
            name="current_password"
            label="Current password"
            placeholder="Your current password"
            autoComplete="current-password"
            value={values.current_password}
            onChange={handleChange}
            error={errors.current_password}
          />
          <PasswordField
            id="new-password"
            name="new_password"
            label="New password"
            placeholder="At least 8 characters"
            autoComplete="new-password"
            value={values.new_password}
            onChange={handleChange}
            error={errors.new_password}
          />
          <PasswordField
            id="confirm-password"
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
            {saving ? "Changing…" : "Change password"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default ChangePasswordModal;
