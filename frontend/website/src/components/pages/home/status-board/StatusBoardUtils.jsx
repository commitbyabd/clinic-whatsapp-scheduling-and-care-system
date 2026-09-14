/* Formatting helpers for the status board, kept out of the component. */

/**
 * Renders the feed's timestamp as a local "HH:MM" clock time. Returns null
 * for a missing or unparseable value so the caller can simply omit the line
 * rather than print "Invalid Date".
 */
export const formatUpdatedAt = (value) => {
  if (!value) return null;

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
};
