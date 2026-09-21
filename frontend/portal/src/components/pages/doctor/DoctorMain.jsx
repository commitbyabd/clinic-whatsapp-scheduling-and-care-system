import { useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CalendarClock, Clock } from "lucide-react";
import DashboardHeader from "../dashboard/DashboardHeader.jsx";
import AppointmentsView from "./AppointmentsView.jsx";
import WorkingHoursView from "./WorkingHoursView.jsx";
import Toast from "../../ui/Toast.jsx";
import { getSchedule } from "../../../api/doctor.js";
import { useApiResource } from "../../../hooks/useApiResource.js";
import { hasWorkingHours } from "../../../utils/workingHours.js";

const TABS = [
  { slug: "appointments", label: "Appointments", icon: CalendarClock },
  { slug: "hours", label: "Working hours", icon: Clock },
];

// The doctor's portal: their visits, and the hours reception books them into.
function DoctorMain() {
  // The tab lives in the URL, so a refresh keeps it.
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get("tab") === "hours" ? "hours" : "appointments";
  const selectTab = (slug) => setSearchParams({ tab: slug }, { replace: true });

  // Loaded here because both tabs need it: the hours to edit, and whether
  // any are set at all. After a save the saved copy takes over, so nothing
  // has to be fetched again.
  const loaded = useApiResource("schedule", getSchedule);
  const [saved, setSaved] = useState(null);
  const schedule = saved ? { status: "ready", data: saved } : loaded;

  // a counter, so two toasts in the same millisecond still get their own key
  const toastId = useRef(0);
  const [toast, setToast] = useState(null);
  const showToast = (text) => {
    toastId.current += 1;
    setToast({ id: toastId.current, text });
  };

  return (
    <div className="relative min-h-screen bg-porcelain">
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 bg-(image:--gradient-page) opacity-40"
      />

      <div className="relative">
        <DashboardHeader roleLabel="Doctor" />

        <div className="mx-auto max-w-310 px-4 py-6 sm:px-6">
          <nav aria-label="Doctor portal" className="mb-6 flex flex-wrap gap-2">
            {TABS.map(({ slug, label, icon: Icon }) => {
              const active = tab === slug;
              return (
                <button
                  key={slug}
                  type="button"
                  aria-current={active ? "page" : undefined}
                  onClick={() => selectTab(slug)}
                  className={`inline-flex h-10 items-center gap-2 rounded-pill px-4 font-primary text-sm font-semibold transition duration-200 focus-visible:ring-4 focus-visible:ring-violet/22 focus-visible:outline-none ${
                    active
                      ? "bg-plum text-white shadow-button"
                      : "border border-border bg-white text-plum hover:bg-pale-lavender"
                  }`}
                >
                  <Icon className="size-4" strokeWidth={2} />
                  {label}
                </button>
              );
            })}
          </nav>

          <section>
            {tab === "appointments" ? (
              <AppointmentsView
                needsHours={
                  schedule.status === "ready" && !hasWorkingHours(schedule.data)
                }
                onShowHours={() => selectTab("hours")}
                showToast={showToast}
              />
            ) : (
              <WorkingHoursView
                schedule={schedule}
                onSaved={(data) => {
                  setSaved(data);
                  showToast("Working hours saved.");
                }}
              />
            )}
          </section>
        </div>
      </div>

      {toast && (
        <Toast
          key={toast.id}
          message={toast.text}
          duration={3000}
          onDone={() => setToast(null)}
        />
      )}
    </div>
  );
}

export default DoctorMain;
