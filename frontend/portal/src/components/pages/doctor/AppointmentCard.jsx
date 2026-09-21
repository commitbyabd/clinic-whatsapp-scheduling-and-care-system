import { FileText, MessageSquareText, TriangleAlert } from "lucide-react";
import Card from "../../ui/Card.jsx";
import Badge from "../../ui/Badge.jsx";
import Button from "../../ui/Button.jsx";
import StatusBadge from "./StatusBadge.jsx";

/*
  One visit in the doctor's list.

  Presentation only: AppointmentsView maps the API's fields into these
  props. Allergies are shown here as well as inside, so they are seen
  before the visit is even opened.
*/
function AppointmentCard({
  time,
  duration,
  name,
  facts,
  status,
  reason,
  symptoms,
  allergies,
  writtenUp,
  onOpen,
}) {
  return (
    <Card
      as="article"
      className="bg-porcelain/92 p-4 shadow-[0_12px_30px_var(--plum-17)] sm:p-5"
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
                {name}
              </p>
              <StatusBadge status={status} />
            </div>
            {facts && (
              <p className="mt-1 font-primary text-sm text-muted">{facts}</p>
            )}
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={onOpen}
          aria-label={`Open the visit with ${name}`}
          leadingIcon={<FileText className="size-4" strokeWidth={2} />}
        >
          Open
        </Button>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Badge dot={false} className="bg-lavender text-plum">
          {reason}
        </Badge>
        {allergies.length > 0 && (
          <Badge dot={false} className="bg-error-bg text-error">
            <TriangleAlert className="size-4" strokeWidth={2} />
            Allergies: {allergies.join(", ")}
          </Badge>
        )}
        {writtenUp && (
          <Badge dotClassName="bg-violet" className="bg-seafoam/50 text-plum">
            Written up
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
    </Card>
  );
}

export default AppointmentCard;
