import { useState } from "react";
import { Clock, RefreshCw } from "lucide-react";
import AppointmentCard from "./AppointmentCard.jsx";
import ConsultationModal from "./ConsultationModal.jsx";
import SectionHeader from "../dashboard/SectionHeader.jsx";
import Alert from "../../ui/Alert.jsx";
import Button from "../../ui/Button.jsx";
import Card from "../../ui/Card.jsx";
import { listAppointments } from "../../../api/doctor.js";
import { useApiResource } from "../../../hooks/useApiResource.js";
import { useAutoRefresh } from "../../../hooks/useAutoRefresh.js";
import {
  dayHeading,
  groupByDay,
  patientFacts,
} from "../../../utils/appointments.js";
import { reasonLabel } from "../../../utils/bookingRequest.js";
import { formatSlotTime, todayInClinic } from "../../../utils/scheduling.js";

const MODES = [
  { value: "upcoming", label: "Upcoming" },
  { value: "past", label: "Past" },
];

const EMPTY = {
  upcoming: "Nothing booked from today onwards.",
  past: "No earlier visits yet.",
};

/*
  The doctor's visits by clinic day: today and the days ahead, or the days
  before. Opening one shows the patient and the write-up.

  needsHours is true when the doctor has no working hours saved, so
  reception has nothing to book them into.
*/
function AppointmentsView({ needsHours, onShowHours, showToast }) {
  const [mode, setMode] = useState("upcoming");
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((current) => current + 1);
  // reception books visits at any moment
  useAutoRefresh(refresh);

  // "Past" asks the server for everything and keeps the earlier days
  const appointments = useApiResource(
    `appointments:${mode}`,
    () => listAppointments(mode === "past"),
    version,
  );

  // The visit being looked at, as it was when opened: a refresh behind the
  // dialog must not reset what the doctor is typing.
  const [opened, setOpened] = useState(null);

  const [today] = useState(todayInClinic);
  const groups =
    appointments.status === "ready"
      ? groupByDay(appointments.data ?? [], mode, today)
      : [];
  const total = groups.reduce((sum, group) => sum + group.appointments.length, 0);

  const count =
    appointments.status === "loading"
      ? "Loading…"
      : `${total} visit${total === 1 ? "" : "s"}`;

  return (
    <>
      <SectionHeader
        title="Appointments"
        subtitle={
          mode === "upcoming"
            ? "Today and the days ahead, in clinic time"
            : "Earlier visits, the latest day first"
        }
        count={count}
        action={
          <div className="flex flex-wrap items-center justify-end gap-2">
            <div
              role="group"
              aria-label="Which visits"
              className="flex rounded-md border border-border bg-white p-1"
            >
              {MODES.map(({ value, label }) => (
                <button
                  key={value}
                  type="button"
                  aria-pressed={mode === value}
                  onClick={() => setMode(value)}
                  className={`h-7 rounded-sm px-3 font-primary text-sm font-semibold transition duration-200 focus-visible:ring-2 focus-visible:ring-violet/22 focus-visible:outline-none ${
                    mode === value
                      ? "bg-plum text-white"
                      : "text-plum hover:bg-pale-lavender"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

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

      <div className="mt-5 space-y-6">
        {needsHours && (
          <Card className="flex flex-col gap-3 bg-butter/40 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
            <p className="font-primary text-sm leading-body text-ink">
              You have no working hours yet, so reception cannot book any
              visits with you.
            </p>
            <Button
              variant="primary"
              size="sm"
              onClick={onShowHours}
              leadingIcon={<Clock className="size-4" strokeWidth={2} />}
            >
              Set working hours
            </Button>
          </Card>
        )}

        {appointments.status === "error" && (
          <Alert>{appointments.message}</Alert>
        )}

        {appointments.status === "loading" && (
          <p className="font-primary text-sm text-muted">
            Loading appointments…
          </p>
        )}

        {appointments.status === "ready" && total === 0 && (
          <p className="font-primary text-sm text-muted">{EMPTY[mode]}</p>
        )}

        {groups.map((group) => (
          <section key={group.day} aria-labelledby={`day-${group.day}`}>
            <h2
              id={`day-${group.day}`}
              className="font-primary text-md font-semibold text-plum"
            >
              {dayHeading(group.day, today)}
            </h2>

            {/* API field names are mapped here so the card stays
                presentation and never sees the backend's vocabulary */}
            <div className="mt-3 space-y-3">
              {group.appointments.map((appointment) => (
                <AppointmentCard
                  key={appointment.id}
                  time={formatSlotTime(appointment.scheduled_for)}
                  duration={appointment.duration_minutes}
                  name={appointment.patient?.full_name ?? "Patient record missing"}
                  facts={patientFacts(appointment.patient)}
                  status={appointment.status}
                  reason={reasonLabel(appointment.reason)}
                  symptoms={appointment.symptom_summary}
                  allergies={appointment.patient?.allergies ?? []}
                  writtenUp={Boolean(appointment.consultation)}
                  onOpen={() => setOpened(appointment)}
                />
              ))}
            </div>
          </section>
        ))}
      </div>

      {opened && (
        <ConsultationModal
          appointment={opened}
          onClose={() => setOpened(null)}
          onSaved={(text) => {
            showToast(text);
            refresh();
          }}
          onDone={(text) => {
            setOpened(null);
            showToast(text);
            refresh();
          }}
        />
      )}
    </>
  );
}

export default AppointmentsView;
