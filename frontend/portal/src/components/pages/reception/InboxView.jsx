import { useState } from "react";
import { RefreshCw } from "lucide-react";
import SectionHeader from "../dashboard/SectionHeader.jsx";
import BookingRequestCard from "./BookingRequestCard.jsx";
import ScheduleModal from "./ScheduleModal.jsx";
import Alert from "../../ui/Alert.jsx";
import Button from "../../ui/Button.jsx";
import ConfirmDialog from "../../ui/ConfirmDialog.jsx";
import TextField from "../../ui/TextField.jsx";
import { declineBookingRequest } from "../../../api/receptionist.js";
import { readApiError } from "../../../api/auth.js";
import { useAutoRefresh } from "../../../hooks/useAutoRefresh.js";
import { useBookingRequests } from "../../../hooks/useBookingRequests.js";
import { initialsFrom } from "../../../utils/initials.js";
import {
  formatReceived,
  patientLabel,
  reasonLabel,
} from "../../../utils/bookingRequest.js";
import { formatAppointment } from "../../../utils/scheduling.js";

// The inbox: WhatsApp booking chats waiting to be scheduled or declined.
function InboxView({ showToast }) {
  const { status, items, message, refresh } = useBookingRequests("new");
  // new requests arrive from WhatsApp at any moment
  useAutoRefresh(refresh);

  const [scheduling, setScheduling] = useState(null);
  const [declining, setDeclining] = useState(null);
  const [declineReason, setDeclineReason] = useState("");
  const [declineBusy, setDeclineBusy] = useState(false);
  const [declineError, setDeclineError] = useState("");

  // Every dialog reloads the list when it closes, even on Cancel: another
  // receptionist may have handled a request in the meantime.
  const closeSchedule = () => {
    setScheduling(null);
    refresh();
  };

  const closeDecline = () => {
    setDeclining(null);
    setDeclineReason("");
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
      await declineBookingRequest(target.id, declineReason.trim() || null);
      closeDecline();
      showToast(`The request from ${patientLabel(target)} was declined.`);
    } catch (error) {
      setDeclineError(readApiError(error));
    } finally {
      setDeclineBusy(false);
    }
  };

  const count = status === "loading" ? "Loading…" : `${items.length} waiting`;

  return (
    <>
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
        >
          <TextField
            id="decline-reason"
            label="Reason (optional)"
            placeholder="e.g. booked by phone instead"
            maxLength={200}
            value={declineReason}
            onChange={(event) => setDeclineReason(event.target.value)}
            disabled={declineBusy}
          />
        </ConfirmDialog>
      )}
    </>
  );
}

export default InboxView;
