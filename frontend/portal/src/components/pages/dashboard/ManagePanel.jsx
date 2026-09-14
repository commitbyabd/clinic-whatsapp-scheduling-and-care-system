import Card from "../../ui/Card.jsx";
import NavItem from "../../ui/NavItem.jsx";
import { STAFF_VIEWS } from "../../../config/staffViews.js";

// Controlled: renders whichever view the parent says is active and reports
// clicks back, rather than holding a selection the list must stay in sync
// with. The items come from the shared config, so wording lives in one file.
function ManagePanel({ activeSlug, onSelect }) {
  return (
    <Card
      as="nav"
      aria-label="Manage staff"
      className="bg-porcelain/85 p-4 shadow-[0_12px_30px_var(--plum-17)] sm:p-5"
    >
      <p className="px-3 font-primary text-xs font-semibold tracking-[0.12em] text-muted uppercase">
        Manage staff
      </p>

      <div className="mt-4 space-y-1">
        {STAFF_VIEWS.map((view) => (
          <NavItem
            key={view.slug}
            icon={view.icon}
            title={view.title}
            subtitle={view.subtitle}
            active={view.slug === activeSlug}
            onClick={() => onSelect?.(view.slug)}
          />
        ))}
      </div>
    </Card>
  );
}

export default ManagePanel;
