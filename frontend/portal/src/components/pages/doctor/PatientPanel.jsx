import { useState } from "react";
import { Pencil } from "lucide-react";
import Alert from "../../ui/Alert.jsx";
import Button from "../../ui/Button.jsx";
import SelectField from "../../ui/SelectField.jsx";
import TextField from "../../ui/TextField.jsx";
import { saveMedicalDetails } from "../../../api/doctor.js";
import { readApiError } from "../../../api/auth.js";
import { BLOOD_GROUPS, medicalSchema } from "../../../schemas/consultation.js";
import { patientFacts } from "../../../utils/appointments.js";
import { joinList, parseList } from "../../../utils/consultation.js";

function Fact({ label, items, empty, warn = false }) {
  return (
    <div>
      <dt className="font-primary text-xs font-semibold tracking-[0.08em] text-muted uppercase">
        {label}
      </dt>
      <dd className="mt-1.5 flex flex-wrap gap-1.5">
        {items.length === 0 && (
          <span className="font-primary text-sm text-muted">{empty}</span>
        )}
        {items.map((item) => (
          <span
            key={item}
            className={`rounded-pill px-2.5 py-0.5 font-primary text-sm font-medium ${
              warn ? "bg-error-bg text-error" : "bg-lavender text-plum"
            }`}
          >
            {item}
          </span>
        ))}
      </dd>
    </div>
  );
}

/*
  Who the patient is, and the medical details only a doctor may change:
  allergies, long-term conditions and blood group. Those save on their own,
  apart from the consultation, since they belong to the patient rather
  than to this visit.
*/
function PatientPanel({ patient, onSaved }) {
  const [medical, setMedical] = useState({
    allergies: patient.allergies ?? [],
    chronic_conditions: patient.chronic_conditions ?? [],
    blood_group: patient.blood_group ?? null,
  });
  const [values, setValues] = useState(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const editing = values !== null;

  const startEditing = () => {
    setValues({
      allergies: joinList(medical.allergies),
      chronic_conditions: joinList(medical.chronic_conditions),
      blood_group: medical.blood_group ?? "",
    });
    setError("");
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setValues((current) => ({ ...current, [name]: value }));
  };

  const save = async () => {
    const parsed = medicalSchema.safeParse({
      allergies: parseList(values.allergies),
      chronic_conditions: parseList(values.chronic_conditions),
      blood_group: values.blood_group,
    });
    if (!parsed.success) {
      setError(parsed.error.issues[0].message);
      return;
    }

    setSaving(true);
    setError("");
    try {
      const envelope = await saveMedicalDetails(patient.id, parsed.data);
      setMedical({
        allergies: envelope.data.allergies ?? [],
        chronic_conditions: envelope.data.chronic_conditions ?? [],
        blood_group: envelope.data.blood_group ?? null,
      });
      setValues(null);
      onSaved("Medical details saved.");
    } catch (failure) {
      setError(readApiError(failure));
    } finally {
      setSaving(false);
    }
  };

  const facts = [patientFacts(patient), patient.whatsapp_number]
    .filter(Boolean)
    .join(" · ");

  return (
    <section aria-labelledby="visit-patient">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3
          id="visit-patient"
          className="font-primary text-md-lg font-semibold text-plum"
        >
          Patient
        </h3>
        {/* a visit whose patient record is missing has nothing to edit */}
        {!editing && patient.id && (
          <Button
            variant="outline"
            size="sm"
            onClick={startEditing}
            leadingIcon={<Pencil className="size-4" strokeWidth={2} />}
          >
            Edit medical details
          </Button>
        )}
      </div>
      {facts && (
        <p className="mt-1 font-primary text-sm text-muted">{facts}</p>
      )}

      {!editing && (
        <dl className="mt-4 grid gap-4 sm:grid-cols-3">
          <Fact
            label="Allergies"
            items={medical.allergies}
            empty="None recorded"
            warn
          />
          <Fact
            label="Long-term conditions"
            items={medical.chronic_conditions}
            empty="None recorded"
          />
          <Fact
            label="Blood group"
            items={medical.blood_group ? [medical.blood_group] : []}
            empty="Not recorded"
          />
        </dl>
      )}

      {editing && (
        <fieldset disabled={saving} className="mt-4 grid gap-4 sm:grid-cols-3">
          <TextField
            id="medical-allergies"
            name="allergies"
            label="Allergies"
            placeholder="Penicillin, peanuts"
            className="sm:col-span-3"
            value={values.allergies}
            onChange={handleChange}
          />
          <TextField
            id="medical-conditions"
            name="chronic_conditions"
            label="Long-term conditions"
            placeholder="Asthma, diabetes"
            className="sm:col-span-2"
            value={values.chronic_conditions}
            onChange={handleChange}
          />
          <SelectField
            id="medical-blood-group"
            name="blood_group"
            label="Blood group"
            value={values.blood_group}
            onChange={handleChange}
          >
            <option value="">Not recorded</option>
            {BLOOD_GROUPS.map((group) => (
              <option key={group} value={group}>
                {group}
              </option>
            ))}
          </SelectField>

          <p className="font-primary text-sm text-muted sm:col-span-3">
            Separate items with commas.
          </p>
          {error && <Alert className="sm:col-span-3">{error}</Alert>}

          <div className="flex justify-end gap-2 sm:col-span-3">
            <Button variant="outline" onClick={() => setValues(null)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={save}
              className="disabled:pointer-events-none disabled:opacity-70"
            >
              {saving ? "Saving…" : "Save details"}
            </Button>
          </div>
        </fieldset>
      )}
    </section>
  );
}

export default PatientPanel;
