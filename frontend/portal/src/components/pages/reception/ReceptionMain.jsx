import { useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CalendarDays, Inbox } from "lucide-react";
import DashboardHeader from "../dashboard/DashboardHeader.jsx";
import DayAppointmentsView from "./DayAppointmentsView.jsx";
import InboxView from "./InboxView.jsx";
import TabNav from "../../ui/TabNav.jsx";
import Toast from "../../ui/Toast.jsx";

const TABS = [
  { slug: "requests", label: "Requests", icon: Inbox },
  { slug: "appointments", label: "Appointments", icon: CalendarDays },
];

// The front desk: WhatsApp requests to handle, and the visits already booked.
function ReceptionMain() {
  // The tab lives in the URL, so a refresh keeps it.
  const [searchParams, setSearchParams] = useSearchParams();
  const tab =
    searchParams.get("tab") === "appointments" ? "appointments" : "requests";
  const selectTab = (slug) => setSearchParams({ tab: slug }, { replace: true });

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
        <DashboardHeader roleLabel="Reception" />

        <section className="mx-auto max-w-310 px-4 py-6 sm:px-6">
          <TabNav
            tabs={TABS}
            active={tab}
            onSelect={selectTab}
            label="Reception"
          />

          {tab === "requests" ? (
            <InboxView showToast={showToast} />
          ) : (
            <DayAppointmentsView showToast={showToast} />
          )}
        </section>
      </div>

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
