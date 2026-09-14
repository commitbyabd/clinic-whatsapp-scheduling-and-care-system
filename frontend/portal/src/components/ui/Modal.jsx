import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import Card from "./Card.jsx";

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

// Dialog shell. Owns the backdrop, Escape to close, the scroll lock and
// focus containment; the caller supplies the body and the footer.
function Modal({
  title,
  subtitle,
  onClose,
  children,
  width = "max-w-[520px]",
}) {
  const panelRef = useRef(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  });

  useEffect(() => {
    const panel = panelRef.current;
    // Restored on close so the trigger does not lose its place in the page.
    const previouslyFocused = document.activeElement;

    const focusable = () =>
      Array.from(panel?.querySelectorAll(FOCUSABLE) ?? []);

    // The first field, or the panel itself when the dialog is only a
    // message. Without this, focus stays behind the backdrop.
    const first = focusable()[0];
    if (first) first.focus();
    else panel?.focus();

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        onCloseRef.current();
        return;
      }

      if (event.key !== "Tab") return;

      // Tab must not reach the page behind the backdrop, so the ends of the
      // list wrap into each other.
      const items = focusable();
      if (items.length === 0) {
        event.preventDefault();
        return;
      }

      const firstItem = items[0];
      const lastItem = items[items.length - 1];

      if (event.shiftKey && document.activeElement === firstItem) {
        event.preventDefault();
        lastItem.focus();
      } else if (!event.shiftKey && document.activeElement === lastItem) {
        event.preventDefault();
        firstItem.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
      previouslyFocused?.focus?.();
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Sibling of the panel, not its parent, so a click inside the dialog
          never bubbles out and closes it */}
      <div
        aria-hidden="true"
        onClick={onClose}
        className="absolute inset-0 bg-plum/45 backdrop-blur-glass"
      />

      <Card
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        className={`relative w-full ${width} bg-porcelain/95 p-6 shadow-card backdrop-blur-card outline-none sm:p-7`}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h2 className="font-primary text-heading-xs leading-heading font-semibold tracking-tight text-plum">
              {title}
            </h2>
            {subtitle && (
              <p className="mt-1 font-primary text-sm leading-body text-muted">
                {subtitle}
              </p>
            )}
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="grid size-9 shrink-0 place-items-center rounded-md text-muted transition duration-200 hover:bg-pale-lavender hover:text-plum focus-visible:ring-2 focus-visible:ring-violet/22 focus-visible:outline-none"
          >
            <X className="size-4.5" strokeWidth={2} />
          </button>
        </div>

        <div className="mt-6">{children}</div>
      </Card>
    </div>
  );
}

export default Modal;
