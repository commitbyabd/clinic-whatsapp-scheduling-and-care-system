import { HeartPulse } from "lucide-react";
import IconBox from "../../ui/IconBox.jsx";
import Badge from "../../ui/Badge.jsx";

function ClinicIdentity() {
  return (
    <div className="flex items-center gap-3">
      <IconBox
        size="size-10"
        radius="rounded-md"
        className="bg-(image:--gradient-brand-panel)"
      >
        <HeartPulse className="size-5 text-seafoam" strokeWidth={2} />
      </IconBox>

      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="font-primary text-md-lg font-semibold text-plum">
          Northgate Clinic
        </span>
        <Badge dot={false} className="bg-lavender text-plum">
          Administrator
        </Badge>
      </div>
    </div>
  );
}

export default ClinicIdentity;
