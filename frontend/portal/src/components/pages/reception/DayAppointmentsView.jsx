import { useState } from "react";
import { ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import SectionHeader from "../dashboard/SectionHeader.jsx";
import ReceptionAppointmentCard from "./ReceptionAppointmentCard.jsx";
import RescheduleModal from "./RescheduleModal.jsx";
import Alert from "../../ui/Alert.jsx";
import Button from "../../ui/Button.jsx";
import ConfirmDialog from "../../ui/ConfirmDialog.jsx";
import SmallField from "../../ui/SmallField.jsx";
import TextField from "../../ui/TextField.jsx";
import {
  cancelAppointment,
  listDayAppointments,
} from "../../../api/receptionist.js";
import { readApiError } from "../../../api/auth.js";
import { useApiResource } from "../../../hooks/useApiResource.js";
import { useAutoRefresh } from "../../../hooks/useAutoRefresh.js";
import { dayHeading, shiftDay } from "../../../utils/appointments.js";
import { reasonLabel } from "../../../utils/bookingRequest.js";
import {
  formatAppointment,
  formatSlotTime,
  todayInClinic,
} from "../../../utils/scheduling.js";

const ICON_BUTTON =
  "grid size-9 place-items-center rounded-md border border-border bg-white text-plum transition duration-200 hover:bg-pale-lavender focus-visible:ring-2 focus-visible:ring-violet/22 focus-visible:outline-none";

/*
  One clinic day at the front desk: every doctor's visits in time order,
  cancelled ones included. A visit still to come can be moved to another
  free time or cancelled, with a reason kept on the record.
*/
function DayAppointmentsView({ showToast }) {
  const [today] = useState(todayInClinic);
  const [day, setDay] = useState(today);

  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((current) => current + 1);
  // bookings are made and changed at any moment
  useAutoRefresh(refresh);

  const appointments = useApiResource(
    `day:${day}`,
    () => listDayAppointments(day),
    version,
  );
  const rows = appointments.status === "ready" ? (appointments.data ?? []) : [];
  const upcoming = rows.filter(
    (row) => row.status === "booked" || row.status === "confirmed",
  ).length;

  const [moving, setMoving] = useState(null);
  const [cancelling, setCancelling] = useState(null);
  const [cancelReason, setCancelReason] = useState("");
  const [cancelBusy, setCancelBusy] = useState(false);
  const [cancelError, setCancelError] = useState("");

  const closeCancel = () => {
    setCancelling(null);
    setCancelReason("");
    setCancelError("");
  };

  const handleCancel = async () => {
    setCancelBusy(true);
    setCancelError("");
    const target = cancelling;

    try {
      await cancelAppointment(target.id, cancelReason.trim() || null);
      closeCancel();
      refresh();
      const whose = target.patient.full_name
        ? `${target.patient.full_name}'s visit`
        : "The visit";
      showToast(`${whose} was cancelled. Let them know on WhatsApp.`);
    } catch (error) {
      setCancelError(readApiError(error));
    } finally {
      setCancelBusy(false);
    }
  };

  const count =
    appointments.status === "loading"
      ? "Loading…"
      : `${rows.length} visit${rows.length === 1 ? "" : "s"}, ${upcoming} still to come`;

  return (
    <>
      <SectionHeader
        title="Appointments"
        subtitle={dayHeading(day, today)}
        count={count}
        action={
          <div className="flex flex-wrap items-end justify-end gap-2">
            <button
              type="button"
              onClick={() => setDay((current) => shiftDay(current, -1))}
              aria-label="Previous day"
              className={ICON_BUTTON}
            >
              <ChevronLeft className="size-4" strokeWidth={2} />
            </button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDay(today)}
              disabled={day === today}
              className="disabled:pointer-events-none disabled:opacity-60"
            >
              Today
            </Button>
            <button
              type="button"
              onClick={() => setDay((current) => shiftDay(current, 1))}
              aria-label="Next day"
              className={ICON_BUTTON}
            >
              <ChevronRight className="size-4" strokeWidth={2} />
            </button>
            <SmallField
              id="appointments-day"
              label="Day"
              type="date"
              className="w-40 [&_label]:sr-only [&_input]:mt-0 [&_input]:h-9"
              value={day}
              onChange={(event) => event.target.value && setDay(event.target.value)}
            />
            <Button
              variant="outline"
              size="sm"
              leadingIcon={<RefreshCw className="size-4" strokeWidth={2} />}
              onClick={refresh}
            >
              Refresh
            </Button>
          </div>
        }
      />

      <div className="mt-5 space-y-3">
        {appointments.status === "error" && (
          <Alert>{appointments.message}</Alert>
        )}

        {appointments.status === "loading" && (
          <p className="font-primary text-sm text-muted">
            Loading appointments…
          </p>
        )}

        {appointments.status === "ready" && rows.length === 0 && (
          <p className="font-primary text-sm text-muted">
            No visits booked on this day.
          </p>
        )}

        {rows.map((row) => (
          <ReceptionAppointmentCard
            key={row.id}
            time={formatSlotTime(row.scheduled_for)}
            duration={row.duration_minutes}
            patient={row.patient.full_name ?? "Patient record missing"}
            phone={row.patient.whatsapp_number}
            doctor={row.doctor.full_name ?? "Doctor"}
            specialization={row.doctor.specialization}
            status={row.status}
            reason={reasonLabel(row.reason)}
            cancelReason={row.cancel_reason}
            onMove={() => setMoving(row)}
            onCancel={() => setCancelling(row)}
          />
        ))}
      </div>

      {moving && (
        <RescheduleModal
          appointment={moving}
          onClose={() => setMoving(null)}
          onMoved={({ patientName, doctorName, startsAt }) => {
            setMoving(null);
            refresh();
            showToast(
              `Moved ${patientName} to ${formatAppointment(startsAt)} with ${doctorName}.`,
            );
          }}
        />
      )}

      {cancelling && (
        <ConfirmDialog
          title="Cancel visit"
          message={`Cancel ${cancelling.patient.full_name ?? "this patient"}'s visit on ${formatAppointment(cancelling.scheduled_for)} with ${cancelling.doctor.full_name ?? "the doctor"}? The time becomes free to book again, and the visit stays on record.`}
          confirmLabel="Cancel visit"
          cancelLabel="Keep it"
          busy={cancelBusy}
          error={cancelError}
          onConfirm={handleCancel}
          onClose={closeCancel}
        >
          <TextField
            id="cancel-reason"
            label="Reason (optional)"
            placeholder="e.g. the patient asked to cancel"
            maxLength={200}
            value={cancelReason}
            onChange={(event) => setCancelReason(event.target.value)}
            disabled={cancelBusy}
          />
        </ConfirmDialog>
      )}
    </>
  );
}

export default DayAppointmentsView;
