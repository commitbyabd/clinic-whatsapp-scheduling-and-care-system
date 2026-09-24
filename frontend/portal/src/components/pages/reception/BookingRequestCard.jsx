import {
  Ban,
  CalendarClock,
  CalendarPlus,
  MessageSquareText,
  Phone,
} from "lucide-react";
import Card from "../../ui/Card.jsx";
import Avatar from "../../ui/Avatar.jsx";
import Badge from "../../ui/Badge.jsx";
import Button from "../../ui/Button.jsx";

/*
  One WhatsApp booking request.

  Presentation only: ReceptionMain maps the API's field names into these
  props. 'phone' is left out when the title already is the number. Both
  actions only open a dialog; the list that owns the request does the rest.
*/
function BookingRequestCard({
  initials,
  title,
  phone,
  returning,
  reason,
  symptoms,
  department,
  asked,
  received,
  onSchedule,
  onDecline,
}) {
  return (
    <Card
      as="article"
      className="bg-porcelain/92 p-4 shadow-[0_12px_30px_var(--plum-17)] sm:p-5"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
        <div className="flex min-w-0 items-center gap-4">
          <Avatar initials={initials} className="bg-seafoam/60" />

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
              <p className="font-primary text-md-lg font-semibold text-plum">
                {title}
              </p>
              <Badge
                dot={false}
                className="border border-border bg-pale-lavender text-violet"
              >
                {returning ? "Returning patient" : "New patient"}
              </Badge>
            </div>

            {phone && (
              <p className="mt-1 flex items-center gap-2 font-primary text-sm text-ink">
                <Phone className="size-4 shrink-0 text-violet" strokeWidth={2} />
                <span>{phone}</span>
              </p>
            )}
          </div>
        </div>

        <p className="shrink-0 font-primary text-xs text-muted">
          Received {received}
        </p>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Badge dot={false} className="bg-lavender text-plum">
          {reason}
        </Badge>
        {/* the model's suggestion, only when it was confident enough */}
        {department && (
          <Badge dotClassName="bg-violet" className="bg-seafoam/50 text-plum">
            Suggested: {department}
          </Badge>
        )}
      </div>

      {symptoms && (
        <p className="mt-3 flex items-start gap-2 font-primary text-sm leading-body text-ink">
          <MessageSquareText
            className="mt-0.5 size-4 shrink-0 text-violet"
            strokeWidth={2}
          />
          <span>“{symptoms}”</span>
        </p>
      )}

      <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="flex items-center gap-2 font-primary text-sm text-ink">
          <CalendarClock
            className="size-4 shrink-0 text-violet"
            strokeWidth={2}
          />
          <span>{asked}</span>
        </p>

        <div className="flex shrink-0 items-center gap-2">
          <Button
            variant="danger"
            size="sm"
            onClick={onDecline}
            aria-label={`Decline the request from ${title}`}
            leadingIcon={<Ban className="size-4" strokeWidth={2} />}
          >
            Decline
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={onSchedule}
            aria-label={`Schedule ${title}`}
            leadingIcon={<CalendarPlus className="size-4" strokeWidth={2} />}
          >
            Schedule
          </Button>
        </div>
      </div>
    </Card>
  );
}

export default BookingRequestCard;
