import { CalendarDays, Stethoscope } from "lucide-react";
import Alert from "../../ui/Alert.jsx";
import IconBox from "../../ui/IconBox.jsx";
import SelectField from "../../ui/SelectField.jsx";
import TextField from "../../ui/TextField.jsx";
import { formatSlotTime } from "../../../utils/scheduling.js";

const MUTED = "mt-2 font-primary text-sm text-muted";

/*
  Which doctor, which day, and which of that doctor's free times. The times
  come from the server, worked out from the doctor's weekly hours minus
  what is already booked.
*/
function SlotPicker({
  doctors,
  doctorId,
  suggestedId,
  suggestedLabel = "(suggested)",
  onDoctor,
  date,
  minDate,
  onDate,
  slots,
  slot,
  onSlot,
  errors,
  tone,
}) {
  const doctorList = doctors.status === "ready" ? (doctors.data ?? []) : [];
  const times = slots.status === "ready" ? (slots.data?.slots ?? []) : [];

  const placeholder =
    doctors.status === "loading"
      ? "Loading doctors…"
      : doctorList.length > 0
        ? "Choose a doctor"
        : "No active doctors";

  return (
    <fieldset>
      <legend className="font-primary text-md-lg font-semibold text-plum">
        Doctor and time
      </legend>

      {doctors.status === "error" && (
        <Alert className="mt-3">{doctors.message}</Alert>
      )}

      <div className="mt-3 grid gap-4 sm:grid-cols-2">
        <SelectField
          id="schedule-doctor"
          label="Doctor"
          value={doctorId}
          onChange={(event) => onDoctor(event.target.value)}
          error={errors.doctor}
          tone={tone}
          icon={
            <IconBox className="bg-lavender">
              <Stethoscope className="size-4 text-violet" strokeWidth={2} />
            </IconBox>
          }
        >
          <option value="" disabled>
            {placeholder}
          </option>
          {doctorList.map((doctor) => (
            <option key={doctor.id} value={doctor.id}>
              {doctor.full_name}
              {doctor.specialization ? ` · ${doctor.specialization}` : ""}
              {doctor.id === suggestedId ? ` ${suggestedLabel}` : ""}
            </option>
          ))}
        </SelectField>

        <TextField
          id="schedule-date"
          type="date"
          label="Date"
          min={minDate}
          value={date}
          onChange={(event) => onDate(event.target.value)}
          icon={
            <IconBox className="bg-lavender">
              <CalendarDays className="size-4 text-violet" strokeWidth={2} />
            </IconBox>
          }
        />
      </div>

      <div className="mt-5">
        <p
          id="schedule-times"
          className="font-primary text-sm font-semibold text-plum"
        >
          Free times
        </p>

        {slots.status === "idle" && (
          <p className={MUTED}>Choose a doctor and a date to see free times.</p>
        )}
        {slots.status === "loading" && (
          <p className={MUTED}>Loading free times…</p>
        )}
        {slots.status === "error" && (
          <Alert className="mt-2">{slots.message}</Alert>
        )}
        {/* the server says why: no hours set, a day off, or fully booked */}
        {slots.status === "ready" && times.length === 0 && (
          <p className={MUTED}>{slots.message}</p>
        )}

        {times.length > 0 && (
          <div
            role="group"
            aria-labelledby="schedule-times"
            className="mt-2 grid grid-cols-3 gap-2 sm:grid-cols-4"
          >
            {times.map((iso) => {
              const selected = iso === slot;
              return (
                <button
                  key={iso}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => onSlot(iso)}
                  className={`h-10 rounded-md border font-primary text-sm font-semibold transition duration-200 focus-visible:ring-4 focus-visible:ring-violet/22 focus-visible:outline-none ${
                    selected
                      ? "border-violet bg-violet text-white"
                      : "border-border bg-white text-plum hover:bg-pale-lavender"
                  }`}
                >
                  {formatSlotTime(iso)}
                </button>
              );
            })}
          </div>
        )}

        {errors.slot && (
          <p role="alert" className="mt-2 font-primary text-sm text-error">
            {errors.slot}
          </p>
        )}
      </div>
    </fieldset>
  );
}

export default SlotPicker;
