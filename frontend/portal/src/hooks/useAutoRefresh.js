import { useEffect, useRef } from "react";

/*
  Calls refresh every `ms` while the tab is on screen, and straight away
  when it comes back into view, so new WhatsApp requests and bookings show
  up without anyone pressing Refresh. A tab in the background is left alone.
*/
export function useAutoRefresh(refresh, ms = 30000) {
  // the latest refresh, so an inline arrow does not restart the timer
  const refreshRef = useRef(refresh);
  useEffect(() => {
    refreshRef.current = refresh;
  });

  useEffect(() => {
    const tick = () => {
      if (document.visibilityState === "visible") refreshRef.current();
    };

    const timer = setInterval(tick, ms);
    document.addEventListener("visibilitychange", tick);

    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", tick);
    };
  }, [ms]);
}
