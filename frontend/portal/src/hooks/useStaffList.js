import { useCallback, useEffect, useState } from "react";
import { readApiError } from "../api/auth.js";

/*
  Loads one staff list and exposes { status, items, message, refresh }.

  The result is tagged with the view it belongs to, so switching tabs never
  shows the previous list. Staleness is resolved at render time instead of
  by resetting state inside the effect, which React 19 rejects as a
  cascading render.
*/
export function useStaffList(view) {
  const [result, setResult] = useState({
    slug: null,
    status: "loading",
    items: [],
    message: "",
  });
  const [reloadToken, setReloadToken] = useState(0);

  const slug = view?.slug ?? null;
  const fetchList = view?.fetchList;

  useEffect(() => {
    if (!fetchList) return undefined;

    // StrictMode runs effects twice, and switching tabs quickly can leave
    // an older request in flight.
    let cancelled = false;

    fetchList()
      .then((envelope) => {
        if (cancelled) return;
        setResult({
          slug,
          status: "ready",
          items: envelope.data ?? [],
          message: "",
        });
      })
      .catch((error) => {
        if (cancelled) return;
        // A 401 never lands here: the interceptor in client.js signs the
        // user out first.
        setResult({
          slug,
          status: "error",
          items: [],
          message: readApiError(error),
        });
      });

    return () => {
      cancelled = true;
    };
  }, [slug, fetchList, reloadToken]);

  const refresh = useCallback(() => setReloadToken((token) => token + 1), []);

  // A refetch of the same list keeps its rows on screen rather than
  // flashing back to "Loading", which would make every save look like a
  // page reload.
  const isCurrent = result.slug === slug;

  return {
    status: isCurrent ? result.status : "loading",
    items: isCurrent ? result.items : [],
    message: isCurrent ? result.message : "",
    refresh,
  };
}
