import { CLINIC_TIME_ZONE } from "../config/clinic.js";
import { formatAppointment } from "./scheduling.js";

// the same wording the WhatsApp menu showed the patient
const REASONS = {
  general: "General check-up",
  symptoms: "Feeling unwell",
  followup: "Follow-up visit",
};

export function reasonLabel(reason) {
  return REASONS[reason] ?? "Reason not given";
}

// Every patient is asked their name on WhatsApp now; a request saved before
// that has none, so it is known by its number.
export function patientLabel(request) {
  return request.patient_name || request.whatsapp_number || "Unknown patient";
}

/*
  What the patient asked for in the chat: the open time they picked from
  the numbered menu, or the words they typed when none of them suited. The
  time is theirs to ask for; the receptionist still books it.
*/
export function askedForLabel(request) {
  const slot = formatAppointment(request.requested_slot);
  const when = slot
    ? `Asked for: ${slot}`
    : `Prefers: ${request.preferred_time_text || "no time given"}`;

  return request.requested_doctor_name
    ? `${when}, with ${request.requested_doctor_name}`
    : when;
}

const RECEIVED = new Intl.DateTimeFormat("en-US", {
  timeZone: CLINIC_TIME_ZONE,
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

export function formatReceived(iso) {
  if (!iso) return "";
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? "" : RECEIVED.format(date);
}
