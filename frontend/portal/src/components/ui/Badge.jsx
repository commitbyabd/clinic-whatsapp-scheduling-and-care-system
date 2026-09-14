// Pill badge with an optional leading dot. Colours come from the caller:
// <Badge className="bg-seafoam text-plum" />
function Badge({
  children,
  dot = true,
  dotClassName = "bg-plum",
  className = "",
}) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-pill px-3.5 py-2 font-primary text-sm font-medium ${className}`}
    >
      {dot && <span className={`size-2 rounded-pill ${dotClassName}`} />}
      {children}
    </span>
  );
}

export default Badge;
