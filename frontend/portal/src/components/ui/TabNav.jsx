/*
  A portal's top-level tabs. Controlled: the parent keeps the active tab
  (in the URL, so a refresh keeps it) and hears about clicks.

  tabs  [{ slug, label, icon }]
*/
function TabNav({ tabs, active, onSelect, label }) {
  return (
    <nav aria-label={label} className="mb-6 flex flex-wrap gap-2">
      {tabs.map(({ slug, label: text, icon: Icon }) => {
        const current = active === slug;
        return (
          <button
            key={slug}
            type="button"
            aria-current={current ? "page" : undefined}
            onClick={() => onSelect(slug)}
            className={`inline-flex h-10 items-center gap-2 rounded-pill px-4 font-primary text-sm font-semibold transition duration-200 focus-visible:ring-4 focus-visible:ring-violet/22 focus-visible:outline-none ${
              current
                ? "bg-plum text-white shadow-button"
                : "border border-border bg-white text-plum hover:bg-pale-lavender"
            }`}
          >
            <Icon className="size-4" strokeWidth={2} />
            {text}
          </button>
        );
      })}
    </nav>
  );
}

export default TabNav;
