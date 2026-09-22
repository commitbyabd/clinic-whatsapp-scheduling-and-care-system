import { CLINIC_TIME_ZONE } from "../config/clinic.js";

// The patient choice that means "add a new record" rather than an id.
export const NEW_PATIENT = "new";

const normalise = (text) => (text ?? "").trim().toLowerCase();

const DAY_PARTS = new Intl.DateTimeFormat("en-US", {
  timeZone: CLINIC_TIME_ZONE,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

// "YYYY-MM-DD" for today where the clinic is, which is what a date input
// and the slots endpoint both take. Built from parts, since locales
// disagree on how to write a date.
export function todayInClinic(now = new Date()) {
  const parts = Object.fromEntries(
    DAY_PARTS.formatToParts(now).map(({ type, value }) => [type, value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}`;
}

// The clinic day a moment falls on, "YYYY-MM-DD", or "" if it is not a date
export function clinicDay(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : todayInClinic(date);
}

const TIME = new Intl.DateTimeFormat("en-US", {
  timeZone: CLINIC_TIME_ZONE,
  hour: "numeric",
  minute: "2-digit",
});

const WHEN = new Intl.DateTimeFormat("en-US", {
  timeZone: CLINIC_TIME_ZONE,
  weekday: "short",
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

// A birthday is a day, not a moment, so it is read and shown in UTC and
// never shifts to the day before.
const BIRTHDAY = new Intl.DateTimeFormat("en-US", {
  timeZone: "UTC",
  month: "short",
  day: "numeric",
  year: "numeric",
});

function format(formatter, value) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : formatter.format(date);
}

// "9:00 AM", in clinic time
export const formatSlotTime = (iso) => format(TIME, iso);

// "Thu, Sep 24, 10:00 AM", in clinic time
export const formatAppointment = (iso) => format(WHEN, iso);

// "May 4, 1998" from "1998-05-04"
export const formatBirthDate = (day) =>
  day ? format(BIRTHDAY, `${day}T00:00:00Z`) : "";

/*
  Which patient the form starts on. The receptionist can always change it.

  - someone on this number has the name the patient gave: them
  - a returning patient, and the number has one patient: them
  - a first-time patient, or nobody on the number: a new record
  - otherwise nothing, so the receptionist has to choose
*/
export function defaultPatientChoice(request, patients) {
  const name = normalise(request.patient_name);
  const sameName = name && patients.find((p) => normalise(p.full_name) === name);
  if (sameName) return sameName.id;

  if (request.returning_patient !== "yes" || patients.length === 0) {
    return NEW_PATIENT;
  }

  return patients.length === 1 ? patients[0].id : "";
}

// The doctor whose specialization is the department the model suggested.
// Admins pick specializations from the same list (config/specializations.js),
// so they match; case is ignored for anything saved before that.
export function suggestedDoctorId(doctors, department) {
  const wanted = normalise(department);
  if (!wanted) return "";
  return doctors.find((d) => normalise(d.specialization) === wanted)?.id ?? "";
}
