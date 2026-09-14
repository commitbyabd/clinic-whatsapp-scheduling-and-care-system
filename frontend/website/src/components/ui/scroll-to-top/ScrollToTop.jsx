import { useLenis } from "lenis/react";
import { useLayoutEffect } from "react";
import { useLocation } from "react-router";

/**
 * Resets scroll position on every route change. Headless — renders nothing.
 * Goes through Lenis when it is running so the reset is not fought by the
 * smooth-scroll loop.
 */
function ScrollToTop() {
  const { pathname } = useLocation();
  const lenis = useLenis();

  useLayoutEffect(() => {
    if (lenis) {
      lenis.scrollTo(0, { immediate: true });
      return;
    }

    window.scrollTo(0, 0);
  }, [pathname, lenis]);

  return null;
}

export default ScrollToTop;
