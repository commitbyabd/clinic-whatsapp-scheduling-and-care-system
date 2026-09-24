import { statusLabel } from "../../utils/appointments.js";

const TONES = {
  // gold for a visit still to happen, sage once it has, rose for a no-show:
  // the website's own colour language
  booked: "bg-butter text-plum",
  confirmed: "bg-seafoam/60 text-plum",
  completed: "bg-seafoam text-plum",
  no_show: "bg-error-bg text-error",
  cancelled: "bg-border text-muted",
};

// A visit's status as a small pill, sized to sit beside a name or a date
function StatusBadge({ status, small = false }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center rounded-pill font-primary font-medium ${
        small ? "px-2.5 py-0.5 text-xs" : "px-3 py-1 text-sm"
      } ${TONES[status] ?? TONES.cancelled}`}
    >
      {statusLabel(status)}
    </span>
  );
}

export default StatusBadge;
