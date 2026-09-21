import StatusBadge from "./StatusBadge.jsx";
import { formatAppointment } from "../../../utils/scheduling.js";

// The patient's earlier visits that happened (completed or missed), with
// any doctor, most recent first. The server sends at most twenty.
function VisitHistory({ visits }) {
  return (
    <section aria-labelledby="visit-history">
      <h3
        id="visit-history"
        className="font-primary text-md-lg font-semibold text-plum"
      >
        Past visits
      </h3>

      {visits.length === 0 && (
        <p className="mt-2 font-primary text-sm text-muted">
          No earlier visits on record.
        </p>
      )}

      {visits.length > 0 && (
        <ol className="mt-3 space-y-2">
          {visits.map((visit) => (
            <li
              key={visit.id}
              className="rounded-md border border-border bg-white px-4 py-3"
            >
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <p className="font-primary text-sm font-semibold text-plum">
                  {formatAppointment(visit.scheduled_for)}
                </p>
                <StatusBadge status={visit.status} small />
                {visit.seen_by && (
                  <p className="font-primary text-xs text-muted">
                    Seen by {visit.seen_by}
                  </p>
                )}
              </div>
              {visit.diagnosis && (
                <p className="mt-2 font-primary text-sm text-ink">
                  <span className="font-semibold">Diagnosis: </span>
                  {visit.diagnosis}
                </p>
              )}
              {visit.doctor_notes && (
                <p className="mt-1 line-clamp-3 font-primary text-sm leading-body whitespace-pre-line text-muted">
                  {visit.doctor_notes}
                </p>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

export default VisitHistory;
