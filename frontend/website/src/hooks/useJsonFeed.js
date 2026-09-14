import { useEffect, useState } from "react";

/**
 * Fetches a JSON document served from the public folder — the operational
 * data the clinic edits without a rebuild.
 *
 * Returns a status rather than throwing, so a caller can hide its section
 * entirely when the feed is missing. For this site that is the required
 * behaviour: a board showing zeros is worse than no board.
 *
 * status: "loading" | "ready" | "error"
 */
function useJsonFeed(url) {
  const [state, setState] = useState({ status: "loading", data: null });

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    const load = async () => {
      try {
        const response = await fetch(url, {
          signal: controller.signal,
          cache: "no-store",
        });

        if (!response.ok) throw new Error(`Request failed: ${response.status}`);

        const data = await response.json();
        if (active) setState({ status: "ready", data });
      } catch (error) {
        if (error.name === "AbortError" || !active) return;
        setState({ status: "error", data: null });
      }
    };

    load();

    return () => {
      active = false;
      controller.abort();
    };
  }, [url]);

  return state;
}

export default useJsonFeed;
