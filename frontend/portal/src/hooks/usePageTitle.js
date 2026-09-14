import { useEffect } from "react";

const SUFFIX = "CWAC";

// Sets the document title for as long as the page is mounted. Belongs to
// the page layer, which is what owns a route's identity.
export function usePageTitle(title) {
  useEffect(() => {
    const previous = document.title;
    document.title = title ? `${title} · ${SUFFIX}` : SUFFIX;

    return () => {
      document.title = previous;
    };
  }, [title]);
}
