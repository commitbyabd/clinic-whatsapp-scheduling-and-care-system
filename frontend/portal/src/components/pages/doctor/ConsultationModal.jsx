import { useState } from "react";
import { MessageSquareText } from "lucide-react";
import Alert from "../../ui/Alert.jsx";
import Button from "../../ui/Button.jsx";
import Modal from "../../ui/Modal.jsx";
import ConsultationForm from "./ConsultationForm.jsx";
import PatientPanel from "./PatientPanel.jsx";
import VisitHistory from "./VisitHistory.jsx";
import { saveConsultation, setAppointmentStatus } from "../../../api/doctor.js";
import { readApiError } from "../../../api/auth.js";
import { consultationSchema } from "../../../schemas/consultation.js";
import { validateField, validateWithPaths } from "../../../schemas/validate.js";
import {
  canWriteUp,
  isOpenVisit,
  statusLabel,
} from "../../../utils/appointments.js";
import { reasonLabel } from "../../../utils/bookingRequest.js";
import {
  consultationForm,
  consultationPayload,
  emptyPrescription,
} from "../../../utils/consultation.js";
import {
  clinicDay,
  formatAppointment,
  todayInClinic,
} from "../../../utils/scheduling.js";

const DISABLED = "disabled:pointer-events-none disabled:opacity-70";

