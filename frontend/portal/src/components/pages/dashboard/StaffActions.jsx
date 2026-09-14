import { Pencil, Ban, RotateCcw } from "lucide-react";
import Button from "../../ui/Button.jsx";

// Every button only opens a dialog. The request belongs to whoever owns the
// list, since that is what has to refresh afterwards.
function StaffActions({ name, onEdit, onDeactivate, onReactivate }) {
  // A deactivated account has nothing worth editing until it is restored,
  // so that list offers the one action that changes anything.
  if (onReactivate) {
    return (
      <div className="flex shrink-0 items-center gap-2">
        <Button
          variant="primary"
          size="sm"
          onClick={onReactivate}
          aria-label={`Reactivate ${name}`}
          leadingIcon={<RotateCcw className="size-4" strokeWidth={2} />}
        >
          Reactivate
        </Button>
      </div>
    );
  }

  return (
    <div className="flex shrink-0 items-center gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={onEdit}
        aria-label={`Edit ${name}`}
        leadingIcon={<Pencil className="size-4" strokeWidth={2} />}
      >
        Edit
      </Button>

      <Button
        variant="danger"
        size="sm"
        onClick={onDeactivate}
        aria-label={`Deactivate ${name}`}
        leadingIcon={<Ban className="size-4" strokeWidth={2} />}
      >
        Deactivate
      </Button>
    </div>
  );
}

export default StaffActions;
