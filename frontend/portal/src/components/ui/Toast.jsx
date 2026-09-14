import { useEffect, useRef } from "react";
import { Check } from "lucide-react";

/*
  Transient success message. The parent decides when a toast exists; this
  only reports when it is finished.

  Give it a key that changes per message so a second toast remounts with a
  fresh timer instead of inheriting what was left of the first one's.
*/
function Toast({ message, duration = 2000, onDone }) {
  // Held in a ref so the timer depends on duration alone. Parents pass an
  // inline arrow, and as a dependency that would restart the countdown on
  // every parent render.
  const onDoneRef = useRef(onDone);

  useEffect(() => {
    onDoneRef.current = onDone;
  });

  useEffect(() => {
    const timer = setTimeout(() => onDoneRef.current(), duration);
    return () => clearTimeout(timer);
  }, [duration]);

  return (
    <div
      role="status"
      className="fixed inset-x-0 bottom-6 z-60 flex justify-center px-4"
    >
      <div className="flex items-center gap-3 rounded-pill bg-plum px-5 py-3 font-primary text-sm font-medium text-white shadow-card">
        <span className="grid size-5 shrink-0 place-items-center rounded-pill bg-seafoam">
          <Check className="size-3.5 text-plum" strokeWidth={3} />
        </span>
        {message}
      </div>
    </div>
  );
}

export default Toast;
