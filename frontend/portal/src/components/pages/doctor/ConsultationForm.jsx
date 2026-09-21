import { Plus, Trash2 } from "lucide-react";
import Button from "../../ui/Button.jsx";
import SmallField from "../../ui/SmallField.jsx";
import TextArea from "../../ui/TextArea.jsx";
import TextField from "../../ui/TextField.jsx";

// the server's limit
const MAX_MEDICINES = 20;

function PrescriptionRows({ rows, errors, tone, onRowChange, onAddRow, onRemoveRow }) {
  return (
    <fieldset>
      <legend className="block font-primary text-sm font-semibold text-plum">
        Prescriptions
      </legend>

      {rows.length === 0 && (
        <p className="mt-2 font-primary text-sm text-muted">
          No medicines added.
        </p>
      )}

      <div className="mt-2 space-y-3">
        {rows.map((row, index) => {
          // rows can be removed, so the index is what ties a row to its errors
          const field = (name) => ({
            id: `rx-${index}-${name}`,
            value: row[name],
            onChange: (event) => onRowChange(index, name, event.target.value),
            error: errors[`prescriptions.${index}.${name}`],
            tone,
          });

          return (
            <div
              key={index}
              className="rounded-md border border-border bg-white p-3"
            >
              <div className="grid gap-3 sm:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)_5rem_auto] sm:items-start">
                <SmallField label="Medicine" placeholder="Paracetamol" {...field("medicine")} />
                <SmallField label="Dose" placeholder="500 mg" {...field("dose")} />
                <SmallField label="How often" placeholder="Twice a day" {...field("frequency")} />
                <SmallField label="Days" inputMode="numeric" placeholder="5" {...field("days")} />
                <button
                  type="button"
                  onClick={() => onRemoveRow(index)}
                  aria-label={`Remove medicine ${index + 1}`}
                  className="grid size-10 place-items-center self-end rounded-md text-muted transition duration-200 hover:bg-error-bg hover:text-error focus-visible:ring-2 focus-visible:ring-error/30 focus-visible:outline-none"
                >
                  <Trash2 className="size-4" strokeWidth={2} />
                </button>
              </div>
              <SmallField
                label="Instructions"
                placeholder="After meals"
                className="mt-3"
                {...field("instructions")}
              />
            </div>
          );
        })}
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={onAddRow}
        disabled={rows.length >= MAX_MEDICINES}
        leadingIcon={<Plus className="size-4" strokeWidth={2} />}
        className="mt-3 disabled:pointer-events-none disabled:opacity-60"
      >
        Add medicine
      </Button>
    </fieldset>
  );
}

/*
  The write-up of one visit. Presentation only: ConsultationModal owns the
  values, the errors and saving. Vitals use the units the server checks:
  °F for temperature, kg for weight.
*/
function ConsultationForm({
  values,
  errors,
  tone,
  onChange,
  onBlur,
  onRowChange,
  onAddRow,
  onRemoveRow,
}) {
  const field = (name) => ({
    id: `consult-${name}`,
    name,
    value: values[name],
    onChange,
    onBlur,
    error: errors[name],
    tone,
  });

  return (
    <section aria-labelledby="visit-consultation">
      <h3
        id="visit-consultation"
        className="font-primary text-md-lg font-semibold text-plum"
      >
        Consultation
      </h3>

      <div className="mt-3 space-y-5">
        <TextArea label="Diagnosis" rows={2} {...field("diagnosis")} />

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <TextField label="Blood pressure" placeholder="120/80" {...field("bp")} />
          <TextField
            label="Pulse (bpm)"
            inputMode="numeric"
            placeholder="72"
            {...field("pulse")}
          />
          <TextField
            label="Temperature (°F)"
            inputMode="decimal"
            placeholder="98.6"
            {...field("temperature")}
          />
          <TextField
            label="Weight (kg)"
            inputMode="decimal"
            placeholder="70"
            {...field("weight")}
          />
        </div>

        <PrescriptionRows
          rows={values.prescriptions}
          errors={errors}
          tone={tone}
          onRowChange={onRowChange}
          onAddRow={onAddRow}
          onRemoveRow={onRemoveRow}
        />

        <TextField
          type="date"
          label="Follow-up on (optional)"
          className="sm:max-w-xs"
          {...field("follow_up_on")}
        />

        <TextArea label="Notes" rows={4} {...field("doctor_notes")} />
      </div>
    </section>
  );
}

export default ConsultationForm;
