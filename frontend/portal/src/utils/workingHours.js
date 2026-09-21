// 0 is Monday, as the schedule API counts
export const DAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

export const SLOT_CHOICES = [10, 15, 20, 30, 45, 60];

// The server's limit on blocks in one week
const MAX_BLOCKS = 21;

const minutes = (hhmm) => {
  const [hours, mins] = hhmm.split(":").map(Number);
  return hours * 60 + mins;
};

// "13:00" -> "1:00 PM"
export function formatClock(hhmm) {
  const [hours, mins] = hhmm.split(":").map(Number);
  const suffix = hours < 12 ? "AM" : "PM";
  return `${hours % 12 || 12}:${String(mins).padStart(2, "0")} ${suffix}`;
}

/*
  The saved schedule, as the editor holds it: one list of blocks per day,
  the slot length as text for the select, and days off as "YYYY-MM-DD".

  GET /doctor/schedule sends [] rather than null when nothing is saved,
  so anything that is not an object counts as no schedule.
*/
export function weekFromSchedule(schedule) {
  const saved = schedule && !Array.isArray(schedule) ? schedule : null;
  const days = DAYS.map(() => []);

  for (const block of saved?.working_hours ?? []) {
    days[block.day_of_week]?.push({
      start: block.start_time,
      end: block.end_time,
    });
  }
  days.forEach((blocks) =>
    blocks.sort((a, b) => (a.start < b.start ? -1 : 1)),
  );

  return {
    slotMinutes: String(saved?.slot_minutes ?? 30),
    days,
    // stored as midnight UTC, so the day is the first ten characters
    daysOff: (saved?.blackout_dates ?? []).map((day) => day.slice(0, 10)).sort(),
  };
}

export const hasWorkingHours = (schedule) =>
  weekFromSchedule(schedule).days.some((blocks) => blocks.length > 0);

/*
  What is wrong with the week, keyed "<day>.<block>", plus "total" when
  there are too many blocks. Mirrors the server's checks, and adds one it
  cannot make: a block too short for a single slot books nobody.
*/
export function weekErrors(week) {
  const errors = {};
  const slot = Number(week.slotMinutes);

  week.days.forEach((blocks, day) => {
    blocks.forEach((block, index) => {
      const key = `${day}.${index}`;
      if (!block.start || !block.end) {
        errors[key] = "Enter a start and an end time.";
      } else if (block.end <= block.start) {
        errors[key] = "The end must be after the start.";
      } else if (minutes(block.end) - minutes(block.start) < slot) {
        errors[key] = `Shorter than one ${slot}-minute slot.`;
      }
    });

    // in start order, only neighbours can overlap
    const ordered = blocks
      .map((block, index) => ({ ...block, index }))
      .filter((block) => block.start && block.end && block.end > block.start)
      .sort((a, b) => (a.start < b.start ? -1 : 1));

    for (let i = 1; i < ordered.length; i += 1) {
      const before = ordered[i - 1];
      if (ordered[i].start < before.end) {
        errors[`${day}.${ordered[i].index}`] =
          `Overlaps ${formatClock(before.start)} to ${formatClock(before.end)}.`;
      }
    }
  });

  const count = week.days.reduce((total, blocks) => total + blocks.length, 0);
  if (count > MAX_BLOCKS) {
    errors.total = `At most ${MAX_BLOCKS} blocks of hours in a week.`;
  }

  return errors;
}

// The body for PUT /doctor/schedule
export function weekPayload(week) {
  return {
    working_hours: week.days.flatMap((blocks, day) =>
      blocks.map((block) => ({
        day_of_week: day,
        start_time: block.start,
        end_time: block.end,
      })),
    ),
    slot_minutes: Number(week.slotMinutes),
    blackout_dates: [...new Set(week.daysOff)].sort(),
  };
}

// Hours a week across the blocks that make sense, for the header
export function weeklyHours(week) {
  const total = week.days
    .flat()
    .filter((block) => block.start && block.end && block.end > block.start)
    .reduce((sum, block) => sum + minutes(block.end) - minutes(block.start), 0);
  return Math.round((total / 60) * 10) / 10;
}
