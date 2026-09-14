// Icon + title + subtitle navigation row with an active state.
function NavItem({ icon: Icon, title, subtitle, active = false, ...rest }) {
  return (
    <button
      type="button"
      aria-current={active ? "page" : undefined}
      className={`flex w-full items-start gap-3 rounded-lg px-3 py-3 text-left transition duration-200 focus-visible:ring-2 focus-visible:ring-violet/22 focus-visible:outline-none ${
        active
          ? "border border-border bg-white shadow-sm"
          : "border border-transparent hover:bg-pale-lavender"
      }`}
      {...rest}
    >
      <Icon
        className={`mt-0.5 size-4.5 shrink-0 ${active ? "text-violet" : "text-muted"}`}
        strokeWidth={2}
      />
      <span className="min-w-0">
        <span
          className={`block font-primary text-sm font-semibold ${active ? "text-plum" : "text-ink"}`}
        >
          {title}
        </span>
        <span className="mt-0.5 block font-primary text-xs leading-body text-muted">
          {subtitle}
        </span>
      </span>
    </button>
  );
}

export default NavItem;
