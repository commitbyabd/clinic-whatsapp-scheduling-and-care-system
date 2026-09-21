import { User } from "lucide-react";
import Alert from "../../ui/Alert.jsx";
import IconBox from "../../ui/IconBox.jsx";
import SelectField from "../../ui/SelectField.jsx";
import TextField from "../../ui/TextField.jsx";
import {
  NEW_PATIENT,
  formatBirthDate,
  todayInClinic,
} from "../../../utils/scheduling.js";

const GENDERS = { female: "Female", male: "Male", other: "Other" };

const OPTION =
  "flex cursor-pointer items-center gap-3 rounded-md border border-border bg-white px-4 py-3 transition duration-200 hover:bg-pale-lavender has-checked:border-violet has-checked:bg-pale-lavender has-focus-visible:ring-4 has-focus-visible:ring-violet/22";

// what tells family members on one phone apart
function describe(patient) {
  const parts = [];
  if (patient.date_of_birth) {
    parts.push(`Born ${formatBirthDate(patient.date_of_birth)}`);
  }
  if (patient.gender) parts.push(GENDERS[patient.gender] ?? patient.gender);
  return parts.join(" · ") || "No date of birth on record";
}

function Choice({ checked, onChange, title, detail }) {
  return (
    <label className={OPTION}>
      <input
        type="radio"
        name="patient"
        checked={checked}
        onChange={onChange}
        className="size-4 shrink-0 accent-violet"
      />
      <span className="min-w-0">
        <span className="block font-primary text-md font-semibold text-plum">
          {title}
        </span>
        <span className="block font-primary text-sm text-muted">{detail}</span>
      </span>
    </label>
  );
}

/*
  Who the appointment is for: one of the patients already registered under
  the request's number (a family can share one phone), or a new record.
  The details of a new record are asked for only when it is chosen.
*/
function PatientPicker({
  number,
  matches,
  choice,
  onChoose,
  values,
  onChange,
  onBlur,
  errors,
  tone,
}) {
  const patients = matches.status === "ready" ? (matches.data ?? []) : [];

  return (
    <fieldset>
      <legend className="font-primary text-md-lg font-semibold text-plum">
        Patient
      </legend>
      <p className="mt-1 font-primary text-sm text-muted">
        {number ? `Registered under ${number}` : "This request has no number"}
      </p>

      {matches.status === "error" && (
        <Alert className="mt-3">{matches.message}</Alert>
      )}

      {matches.status === "loading" && (
        <p className="mt-3 font-primary text-sm text-muted">
          Looking up patients…
        </p>
      )}

      {matches.status === "ready" && (
        <div className="mt-3 space-y-2">
          {patients.map((patient) => (
            <Choice
              key={patient.id}
              checked={choice === patient.id}
              onChange={() => onChoose(patient.id)}
              title={patient.full_name}
              detail={describe(patient)}
            />
          ))}

          <Choice
            checked={choice === NEW_PATIENT}
            onChange={() => onChoose(NEW_PATIENT)}
            title="New patient"
            detail="Adds a record under this number"
          />
        </div>
      )}

      {errors.patient && (
        <p role="alert" className="mt-2 font-primary text-sm text-error">
          {errors.patient}
        </p>
      )}

      {choice === NEW_PATIENT && (
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <TextField
            id="schedule-full-name"
            name="full_name"
            label="Full name"
            placeholder="Ayesha Khan"
            className="sm:col-span-2"
            value={values.full_name}
            onChange={onChange}
            onBlur={onBlur}
            error={errors.full_name}
            tone={tone}
            icon={
              <IconBox className="bg-lavender">
                <User className="size-4 text-violet" strokeWidth={2} />
              </IconBox>
            }
          />

          <TextField
            id="schedule-date-of-birth"
            name="date_of_birth"
            type="date"
            label="Date of birth (optional)"
            max={todayInClinic()}
            value={values.date_of_birth}
            onChange={onChange}
            onBlur={onBlur}
            error={errors.date_of_birth}
            tone={tone}
          />

          <SelectField
            id="schedule-gender"
            name="gender"
            label="Gender (optional)"
            value={values.gender}
            onChange={onChange}
            onBlur={onBlur}
            error={errors.gender}
            tone={tone}
          >
            <option value="">Not given</option>
            {Object.entries(GENDERS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </SelectField>
        </div>
      )}
    </fieldset>
  );
}

export default PatientPicker;
