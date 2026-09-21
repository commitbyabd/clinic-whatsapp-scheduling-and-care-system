import { useRef, useState } from "react";
import { RefreshCw } from "lucide-react";
import DashboardHeader from "../dashboard/DashboardHeader.jsx";
import SectionHeader from "../dashboard/SectionHeader.jsx";
import BookingRequestCard from "./BookingRequestCard.jsx";
import ScheduleModal from "./ScheduleModal.jsx";
import Alert from "../../ui/Alert.jsx";
import Button from "../../ui/Button.jsx";
import ConfirmDialog from "../../ui/ConfirmDialog.jsx";
import Toast from "../../ui/Toast.jsx";
import { declineBookingRequest } from "../../../api/receptionist.js";
import { readApiError } from "../../../api/auth.js";
import { useBookingRequests } from "../../../hooks/useBookingRequests.js";
import { initialsFrom } from "../../../utils/initials.js";
import {
  formatReceived,
  patientLabel,
  reasonLabel,
} from "../../../utils/bookingRequest.js";
import { formatAppointment } from "../../../utils/scheduling.js";

// The receptionist's inbox: WhatsApp booking chats waiting to be scheduled.
function ReceptionMain() {
  const { status, items, message, refresh } = useBookingRequests("new");

  const [scheduling, setScheduling] = useState(null);
  const [declining, setDeclining] = useState(null);
  const [declineBusy, setDeclineBusy] = useState(false);
  const [declineError, setDeclineError] = useState("");

  // a counter, so two toasts in the same millisecond still get their own key
  const toastId = useRef(0);
  const [toast, setToast] = useState(null);
  const showToast = (text) => {
    toastId.current += 1;
    setToast({ id: toastId.current, text });
  };

  // Every dialog reloads the list when it closes, even on Cancel: another
  // receptionist may have handled a request in the meantime.
  const closeSchedule = () => {
    setScheduling(null);
    refresh();
  };

  const closeDecline = () => {
    setDeclining(null);
    setDeclineError("");
    refresh();
  };

  const handleScheduled = ({ patientName, doctorName, startsAt }) => {
    closeSchedule();
    showToast(
      `Booked ${patientName} with ${doctorName}, ${formatAppointment(startsAt)}.`,
    );
  };

  const handleDecline = async () => {
    setDeclineBusy(true);
    setDeclineError("");

    // captured before the dialog closes, since declining is null by then
    const target = declining;

    try {
      await declineBookingRequest(target.id);
      closeDecline();
      showToast(`The request from ${patientLabel(target)} was declined.`);
    } catch (error) {
      setDeclineError(readApiError(error));
    } finally {
      setDeclineBusy(false);
    }
  };

  const count =
    status === "loading" ? "Loading…" : `${items.length} waiting`;

  return (
    <div className="relative min-h-screen bg-porcelain">
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 bg-(image:--gradient-page) opacity-40"
      />

      <div className="relative">
        <DashboardHeader roleLabel="Reception" />

        <section className="mx-auto max-w-310 px-4 py-6 sm:px-6">
          <SectionHeader
            title="Booking requests"
            subtitle="WhatsApp requests waiting for a receptionist, newest first"
            count={count}
            action={
              <Button
                variant="outline"
                size="sm"
                leadingIcon={<RefreshCw className="size-4" strokeWidth={2} />}
                onClick={refresh}
              >
                Refresh
              </Button>
            }
          />

          <div className="mt-5 space-y-4">
            {status === "error" && <Alert>{message}</Alert>}

            {status === "loading" && (
              <p className="font-primary text-sm text-muted">
                Loading booking requests…
              </p>
            )}

            {status === "ready" && items.length === 0 && (
              <p className="font-primary text-sm text-muted">
                No new requests. Bookings made on WhatsApp will appear here.
              </p>
            )}

            {/* API field names are mapped here so the card stays
                presentation and never sees the backend's vocabulary */}
            {status === "ready" &&
              items.map((request) => (
                <BookingRequestCard
                  key={request.id}
                  initials={initialsFrom(request.patient_name ?? "") || "?"}
                  title={patientLabel(request)}
                  phone={request.patient_name ? request.whatsapp_number : null}
                  returning={request.returning_patient === "yes"}
                  reason={reasonLabel(request.reason)}
                  symptoms={request.symptom_text}
                  department={request.suggested_specialization}
                  preferredTime={request.preferred_time_text}
                  received={formatReceived(request.created_at)}
                  onSchedule={() => setScheduling(request)}
                  onDecline={() => setDeclining(request)}
                />
              ))}
          </div>
        </section>
      </div>

      {scheduling && (
        <ScheduleModal
          request={scheduling}
          onClose={closeSchedule}
          onScheduled={handleScheduled}
        />
      )}

      {declining && (
        <ConfirmDialog
          title="Decline request"
          message={`Decline the request from ${patientLabel(declining)}? It leaves the inbox and no appointment is made. WhatsApp does not tell the patient yet, so let them know.`}
          confirmLabel="Decline"
          busy={declineBusy}
          error={declineError}
          onConfirm={handleDecline}
          onClose={closeDecline}
        />
      )}

      {toast && (
        <Toast
          key={toast.id}
          message={toast.text}
          duration={4000}
          onDone={() => setToast(null)}
        />
      )}
    </div>
  );
}

export default ReceptionMain;
