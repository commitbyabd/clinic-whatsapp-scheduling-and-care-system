import { KeyRound, Mail, X } from "lucide-react";
import Card from "../../ui/Card.jsx";
import Avatar from "../../ui/Avatar.jsx";
import Badge from "../../ui/Badge.jsx";
import Button from "../../ui/Button.jsx";

/*
  One staff member who cannot sign in, as sent from the sign-in page.

  Presentation only: DashboardMain maps the API's field names into these
  props. Reset password opens the same dialog as the staff lists; the
  request closes itself once the password is reset.
*/
function PasswordRequestCard({
  initials,
  name,
  role,
  email,
  asked,
  times = 1,
  onReset,
  onDismiss,
  busy = false,
}) {
  return (
    <Card
      as="article"
      className="bg-porcelain/92 p-4 shadow-[0_12px_30px_var(--plum-17)] sm:p-5"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between sm:gap-6">
        <div className="flex min-w-0 items-center gap-4">
          <Avatar initials={initials} className="bg-seafoam/60" />

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
              <p className="font-primary text-md-lg font-semibold text-plum">
                {name}
              </p>
              <Badge
                dot={false}
                className="border border-border bg-pale-lavender text-violet"
              >
                {role}
              </Badge>

              {/* they pressed Send more than once, so they are waiting */}
              {times > 1 && (
                <Badge
                  dotClassName="bg-violet"
                  className="bg-seafoam/50 text-plum"
                >
                  Asked {times} times
                </Badge>
              )}
            </div>

            <p className="mt-2 flex items-center gap-2 font-primary text-sm text-ink">
              <Mail className="size-4 shrink-0 text-violet" strokeWidth={2} />
              <span className="truncate">{email}</span>
            </p>
          </div>
        </div>

        <p className="shrink-0 font-primary text-xs text-muted">
          Asked {asked}
        </p>
      </div>

      <div className="mt-4 flex flex-wrap justify-end gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onDismiss}
          disabled={busy}
          aria-label={`Dismiss the request from ${name}`}
          leadingIcon={<X className="size-4" strokeWidth={2} />}
        >
          Dismiss
        </Button>

        <Button
          variant="primary"
          size="sm"
          onClick={onReset}
          disabled={busy}
          aria-label={`Reset ${name}'s password`}
          leadingIcon={<KeyRound className="size-4" strokeWidth={2} />}
        >
          Reset password
        </Button>
      </div>
    </Card>
  );
}

export default PasswordRequestCard;
