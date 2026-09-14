import { ShieldCheck } from "lucide-react";
import IconBox from "../../ui/IconBox.jsx";

function SecurityNote() {
  return (
    <div className="flex items-center gap-3 rounded-md bg-lavender p-3.5">
      <IconBox className="bg-white">
        <ShieldCheck className="size-4 text-violet" strokeWidth={2} />
      </IconBox>
      <p className="font-primary text-sm leading-body text-muted">
        Access is restricted to authorised clinic staff.
      </p>
    </div>
  );
}

export default SecurityNote;
