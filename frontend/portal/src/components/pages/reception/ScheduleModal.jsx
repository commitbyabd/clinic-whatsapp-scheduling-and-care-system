import { useState } from "react";
import Alert from "../../ui/Alert.jsx";
import Button from "../../ui/Button.jsx";
import Modal from "../../ui/Modal.jsx";
import PatientPicker from "./PatientPicker.jsx";
import SlotPicker from "./SlotPicker.jsx";
import {
  listDoctors,
  listFreeSlots,
  listMatchingPatients,
  scheduleBookingRequest,
} from "../../../api/receptionist.js";
import { readApiError } from "../../../api/auth.js";
import { useApiResource } from "../../../hooks/useApiResource.js";
import { newPatientSchema } from "../../../schemas/scheduling.js";
import { validateField, validateWith } from "../../../schemas/validate.js";
import { askedForLabel, patientLabel } from "../../../utils/bookingRequest.js";
import {
  NEW_PATIENT,
  defaultPatientChoice,
  matchingSlot,
  pickedDoctorId,
  startingDay,
  suggestedDoctorId,
  todayInClinic,
} from "../../../utils/scheduling.js";

/*
  Turns one booking request into an appointment: who it is for, which
  doctor, and which of that doctor's free times.

  Patient, doctor and time start on a best guess (the name the patient
  gave, the doctor and open time they picked on WhatsApp, else the
  department the model suggested) until the receptionist picks one. The
  guesses are worked out on every render rather than copied into state, so
  they fill in by themselves once the lists arrive.
*/
function ScheduleModal({ request, onClose, onScheduled }) {
  const [today] = useState(todayInClinic);

  const doctors = useApiResource("doctors", listDoctors);
  const matches = useApiResource(`patients:${request.id}`, () =>
    listMatchingPatients(request.id),
  );

  const doctorList = doctors.status === "ready" ? (doctors.data ?? []) : [];
  const patientList = matches.status === "ready" ? (matches.data ?? []) : [];

  // the doctor the patient picked on WhatsApp comes first; the department
  // the model suggested is the fallback
  const askedId = pickedDoctorId(doctorList, request.requested_doctor_id);
  const suggestedId =
    askedId || suggestedDoctorId(doctorList, request.suggested_specialization);

  // null until the receptionist picks, so the guess shows in the meantime
  const [patientPick, setPatientPick] = useState(null);
  const [doctorPick, setDoctorPick] = useState(null);
  const patientChoice =
    patientPick ??
    (matches.status === "ready"
      ? defaultPatientChoice(request, patientList)
      : "");
  const doctorId = doctorPick ?? suggestedId;

  const [date, setDate] = useState(() =>
    startingDay(request.requested_slot, today),
  );
  // null until the receptionist picks, so the time they asked for shows
  // once the free ones arrive, and "" after a clash
  const [slotPick, setSlotPick] = useState(null);
  // bumped to fetch the free times again after a clash
  const [slotsRound, setSlotsRound] = useState(0);
  const slots = useApiResource(
    doctorId && date ? `slots:${doctorId}:${date}:${slotsRound}` : null,
    () => listFreeSlots(doctorId, date),
  );

  const freeSlots = slots.status === "ready" ? (slots.data?.slots ?? []) : [];
  const slot = slotPick ?? matchingSlot(freeSlots, request.requested_slot);

  const [values, setValues] = useState({
    full_name: request.patient_name ?? "",
    date_of_birth: "",
    gender: "",
  });
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  // Before the first submit a message is guidance; afterwards it is the
  // reason nothing happened.
  const [submitted, setSubmitted] = useState(false);
  const tone = submitted ? "error" : "hint";

  const clearError = (name) =>
    setFieldErrors((current) => ({ ...current, [name]: "" }));

  const choosePatient = (id) => {
    setPatientPick(id);
    clearError("patient");
  };

  // a time belongs to one doctor on one day, so changing either drops it
  const chooseDoctor = (id) => {
    setDoctorPick(id);
    setSlotPick("");
    clearError("doctor");
  };

  const chooseDate = (value) => {
    setDate(value);
    setSlotPick("");
  };

  const chooseSlot = (iso) => {
    setSlotPick(iso);
    clearError("slot");
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setValues((current) => ({ ...current, [name]: value }));
    clearError(name);
  };

  const handleBlur = (event) => {
    const { name, value } = event.target;
    setFieldErrors((current) => ({
      ...current,
      [name]: validateField(newPatientSchema, name, value),
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError("");
    setSubmitted(true);

    const errors = {};
    let patient = null;

    if (patientChoice === NEW_PATIENT) {
      // the parsed data is the payload: trimmed, with blanks sent as null
      const result = validateWith(newPatientSchema, values);
      Object.assign(errors, result.errors);
      if (result.valid) patient = { new_patient: result.data };
    } else if (patientChoice) {
      patient = { patient_id: patientChoice };
    } else {
      errors.patient = "Choose the patient, or add them as new.";
    }

    if (!doctorId) errors.doctor = "Choose a doctor.";
    if (!slot) errors.slot = "Choose one of the free times.";

    setFieldErrors(errors);
    if (!patient || !doctorId || !slot) return;

    setSaving(true);
    try {
      await scheduleBookingRequest(request.id, {
        doctor_id: doctorId,
        starts_at: slot,
        ...patient,
      });

      onScheduled({
        patientName:
          patient.new_patient?.full_name ??
          patientList.find((p) => p.id === patientChoice)?.full_name ??
          patientLabel(request),
        doctorName:
          doctorList.find((d) => d.id === doctorId)?.full_name ?? "the doctor",
        startsAt: slot,
      });
    } catch (error) {
      setFormError(readApiError(error));
      setSaving(false);

      // someone else took the time meanwhile, so show what is free now
      if (error?.response?.data?.error_code === "SLOT_NOT_FREE") {
        setSlotPick("");
        setSlotsRound((round) => round + 1);
      }
    }
  };

  return (
    <Modal
      title={`Schedule ${patientLabel(request)}`}
      subtitle={askedForLabel(request)}
      onClose={onClose}
      width="max-w-[640px]"
    >
      <form onSubmit={handleSubmit} noValidate>
        {formError && <Alert className="mb-5">{formError}</Alert>}

        {/* disabled while saving, so nothing changes under the request */}
        <fieldset disabled={saving} className="space-y-7">
          <PatientPicker
            number={request.whatsapp_number}
            matches={matches}
            choice={patientChoice}
            onChoose={choosePatient}
            values={values}
            onChange={handleChange}
            onBlur={handleBlur}
            errors={fieldErrors}
            tone={tone}
          />

          <SlotPicker
            doctors={doctors}
            doctorId={doctorId}
            suggestedId={suggestedId}
            suggestedLabel={askedId ? "(asked for)" : "(suggested)"}
            onDoctor={chooseDoctor}
            date={date}
            minDate={today}
            onDate={chooseDate}
            slots={slots}
            slot={slot}
            onSlot={chooseSlot}
            errors={fieldErrors}
            tone={tone}
          />
        </fieldset>

        <p className="mt-6 font-primary text-sm leading-body text-muted">
          WhatsApp does not tell the patient yet, so let them know the time once
          it is booked.
        </p>

        <div className="mt-5 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={saving}>
            Cancel
          </Button>

          <Button
            type="submit"
            variant="primary"
            disabled={saving}
            className="disabled:pointer-events-none disabled:opacity-70"
          >
            {saving ? "Booking…" : "Book appointment"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default ScheduleModal;
