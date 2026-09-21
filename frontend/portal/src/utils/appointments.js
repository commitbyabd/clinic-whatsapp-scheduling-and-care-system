import { clinicDay, todayInClinic } from "./scheduling.js";

const STATUSES = {
  booked: "Booked",
  confirmed: "Confirmed",
  completed: "Completed",
  no_show: "No-show",
  cancelled: "Cancelled",
};

export const statusLabel = (status) => STATUSES[status] ?? "Unknown";

// Still to be seen, so it can be marked completed or a no-show
export const isOpenVisit = (status) =>
  status === "booked" || status === "confirmed";

// Anything but a cancelled or missed visit can be written up, as on the server
export const canWriteUp = (status) =>
  isOpenVisit(status) || status === "completed";

const GENDERS = { female: "Female", male: "Male", other: "Other" };

// "Age 34 · Female", or whichever of the two is known
export function patientFacts(patient) {
  const parts = [];
  if (Number.isInteger(patient?.age)) parts.push(`Age ${patient.age}`);
  if (patient?.gender) parts.push(GENDERS[patient.gender] ?? patient.gender);
  return parts.join(" · ");
}

function shiftDay(day, days) {
  const date = new Date(`${day}T00:00:00Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

// A day is not a moment, so it is shown in UTC and never shifts
const DAY_NAME = new Intl.DateTimeFormat("en-US", {
  timeZone: "UTC",
  weekday: "short",
  month: "short",
  day: "numeric",
});

// "Thu, Sep 24" from "2026-09-24"
export const formatDay = (day) => DAY_NAME.format(new Date(`${day}T00:00:00Z`));

// "Today · Mon, Sep 21", "Tomorrow · …", "Yesterday · …" or "Thu, Sep 24"
export function dayHeading(day, today = todayInClinic()) {
  const date = formatDay(day);
  const near = {
    [today]: "Today",
    [shiftDay(today, 1)]: "Tomorrow",
    [shiftDay(today, -1)]: "Yesterday",
  }[day];
  return near ? `${near} · ${date}` : date;
}

/*
  Splits the list into clinic days. "upcoming" keeps today onwards, soonest
  day first; "past" keeps the days before today, latest day first. Within a
  day the visits are always in time order, the way the doctor sees them.
*/
export function groupByDay(appointments, mode, today = todayInClinic()) {
  const past = mode === "past";

  const rows = appointments
    .map((appointment) => ({
      appointment,
      day: clinicDay(appointment.scheduled_for),
    }))
    .filter(({ day }) => day && (past ? day < today : day >= today))
    .sort((a, b) => {
      if (a.day !== b.day) return (a.day < b.day ? -1 : 1) * (past ? -1 : 1);
      return a.appointment.scheduled_for < b.appointment.scheduled_for
        ? -1
        : 1;
    });

  const groups = [];
  for (const { appointment, day } of rows) {
    const last = groups.at(-1);
    if (last?.day === day) last.appointments.push(appointment);
    else groups.push({ day, appointments: [appointment] });
  }
  return groups;
}
