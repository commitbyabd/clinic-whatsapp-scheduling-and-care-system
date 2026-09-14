import { Mail } from "lucide-react";
import Badge from "../../ui/Badge.jsx";

function StaffInfo({ name, specialty, role, email }) {
  return (
    <div className="min-w-0">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <p className="font-primary text-md-lg font-semibold text-plum">
          {name}
        </p>

        {/* Receptionists have no specialization */}
        {specialty && (
          <Badge
            dot={false}
            className="border border-border bg-pale-lavender text-violet"
          >
            {specialty}
          </Badge>
        )}
      </div>

      <p className="mt-1 font-primary text-sm text-muted">{role}</p>

      <p className="mt-2 flex items-center gap-2 font-primary text-sm text-ink">
        <Mail className="size-4 shrink-0 text-violet" strokeWidth={2} />
        <span className="truncate">{email}</span>
      </p>
    </div>
  );
}

export default StaffInfo;
