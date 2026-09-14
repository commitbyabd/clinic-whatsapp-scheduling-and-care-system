// Shown while a lazily loaded route is still downloading. Deliberately
// plain: on a fast connection it is on screen for a few frames.
function RouteFallback() {
  return (
    <div
      role="status"
      className="grid min-h-screen place-items-center bg-(image:--gradient-page)"
    >
      <p className="font-primary text-sm text-muted">Loading…</p>
    </div>
  );
}

export default RouteFallback;
