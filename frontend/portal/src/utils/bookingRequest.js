import { CLINIC_TIME_ZONE } from "../config/clinic.js";

// the same wording the WhatsApp menu showed the patient
const REASONS = {
  general: "General check-up",
  symptoms: "Feeling unwell",
  followup: "Follow-up visit",
};

export function reasonLabel(reason) {
  return REASONS[reason] ?? "Reason not given";
}

// Only first-time patients are asked their name on WhatsApp, so a returning
// patient is known by their number until the receptionist matches them.
export function patientLabel(request) {
  return request.patient_name || request.whatsapp_number || "Unknown patient";
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
