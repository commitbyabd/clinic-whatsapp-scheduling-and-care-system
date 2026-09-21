import { useCallback, useEffect, useState } from "react";
import { listBookingRequests } from "../api/receptionist.js";
import { readApiError } from "../api/auth.js";

/*
  Loads the booking requests with one status and exposes
  { status, items, message, refresh }, the same shape as useStaffList.
*/
export function useBookingRequests(requestStatus) {
  const [result, setResult] = useState({
    key: null,
    status: "loading",
    items: [],
    message: "",
  });
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    // StrictMode runs effects twice, and a quick refresh can leave an older
    // request in flight
    let cancelled = false;

    listBookingRequests(requestStatus)
      .then((envelope) => {
        if (cancelled) return;
        setResult({
          key: requestStatus,
          status: "ready",
          items: envelope.data ?? [],
          message: "",
        });
      })
      .catch((error) => {
        if (cancelled) return;
        setResult({
          key: requestStatus,
          status: "error",
          items: [],
          message: readApiError(error),
        });
      });

    return () => {
      cancelled = true;
    };
  }, [requestStatus, reloadToken]);

  const refresh = useCallback(() => setReloadToken((token) => token + 1), []);

  // a refresh keeps the current rows on screen instead of flashing "Loading"
  const isCurrent = result.key === requestStatus;

  return {
    status: isCurrent ? result.status : "loading",
    items: isCurrent ? result.items : [],
    message: isCurrent ? result.message : "",
    refresh,
  };
}
