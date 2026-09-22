import { useState } from "react";
import Alert from "../../ui/Alert.jsx";
import Button from "../../ui/Button.jsx";
import Modal from "../../ui/Modal.jsx";
import SlotPicker from "./SlotPicker.jsx";
import {
  listDoctors,
  listFreeSlots,
  rescheduleAppointment,
} from "../../../api/receptionist.js";
import { readApiError } from "../../../api/auth.js";
import { useApiResource } from "../../../hooks/useApiResource.js";
import {
  clinicDay,
  formatAppointment,
  todayInClinic,
} from "../../../utils/scheduling.js";

/*
  Moves a booked visit to another free time, with the same doctor or a
  different one. It starts on the visit's own doctor and day; that day's
  list leaves out the visit's current time, which is taken by the visit
  itself.
*/
function RescheduleModal({ appointment, onClose, onMoved }) {
  const [today] = useState(todayInClinic);
  const doctors = useApiResource("doctors", listDoctors);
  const doctorList = doctors.status === "ready" ? (doctors.data ?? []) : [];

  const [doctorId, setDoctorId] = useState(appointment.doctor.id ?? "");
  const [date, setDate] = useState(() => {
    const day = clinicDay(appointment.scheduled_for);
    return day && day >= today ? day : today;
  });
  const [slot, setSlot] = useState("");
  // bumped to fetch the free times again after a clash
  const [slotsRound, setSlotsRound] = useState(0);
  const slots = useApiResource(
    doctorId && date ? `slots:${doctorId}:${date}:${slotsRound}` : null,
    () => listFreeSlots(doctorId, date),
  );

  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  // a time belongs to one doctor on one day, so changing either drops it
  const chooseDoctor = (id) => {
    setDoctorId(id);
    setSlot("");
    setErrors((current) => ({ ...current, doctor: "" }));
  };

  const chooseDate = (value) => {
    setDate(value);
    setSlot("");
  };

  const chooseSlot = (iso) => {
    setSlot(iso);
    setErrors((current) => ({ ...current, slot: "" }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError("");

    const found = {};
    if (!doctorId) found.doctor = "Choose a doctor.";
    if (!slot) found.slot = "Choose one of the free times.";
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    setSaving(true);
    try {
      await rescheduleAppointment(appointment.id, {
        doctor_id: doctorId,
        starts_at: slot,
      });
      onMoved({
        patientName: appointment.patient.full_name ?? "The patient",
        doctorName:
          doctorList.find((d) => d.id === doctorId)?.full_name ?? "the doctor",
        startsAt: slot,
      });
    } catch (error) {
      setFormError(readApiError(error));
      setSaving(false);

      // someone else took the time meanwhile, so show what is free now
      if (error?.response?.data?.error_code === "SLOT_NOT_FREE") {
        setSlot("");
        setSlotsRound((round) => round + 1);
      }
    }
  };

  return (
    <Modal
      title={`Move ${appointment.patient.full_name ?? "this visit"}`}
      subtitle={`Now: ${formatAppointment(appointment.scheduled_for)} with ${appointment.doctor.full_name ?? "a doctor"}`}
      onClose={onClose}
      width="max-w-[640px]"
    >
      <form onSubmit={handleSubmit} noValidate>
        {formError && <Alert className="mb-5">{formError}</Alert>}

        <fieldset disabled={saving}>
          <SlotPicker
            doctors={doctors}
            doctorId={doctorId}
            suggestedId=""
            onDoctor={chooseDoctor}
            date={date}
            minDate={today}
            onDate={chooseDate}
            slots={slots}
            slot={slot}
            onSlot={chooseSlot}
            errors={errors}
            tone="error"
          />
        </fieldset>

        <p className="mt-6 font-primary text-sm leading-body text-muted">
          WhatsApp does not tell the patient yet, so let them know the new
          time.
        </p>

        <div className="mt-5 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={saving}>
            Keep it
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={saving}
            className="disabled:pointer-events-none disabled:opacity-70"
          >
            {saving ? "Moving…" : "Move appointment"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default RescheduleModal;
