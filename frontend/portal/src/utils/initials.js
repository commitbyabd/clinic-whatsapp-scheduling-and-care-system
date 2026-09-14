// Honorifics rather than names. Matched without the trailing dot, which is
// stripped before the lookup.
const TITLES = new Set([
  "dr",
  "mr",
  "mrs",
  "ms",
  "miss",
  "prof",
  "sir",
  "hafiz",
  "hafiza",
  "syed",
  "syeda",
  "mufti",
  "qari",
  "engr",
  "adv",
]);

const isTitle = (word) => TITLES.has(word.toLowerCase().replace(/\.$/, ""));

// "Dr. Sara Khan" -> "SK". Titles are dropped first, or every clinician in
// the list would share a "D". A name that is nothing but titles keeps them,
// since one letter beats a question mark.
export function initialsFrom(fullName) {
  const parts = String(fullName ?? "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  const named = parts.filter((word) => !isTitle(word));
  const words = named.length > 0 ? named : parts;

  if (words.length === 0) return "?";

  const letters =
    words.length === 1
      ? words[0].slice(0, 1)
      : words[0].slice(0, 1) + words[words.length - 1].slice(0, 1);

  return letters.toUpperCase();
}
