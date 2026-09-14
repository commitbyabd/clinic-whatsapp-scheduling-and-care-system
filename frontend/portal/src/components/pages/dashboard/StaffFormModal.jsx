import { useState } from "react";
import { Mail, User, Stethoscope } from "lucide-react";
import Modal from "../../ui/Modal.jsx";
import Button from "../../ui/Button.jsx";
import Alert from "../../ui/Alert.jsx";
import TextField from "../../ui/TextField.jsx";
import IconBox from "../../ui/IconBox.jsx";
import PasswordField from "../../ui/PasswordField.jsx";
import {
  createDoctor,
  createReceptionist,
  updateDoctor,
  updateReceptionist,
} from "../../../api/admin.js";
import { readApiError } from "../../../api/auth.js";
import {
  doctorCreateSchema,
  doctorUpdateSchema,
  receptionistCreateSchema,
  receptionistUpdateSchema,
} from "../../../schemas/staff.js";
import { validateField, validateWith } from "../../../schemas/validate.js";

const SCHEMAS = {
  doctor: { create: doctorCreateSchema, update: doctorUpdateSchema },
  receptionist: {
    create: receptionistCreateSchema,
    update: receptionistUpdateSchema,
  },
};

/*
  One dialog for adding and editing staff, along two independent axes:
  'kind' picks doctor or receptionist, 'staff' picks edit or add. Pass a
  record to edit it, pass nothing to create one.

  Client-side rules exist only to spare a round trip. The server validates
  regardless, and a rejection surfaces through readApiError.
*/
function StaffFormModal({ staff = null, kind, onClose, onSaved }) {
  const isDoctor = kind === "doctor";
  const isCreate = staff === null;
  const noun = isDoctor ? "doctor" : "receptionist";
  const mode = isCreate ? "add" : "edit";

  const schema =
    SCHEMAS[isDoctor ? "doctor" : "receptionist"][
      isCreate ? "create" : "update"
    ];

  const [values, setValues] = useState({
    full_name: staff?.full_name ?? "",
    email: staff?.email ?? "",
    specialization: staff?.specialization ?? "",
    password: "",
  });
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  // Before the first submit a message is guidance; afterwards it is the
  // reason nothing happened.
  const [submitted, setSubmitted] = useState(false);
  const tone = submitted ? "error" : "hint";

  const handleChange = (event) => {
    const { name, value } = event.target;
    setValues((current) => ({ ...current, [name]: value }));
    setFieldErrors((current) => ({ ...current, [name]: "" }));
  };

  const handleBlur = (event) => {
    const { name, value } = event.target;
    setFieldErrors((current) => ({
      ...current,
      [name]: validateField(schema, name, value),
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError("");
    setSubmitted(true);

    // The parsed data is the payload: the schema has trimmed what needs
    // trimming and dropped every key it does not declare.
    const { valid, data: payload, errors } = validateWith(schema, values);
    setFieldErrors(errors);
    if (!valid) return;

    setSaving(true);
    try {
      let envelope;

      if (isCreate) {
        envelope = isDoctor
          ? await createDoctor(payload)
          : await createReceptionist(payload);
      } else {
        envelope = isDoctor
          ? await updateDoctor(staff.id, payload)
          : await updateReceptionist(staff.id, payload);
      }

      // The payload goes back with the message because the name in it is
      // the new one; the parent's copy still holds the name before the edit.
      onSaved(envelope.message, payload);
    } catch (error) {
      // A duplicate email arrives here as a 409 with a readable message.
      setFormError(readApiError(error));
      setSaving(false);
    }
  };

  return (
    <Modal
      title={`${isCreate ? "Add" : "Edit"} ${noun}`}
      subtitle={
        isCreate
          ? "They can sign in with these details straight away."
          : staff.full_name
      }
      onClose={onClose}
    >
      <form onSubmit={handleSubmit} noValidate>
        {formError && <Alert className="mb-5">{formError}</Alert>}

        <div className="space-y-5">
          <TextField
            id={`${mode}-full-name`}
            name="full_name"
            label="Full name"
            placeholder={isDoctor ? "Dr. Sara Khan" : "Sara Khan"}
            value={values.full_name}
            onChange={handleChange}
            onBlur={handleBlur}
            error={fieldErrors.full_name}
            tone={tone}
            disabled={saving}
            icon={
              <IconBox className="bg-lavender">
                <User className="size-4 text-violet" strokeWidth={2} />
              </IconBox>
            }
          />

          <TextField
            id={`${mode}-email`}
            name="email"
            type="email"
            label="Email address"
            placeholder="name@clinic.com"
            autoComplete="email"
            value={values.email}
            onChange={handleChange}
            onBlur={handleBlur}
            error={fieldErrors.email}
            tone={tone}
            disabled={saving}
            icon={
              <IconBox className="bg-lavender">
                <Mail className="size-4 text-violet" strokeWidth={2} />
              </IconBox>
            }
          />

          {isDoctor && (
            <TextField
              id={`${mode}-specialization`}
              name="specialization"
              label="Specialization"
              placeholder="Dermatology"
              value={values.specialization}
              onChange={handleChange}
              onBlur={handleBlur}
              error={fieldErrors.specialization}
              tone={tone}
              disabled={saving}
              icon={
                <IconBox className="bg-lavender">
                  <Stethoscope className="size-4 text-violet" strokeWidth={2} />
                </IconBox>
              }
            />
          )}

          {/* Only asked for at creation: there is no change-password
              endpoint, and PATCH ignores the field */}
          {isCreate && (
            <PasswordField
              id={`${mode}-password`}
              label="Password"
              placeholder="At least 8 characters"
              autoComplete="new-password"
              value={values.password}
              onChange={handleChange}
              onBlur={handleBlur}
              error={fieldErrors.password}
              tone={tone}
              disabled={saving}
            />
          )}
        </div>

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
            {isCreate
              ? saving
                ? "Adding…"
                : `Add ${noun}`
              : saving
                ? "Saving…"
                : "Save changes"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default StaffFormModal;
