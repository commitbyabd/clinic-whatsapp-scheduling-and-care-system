import { useEffect, useRef, useState } from "react";
import { readApiError } from "../api/auth.js";

const IDLE = { status: "idle", data: null, message: "" };
const LOADING = { status: "loading", data: null, message: "" };

/*
  Loads one thing from the API and exposes { status, data, message }.

  'key' names what is being loaded, e.g. "slots:<doctor>:<date>". When it
  changes the old result is hidden straight away, so one doctor's slots
  never show under another's name. A null key loads nothing ("idle").

  Changing 'version' loads the same thing again but keeps the current
  result on screen until the new one arrives, so a refresh does not flash.

  message is the server's text, which also explains an empty result.
*/
export function useApiResource(key, load, version = 0) {
  const [result, setResult] = useState({ key: null, ...LOADING });

  // Callers pass an inline arrow, which is new every render. The latest one
  // is kept here and read when the key changes.
  const loadRef = useRef(load);
  useEffect(() => {
    loadRef.current = load;
  });

  useEffect(() => {
    if (key === null) return undefined;

    // StrictMode runs effects twice, and a quick change of key can leave an
    // older request in flight
    let cancelled = false;

    loadRef
      .current()
      .then((envelope) => {
        if (cancelled) return;
        setResult({
          key,
          status: "ready",
          data: envelope.data,
          message: envelope.message ?? "",
        });
      })
      .catch((error) => {
        if (cancelled) return;
        setResult({
          key,
          status: "error",
          data: null,
          message: readApiError(error),
        });
      });

    return () => {
      cancelled = true;
    };
  }, [key, version]);

  if (key === null) return IDLE;
  return result.key === key ? result : LOADING;
}
