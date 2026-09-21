import { RefreshCw } from "lucide-react";
import DashboardHeader from "../dashboard/DashboardHeader.jsx";
import SectionHeader from "../dashboard/SectionHeader.jsx";
import BookingRequestCard from "./BookingRequestCard.jsx";
import Alert from "../../ui/Alert.jsx";
import Button from "../../ui/Button.jsx";
import { useBookingRequests } from "../../../hooks/useBookingRequests.js";
import { initialsFrom } from "../../../utils/initials.js";
import {
  formatReceived,
  patientLabel,
  reasonLabel,
} from "../../../utils/bookingRequest.js";

// The receptionist's inbox: WhatsApp booking chats waiting to be scheduled.
function ReceptionMain() {
  const { status, items, message, refresh } = useBookingRequests("new");

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
                />
              ))}
          </div>
        </section>
      </div>
    </div>
  );
}

export default ReceptionMain;
