/* Static copy for the live status board. The figures themselves are not
   here — they come from /data/status-board.json, which the front desk edits
   without a rebuild. See useJsonFeed. */

export const statusBoardData = {
  eyebrow: "In the clinic right now",
  heading: "Before you set out, see how busy we are.",
  description:
    "Updated every fifteen minutes from the front desk. If emergency is red, we'll still see you — it just means a longer wait for anything non-urgent.",
  updatedLabel: "Last updated",
};

/* The dot is the state indicator, so every state also carries a word —
   color alone must not be the signal. */
export const statusStates = {
  normal: { label: "Normal" },
  busy: { label: "Busy" },
  heavy: { label: "Heavy" },
};

export const STATUS_FEED_URL = "/data/status-board.json";
