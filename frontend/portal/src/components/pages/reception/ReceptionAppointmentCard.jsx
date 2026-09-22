import { ArrowRightLeft, Ban, Phone, Stethoscope } from "lucide-react";
import Badge from "../../ui/Badge.jsx";
import Button from "../../ui/Button.jsx";
import Card from "../../ui/Card.jsx";
import StatusBadge from "../../ui/StatusBadge.jsx";

/*
  One booked visit at the front desk: who, with which doctor, and when.

  Presentation only: DayAppointmentsView maps the API's fields into these
  props. Move and Cancel are offered only while the visit is still to come.
*/
function ReceptionAppointmentCard({
  time,
  duration,
  patient,
  phone,
  doctor,
  specialization,
  status,
  reason,
  cancelReason,
  onMove,
  onCancel,
}) {
  const upcoming = status === "booked" || status === "confirmed";

  return (
    <Card
      as="article"
      className={`p-4 shadow-[0_12px_30px_var(--plum-17)] sm:p-5 ${
        upcoming ? "bg-porcelain/92" : "bg-porcelain/70"
      }`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
        <div className="flex min-w-0 items-start gap-4">
          <div className="w-20 shrink-0">
            <p className="font-primary text-md-lg font-semibold text-plum">
              {time}
            </p>
            <p className="font-primary text-xs text-muted">{duration} min</p>
          </div>

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
              <p className="font-primary text-md-lg font-semibold text-plum">
                {patient}
              </p>
              <StatusBadge status={status} />
            </div>
            {phone && (
              <p className="mt-1 flex items-center gap-2 font-primary text-sm text-ink">
                <Phone className="size-4 shrink-0 text-violet" strokeWidth={2} />
                {phone}
              </p>
            )}
            <p className="mt-1 flex items-center gap-2 font-primary text-sm text-ink">
              <Stethoscope
                className="size-4 shrink-0 text-violet"
                strokeWidth={2}
              />
              {doctor}
              {specialization && (
                <span className="text-muted">· {specialization}</span>
              )}
            </p>
          </div>
        </div>

        {upcoming && (
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            <Button
              variant="danger"
              size="sm"
              onClick={onCancel}
              aria-label={`Cancel the visit of ${patient}`}
              leadingIcon={<Ban className="size-4" strokeWidth={2} />}
            >
              Cancel
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onMove}
              aria-label={`Move the visit of ${patient}`}
              leadingIcon={<ArrowRightLeft className="size-4" strokeWidth={2} />}
            >
              Move
            </Button>
          </div>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <Badge dot={false} className="bg-lavender text-plum">
          {reason}
        </Badge>
        {cancelReason && (
          <Badge dot={false} className="bg-border text-muted">
            Cancelled: {cancelReason}
          </Badge>
        )}
      </div>
    </Card>
  );
}

export default ReceptionAppointmentCard;
