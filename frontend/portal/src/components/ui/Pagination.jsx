import { ChevronLeft, ChevronRight } from "lucide-react";

const STEP_CLASS =
  "grid size-9 place-items-center rounded-md border border-border bg-white text-plum transition duration-200 hover:bg-pale-lavender focus-visible:ring-2 focus-visible:ring-violet/22 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-40";

// Previous / next with a position readout. Page numbers are deliberately
// absent: they earn their place once there are enough pages to skip
// between, and this list is nowhere near that.
function Pagination({
  page,
  pageCount,
  total,
  rangeStart,
  rangeEnd,
  onChange,
}) {
  if (pageCount <= 1) return null;

  return (
    <nav
      aria-label="Pagination"
      className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4"
    >
      <p className="font-primary text-xs text-muted">
        Showing {rangeStart} to {rangeEnd} of {total}
      </p>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => onChange(page - 1)}
          disabled={page <= 1}
          aria-label="Previous page"
          className={STEP_CLASS}
        >
          <ChevronLeft className="size-4" strokeWidth={2} />
        </button>

        {/* aria-live so a screen reader hears the page change, which is
            otherwise silent because focus stays on the arrow */}
        <p aria-live="polite" className="font-primary text-xs text-muted">
          Page {page} of {pageCount}
        </p>

        <button
          type="button"
          onClick={() => onChange(page + 1)}
          disabled={page >= pageCount}
          aria-label="Next page"
          className={STEP_CLASS}
        >
          <ChevronRight className="size-4" strokeWidth={2} />
        </button>
      </div>
    </nav>
  );
}

export default Pagination;
