/* Imperative bits of the header, kept out of Nav.jsx so the component
   stays declarative. */

/**
 * The mobile drawer covers the page, so the document behind it must not
 * scroll. Lenis is paused too, otherwise its loop keeps driving the page.
 */
export const lockScroll = (lenis) => {
  document.body.style.overflow = "hidden";
  lenis?.stop();
};

export const unlockScroll = (lenis) => {
  document.body.style.overflow = "";
  lenis?.start();
};

/**
 * Closes the drawer on Escape. Returns its own teardown.
 */
export const bindEscape = (onEscape) => {
  const handleKeyDown = (event) => {
    if (event.key === "Escape") onEscape();
  };

  window.addEventListener("keydown", handleKeyDown);

  return () => window.removeEventListener("keydown", handleKeyDown);
};

/**
 * The active nav pill. Home only matches exactly; every other route also
 * matches its nested paths.
 */
export const isActivePath = (pathname, path) =>
  path === "/" ? pathname === "/" : pathname.startsWith(path);