/*
  One visit: who the patient is, what brought them, their past visits, and
  the doctor's write-up, with how the visit went.

  onSaved   the write-up or medical details were saved; the dialog stays
  onDone    the visit's status changed; the dialog closes
*/
function ConsultationModal({ appointment, onClose, onSaved, onDone }) {
  const { status } = appointment;
  const open = isOpenVisit(status);
  const writable = canWriteUp(status);
  // completed and no-show describe a visit that has had its day
  const [markable] = useState(
    () => clinicDay(appointment.scheduled_for) <= todayInClinic(),
  );

  const [values, setValues] = useState(() => consultationForm(appointment));
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [busy, setBusy] = useState(null);
  const [confirmingNoShow, setConfirmingNoShow] = useState(false);

  // Before the first save a message is guidance; afterwards it is the
  // reason nothing happened.
  const [submitted, setSubmitted] = useState(false);
  const tone = submitted ? "error" : "hint";

  const handleChange = (event) => {
    const { name, value } = event.target;
    setValues((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: "" }));
  };

  const handleBlur = (event) => {
    const { name, value } = event.target;
    setErrors((current) => ({
      ...current,
      [name]: validateField(consultationSchema, name, value),
    }));
  };

  const changeRow = (index, name, value) => {
    setValues((current) => ({
      ...current,
      prescriptions: current.prescriptions.map((row, i) =>
        i === index ? { ...row, [name]: value } : row,
      ),
    }));
    setErrors((current) => ({
      ...current,
      [`prescriptions.${index}.${name}`]: "",
    }));
  };

  const addRow = () =>
    setValues((current) => ({
      ...current,
      prescriptions: [...current.prescriptions, emptyPrescription()],
    }));

  const removeRow = (index) => {
    setValues((current) => ({
      ...current,
      prescriptions: current.prescriptions.filter((_, i) => i !== index),
    }));
    // the rows below move up, so their errors no longer line up
    setErrors((current) =>
      Object.fromEntries(
        Object.entries(current).filter(
          ([key]) => !key.startsWith("prescriptions."),
        ),
      ),
    );
  };

  // the parsed write-up, or null with the errors shown
  const validated = () => {
    setSubmitted(true);
    const result = validateWithPaths(consultationSchema, values);
    setErrors(result.errors);
    return result.valid ? consultationPayload(result.data) : null;
  };

  const run = async (action, work) => {
    setBusy(action);
    setFormError("");
    try {
      await work();
    } catch (error) {
      setFormError(readApiError(error));
    } finally {
      setBusy(null);
    }
  };

  const save = () => {
    const payload = validated();
    if (!payload) return;
    run("save", async () => {
      await saveConsultation(appointment.id, payload);
      onSaved("Consultation saved.");
    });
  };

  // Saved first, so the write-up is kept even if marking the visit fails.
  const complete = () => {
    const payload = validated();
    if (!payload) return;
    run("complete", async () => {
      await saveConsultation(appointment.id, payload);
      await setAppointmentStatus(appointment.id, "completed");
      onDone("Visit completed.");
    });
  };

  const markNoShow = () =>
    run("no_show", async () => {
      await setAppointmentStatus(appointment.id, "no_show");
      onDone("Visit marked as a no-show.");
    });

  const reopen = () =>
    run("reopen", async () => {
      await setAppointmentStatus(appointment.id, "booked");
      onDone("Visit reopened.");
    });

  const working = busy !== null;
  const patient = appointment.patient ?? {};

  return (
    <Modal
      title={patient.full_name ?? "Patient record missing"}
      subtitle={`${formatAppointment(appointment.scheduled_for)} · ${appointment.duration_minutes} min · ${statusLabel(status)}`}
      onClose={onClose}
      width="max-w-[880px]"
    >
      {formError && <Alert className="mb-5">{formError}</Alert>}

      <div className="space-y-7">
        <PatientPanel patient={patient} onSaved={onSaved} />

        <section aria-labelledby="visit-reason">
          <h3
            id="visit-reason"
            className="font-primary text-md-lg font-semibold text-plum"
          >
            Reason for visit
          </h3>
          <p className="mt-1 font-primary text-sm text-ink">
            {reasonLabel(appointment.reason)}
          </p>
          {/* the patient's own words from the WhatsApp booking */}
          {appointment.symptom_summary && (
            <p className="mt-2 flex items-start gap-2 font-primary text-sm leading-body text-ink">
              <MessageSquareText
                className="mt-0.5 size-4 shrink-0 text-violet"
                strokeWidth={2}
              />
              <span>“{appointment.symptom_summary}”</span>
            </p>
          )}
        </section>

        <VisitHistory visits={appointment.patient_history ?? []} />

        {writable ? (
          <fieldset disabled={working}>
            <ConsultationForm
              values={values}
              errors={errors}
              tone={tone}
              onChange={handleChange}
              onBlur={handleBlur}
              onRowChange={changeRow}
              onAddRow={addRow}
              onRemoveRow={removeRow}
            />
          </fieldset>
        ) : (
          <p className="rounded-md bg-pale-lavender px-4 py-3 font-primary text-sm leading-body text-ink">
            {status === "no_show"
              ? "The patient did not come, so there is nothing to write up. Undo the no-show if they did."
              : "This visit was cancelled, so there is nothing to write up."}
          </p>
        )}
      </div>

      <div className="mt-8 flex flex-col-reverse gap-3 border-t border-border pt-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          {open && markable && !confirmingNoShow && (
            <Button
              variant="danger"
              onClick={() => setConfirmingNoShow(true)}
              disabled={working}
              className={DISABLED}
            >
              Mark as no-show
            </Button>
          )}

          {confirmingNoShow && (
            <>
              <p className="font-primary text-sm text-ink">
                The patient did not come?
              </p>
              <Button
                variant="outline"
                onClick={() => setConfirmingNoShow(false)}
                disabled={working}
                className={DISABLED}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={markNoShow}
                disabled={working}
                className={DISABLED}
              >
                {busy === "no_show" ? "Saving…" : "Yes, a no-show"}
              </Button>
            </>
          )}

          {(status === "completed" || status === "no_show") && (
            <Button
              variant="outline"
              onClick={reopen}
              disabled={working}
              className={DISABLED}
            >
              {busy === "reopen"
                ? "Reopening…"
                : status === "no_show"
                  ? "Undo no-show"
                  : "Reopen visit"}
            </Button>
          )}

          {open && !markable && (
            <p className="font-primary text-sm text-muted">
              This visit can be completed on the day.
            </p>
          )}
        </div>

        <div className="flex justify-end gap-2">
          {!writable && (
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          )}

          {writable && (
            <Button
              variant={open && markable ? "outline" : "primary"}
              onClick={save}
              disabled={working}
              className={DISABLED}
            >
              {busy === "save"
                ? "Saving…"
                : status === "completed"
                  ? "Save changes"
                  : "Save"}
            </Button>
          )}

          {open && markable && (
            <Button
              variant="primary"
              onClick={complete}
              disabled={working}
              className={DISABLED}
            >
              {busy === "complete" ? "Completing…" : "Save and complete"}
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
}

export default ConsultationModal;
